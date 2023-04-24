
'''
Search Program by Jason wu @ 2023
    This program is designed to search from a set of phrases, with matches by pinyin similarity and precise matching.
    It also supports manipulation of searching result like shuffle, filter and Import/Export functionality.
    This program runs in a commandline manner.
'''

'Initilization'
#storage for variables(lists of results)
All_results = dict()
#store attributes
Sort_attributes = dict()
#store default value for attributes
Sort_default = dict()


#Tool function
def load_from_file(file_name):
    loaded_word = set()
    with open(file_name) as file:
        for idx,line in enumerate(file):
            line = line.rstrip()
            if not idx:continue
            if 1 == idx:
                attributes = [i for i in line.split(';') if i]
                for k,v in map(lambda x:x.split(','),attributes):
                    Sort_default[k] = float(v)
            else:
                for wordatr in line.split(';'):
                    if not wordatr:continue
                    word,*wordattri = wordatr.split(',')
                    if word not in Sort_attributes:
                        Sort_attributes[word] = dict()
                    for k,v in map(lambda x:x.split(':'),wordattri):
                        v = float(v)
                        assert k in Sort_default, 'Undefined attributes {k} found in {file_name}!'
                        Sort_attributes[word][k] = v
                    loaded_word.add(word)
    All_results['ALL'] = tuple(loaded_word.union(set(All_results['ALL'])))
    return tuple(loaded_word)

#Load phrases files
All_results['ALL'] = tuple()

with open('category/list.txt') as file:
    for line in file:
        line = line.rstrip()
        load_from_file(f'category/{line}')
        try:
            load_from_file(f'category/{line}')
        except Exception as e:
            if isinstance(e,FileNotFoundError):
                print(f'Error loading file {line}, please check again!')
            elif isinstance(e,AssertionError):
                print(e)
            print(e)

All_results['CUR'] = tuple(All_results['ALL'])

#Load dependency
import expression
import random
import click
import os

