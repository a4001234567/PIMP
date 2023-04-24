from dimsim_edited import get_minimum_distance
import profile
import timeit

def parse_param(params):
    key = '';value = ''
    arg = [];argv = {}
    is_pair = False
    for char in params:
        match char:
            case ',':
                if is_pair:
                    argv[key] = value
                    key = '';value = '';is_pair = False
                else:
                    arg.append(key);key = ''
            case ':':
                is_pair = True
            case _:
                if is_pair:
                    value+= char
                else: key += char
    if is_pair:
        argv[key]= value
    else:arg.append(key)
    return (arg,argv)

class expression:
    def __init__(self,string,first = False):
        self.type = None
        self.prefix = ''
        depth = 0
        first_par = 10000
        if first and string[0] == '(' and string[-1] == ')':
            string = string[1:-1]
        for i,char in enumerate(string):
            match char:
                case '(':
                    first_par = min(first_par,i)
                    depth += 1
                case ')':
                    depth -= 1
                case '&':
                    if depth > 0: continue
                    self.type='AND'
                    self.left = expression(string[:i],first=True)
                    self.right = expression(string[i+1:])
                    if self.right.time > self.left.time:
                        self.right,self.left = self.left,self.right
                    self.time = self.left.time
                case '|':
                    if depth > 0: continue
                    self.type='OR'
                    self.left = expression(string[:i],first=True)
                    self.right = expression(string[i+1:])
                    if self.right.time > self.left.time:
                        self.right,self.left = self.left,self.right
                    self.time = self.left.time
            assert depth >= 0, 'Parenthesis Mismatch!'
            if self.type:break
        else:
            if string[0] == '(':
                assert string[-1] == ')', f'Condition {string} should end with ")"!'
                self.__init__(string[1:-1])
            else:
                self.type = string[:first_par]
                self.param = string[first_par+1:-1]
                assert self.type in ('Not','More','Less') or '(' not in self.param, 'Paramaters cannot contain parenthesis unless for Not, More and Less'
                match self.type:
                    case 'Not':
                        self.param = expression(self.param)
                        self.time = self.param.time
                    case 'More'|'Less':
                        depth = 0;starts = 0;params = []
                        for i,char in enumerate(self.param):
                            match char:
                                case '(':depth += 1
                                case ')':depth -= 1
                                case ',':
                                    if depth:continue
                                    params.append(self.param[starts:i])
                                    starts = i+1
                            assert depth>=0, 'Parenthesis Mismatch!'
                        params.append(self.param[starts:])
                        self.param = (int(params[0]),*sorted(tuple(map(expression,params[1:])),key = lambda x:x.time))
                        self.time = 0
                        if self.type == 'More':
                            self.time = sum(map(lambda x:x.time,self.param[1:self.param[0]]))
                        else:
                            self.time = sum(map(lambda x:x.time,self.param[1:]))
                        #self.param = (int(params[0]),*map(expression,params[1:]))
                    case 'Pinmatch'|'Wordmatch':
                        self.param = parse_param(self.param)
                        if self.type == 'Pinmatch':
                            self.time = 86
                            self.threshold = float(self.param[1].get('threshold',0.5))
                        else:self.time = 100
                        assert len(self.param[0]) == 1, f'{self.type} allow only 1 pattern!'
                    case 'Match':
                        args,argv = parse_param(self.param)
                        assert len(args) == 1, f'Match allow only 1 pattern!'
                        threshold = float(argv.get('threshold',0.01))
                        self.type = 'OR'
                        self.right = expression(f'Wordmatch({args[0]})')
                        self.left = expression(f'Pinmatch({args[0]},threshold:{threshold})')
                        self.time = self.left.time

    def __repr__(self):
        if 'AND' == self.type or 'OR' == self.type:
            return f'{self.type}-({self.left.__repr__()},{self.right.__repr__()})'
        elif self.type:
            return f'{self.type}-({self.param})'

    def check(self,string):
        match self.type:
            case 'AND':
                return self.left.check(string) and self.right.check(string)
            case 'OR':
                return self.left.check(string) or self.right.check(string)
            case 'Not':
                return not self.param.check(string)
            case 'Pinmatch':
                args,argvs = self.param
                threshold = self.threshold
                pattern = args[0];l=len(pattern)
                if l > len(string): return False
                for index in range(len(string)-l+1):
                    try:
                        if get_minimum_distance(string[index:index+l],pattern,threshold=threshold):
                            return True
                    except Exception as e:
                        return False
                return False
            case 'Wordmatch':
                args,argvs = self.param
                pattern = args[0];l=len(pattern)
                if 1 == l:
                    return '_' == pattern or pattern in string
                for starts in range(len(string)-l+1):
                    for index in range(l):
                        if '_' != pattern[index] and string[index+starts] != pattern[index]:
                            break
                    else:
                        return True
                return False
            case 'More':
                cnt = self.param[0];tot = len(self.param)-2
                for idx,pat in enumerate(self.param[1:]):
                    if pat.check(string):cnt -= 1
                    if not cnt:
                        return True
                    if cnt>tot-idx:
                        return False
            case 'Less':
                cnt = self.param[0];tot = len(self.param)-2
                for idx,pat in enumerate(self.param[1:]):
                    if pat.check(string):cnt -= 1
                    if not cnt:
                        return False
                    if cnt>tot-idx:
                        return True
        raise NotImplemented

if __name__ == '__main__':
    a = expression('More(2,Match(你好,threshold:1),Wordmatch(哈))')
    assert a.check('你哈')
    c = expression('Pinmatch(冬天_啦,threshold:5)&Wordmatch(了)')
    assert c.check('东天来了')
    print(c.check('冬天来到了'))#True
    print(c.check('啊冬日来到了'))#False
    b = expression('Wordmatch(o)&Not(Wordmatch(o_ld))')
    print(b.check('World'))#False
    print(b.check('halo'))#True
    d = expression('Match(花,threshold:2)')
    print(d.check('发'))
    e = expression('Match(西藏)')
    f = expression('Match(东,threshold:1)|Match(右,threshold:1)')
    g = expression('Match(花,threshold:1)')
    h = expression('More(2,Match(西藏),Match(东,threshold:1)|Match(右,threshold:1),Match(花,threshold:1))')
    print(e.check('坚定不移'))
    print(f.check('坚定不移'))
    print(g.check('坚定不移'))
    i = expression('More(2,Match(日,threshold:1)|Match(阳,threshold:1),Match(烷,threshold:5)|Match(基,threshold:1))')
    #i = expression('Match(日,threshold:1)|Match(阳,threshold:1)|(Match(烷,threshold:5)|Match(基,threshold:1))')
    assert i.check('日理万机')
    print(get_minimum_distance('烷','万',threshold=5))
    j = expression('Pinmatch(烷)')
    k = expression('Wordmatch(烷)')
    print(timeit.timeit('j.check("日理万机")',globals=dict(j=j)))
    print(timeit.timeit('k.check("日理万机")',globals=dict(k=k)))
