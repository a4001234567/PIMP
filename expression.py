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


LEFT_FUNCTION_PARENTHESIS = -1
RIGHT_FUNCTION_PARENTHESIS = 1
LEFT_PRIORITY_PARENTHESIS = -2
RIGHT_PRIORITY_PARENTHESIS = 2
COMMA = 3;COLON=-3
AND = 4;OR = -4
FUNCTION_NAME = 0
PARAM = 5


def create_expression(string):
    '''
    Generate an expression object from a string.
    This function implements lexical analysis, a list of different components are
    then fed to expression initialization to generate an expression object.
    A components may be one of the special characters ':',',','(',')';
    or one of the logical operator '&','|';
    or function's name: 'Not','Pinmatch','Wordmatch','Match','More','Less'.
    or a function's parameters, which is a sequence of non-special characters 
    enclosed in the parenthesis of a function.
    '''
    types = [];components = []
    depth = 0;cur = '';FLAG_ARG=False;ARG_DEPTH = 0
    for idx,char in enumerate(string):
        try:
            match char:
                case ':':
                    assert FLAG_ARG,'Colon should be used inside function arguments only!'
                    components.append(':')
                    types.append(COLON)
                case ',':
                    assert FLAG_ARG,'Comma should be used inside function arguments only!'
                    if ARG_DEPTH != depth:
                        #comma is inside 
                        cur += ','
                    else:
                        components.append(',')
                        types.append(COMMA)
                case '(':
                    depth += 1
                    #determine types of parenthesis
                    if FLAG_ARG:
                        cur += '('
                case ')':
                case '&':
                case '|':
                case _:




class expression:
    def __init__(self,string,first = False):
        #lexical analysis
        parsed_string = []
        for 

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