#Welcome
banner1 = '''
██████  ██ ███    ███ ██████ 
██   ██ ██ ████  ████ ██   ██
██████  ██ ██ ████ ██ ██████ 
██      ██ ██  ██  ██ ██     
██      ██ ██      ██ ██     
'''
banner2 = '''
██████╗ ██╗███╗   ███╗██████╗ 
██╔══██╗██║████╗ ████║██╔══██╗
██████╔╝██║██╔████╔██║██████╔╝
██╔═══╝ ██║██║╚██╔╝██║██╔═══╝ 
██║     ██║██║ ╚═╝ ██║██║     
╚═╝     ╚═╝╚═╝     ╚═╝╚═╝     
'''                              
width = int(os.environ.get('COLUMNS',40))
for line in random.choice((banner1,banner2)).split('\n'):
    print(' '*max(0,(width-len(line))//2),line[:min(width,len(line))])
for line in ('Pinyin-based Idiom Matching Program 1.0.0',f'{len(All_results["ALL"])} idioms loaded'):
    print(' '*max(0,(width-len(line))//2),line[:min(width,len(line))])



#Main Loop
while True:
    raw_input = input('>>>').strip(' \x7f\n\t\r')
    #try:
    if True:
        loc_ws = raw_input.find(' ')
        cmd = raw_input
        arg = [''];depth = 0
        if loc_ws != -1:
            cmd = raw_input[:loc_ws]
            for char in raw_input[loc_ws+1:]:
                match char:
                    case '(':
                        depth += 1
                        arg[-1] += '('
                    case ')':
                        depth -= 1
                        arg[-1] += ')'
                    case ' ':
                        if arg[-1]:
                            if depth:
                                arg[-1] += ' '
                            else:
                                arg.append('')
                    case _ as char:
                        arg[-1] += char
        if arg and not arg[-1]:arg.pop()

        match cmd:
            case 'Load':
                assert len(arg) <= 1, f'Load takes no more than 1 argument, yours has {len(arg)}!'
                if 0 == len(arg):arg.append('ALL')
                assert arg[0] in All_results, f'{arg[0]} not a saved result!'
                All_results['CUR'] = tuple(All_results[arg[0]])

            case 'Dump':
                assert len(arg) == 1, f'Dump takes only 1 argument, yours has {len(arg)}!'
                assert arg[0] != 'ALl', 'ILLEGAL ACTION!'
                if arg[0] in All_results and not click.confirm(f'{arg[0]} already occupied, overwrite?',default=True):
                    continue
                All_results[arg[0]] = All_results['CUR']

            case 'Count':
                assert len(arg) <= 1, f'Count take 1 or no argument, your input has {len(arg)}!' 
                if len(arg) and arg[0]:
                    assert arg[0] in All_results, f'{arg} not a saved result!'
                    print(f'{arg[0]}:\t{len(All_results[arg[0]])}')
                else:
                    for key,item in All_results.items():
                        print(f'{key}:\t{len(item)}')
            case 'Delete':
                assert len(arg) == 1, f'Delete take only 1 argument, yours has {len(arg)}!'
                assert 'ALL' != arg[0] and 'CUR' != arg[0], 'ILLEGAL ACTION'
                if arg[0] in All_results:
                    All_results.pop(arg[0])
            case 'Concat':
                assert len(arg) > 1, f'Concat take no less than 2 argument, yours has {len(arg)}!'
                for key in arg:
                    assert key in All_results, f'{key} not a saved result!'
                cur = set()
                for key in arg:
                    cur = cur.union(set(All_results[key]))
                All_results['CUR'] = cur
            case 'Minus':
                assert 2 >= len(arg), f'Minus take no more than 2 arguments, yours has {len(arg)}'
                if 1 == len(arg): arg.append['CUR']
                arg[0],arg[1] = arg[1],arg[0]
                cur = set(All_results[arg[0]])
                dif = set(All_results[arg[1]])
                All_results['CUR'] = tuple(cur.difference(dif))
            case 'Intersect':
                assert 2 >= len(arg), f'Intersect take no more than 2 arguments, yours has {len(arg)}!'
                if 1 == len(arg): arg.append['CUR']
                setA = set(All_results[arg[0]])
                setB = set(All_results[arg[1]])
                All_results['CUR'] = tuple(setA.intersection(setB))
            case 'Sortby':
                if not arg:
                    print(f'Available keywords includes:{",".join(Sort_default.keys())}')
                    continue
                assert 2 >= len(arg), f'You must specified 1 Keywords First'
                assert arg[0] in Sort_default, f'Key {arg[0]} not found, choose from {",".join(Sort_default.keys())}'
                key,default = arg[0],Sort_default[arg[0]]
                All_results['CUR'] = sorted(All_results['CUR'], key = lambda x:Sort_attributes[x].get(key,default),reverse = (2 == len(arg)))
            case 'Filter':
                assert len(arg) == 1, f'Only 1 expression needed'
                try:
                    pattern_checker = expression.expression(arg[0])
                except AssertionError as e:
                    print(f'ILLEGAL PATTERN:{e}')
                All_results['CUR'] = tuple(word for word in All_results['CUR'] if pattern_checker.check(word))
            case 'First':
                assert 1 >= len(arg), f'First take 0 or 1 argument only, yours have {len(arg)}!'
                if not arg:arg.append(5)
                try:
                    num = int(arg[0])
                except ValueError:
                    assert False, f'Cannot convert {arg[0]} to integer'
                assert num > 0, f'Input should be greater than 0!'
                All_results['CUR'] = tuple(All_results['CUR'][:num])
            case 'Show':
                assert 1 >= len(arg), f'Show take 0 or 1 argument only, yours have {len(arg)}!'
                if not arg:arg.append('CUR')
                assert arg[0] in All_results, f'{arg[0]} Not Found!'
                to_print = All_results[arg[0]]
                if not to_print:
                    print('No result!')
                    continue
                if len(to_print) >= 100 and not click.confirm(f'{len(to_print)} objects to show, proceed?',default = False):
                    continue
                width = int(os.environ.get('COLUMNS',40))//2
                max_width = min(max(map(len,to_print))+4,width)
                line = '';l = 0;
                for item in to_print:
                    line += item + ' '*(max_width-len(item))*2
                    l += max_width
                    if l + max_width >= width:
                        print(line);line = '';l=0
                if line:print(line)
            case 'Shuffle':
                assert 1 >= len(arg), f'Shuffle take 0 or 1 argument only, yours have {len(arg)}!'
                if not arg:arg.append('CUR')
                assert arg[0] in All_results, f'{arg[0]} Not Found!'
                temp = list(All_results[arg[0]]);random.shuffle(temp)
                All_results[arg[0]] = tuple(temp)
            case 'Import':
                assert 1 == len(arg), f'You must specify one file path!'
                All_results['CUR'] = load_from_file(arg[0])
            case 'Export':
                assert 1 == len(arg), f'You must specify a file name!'
                with open(arg[0],'w') as file:
                    file.write('OUTPUT\n')
                    file.write(';'.join(f'{k,v}' for k,v in Sort_default.items())+'\n')
                    for word in All_results['CUR']:
                        file.write(f'{word}{"".join(f",k:v" for k,v in Sort_attributes[word])};\n')
            case 'Exit':
                exit()
            case _ as other:
                print(f'Unrecognized command:{other}')
    #except Exception as e:
    #    print(e)
