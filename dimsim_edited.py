from pypinyin import Style
import pypinyin
import sys
from math import sqrt
import profile
from functools import lru_cache
import itertools
import pickle
import os


# Load working directory
work_dir = os.path.abspath(__file__)
indexOfLastSlash = work_dir.rfind("/")
work_dir = work_dir[0:indexOfLastSlash]+"/"


#Load dictionary
sfile = open(work_dir+'pinyin_to_simplified.pickle', 'rb')
pinyin_to_simplified = pickle.load(sfile)
sfile.close()

tfile = open(work_dir+'pinyin_to_traditional.pickle', 'rb')
pinyin_to_traditional = pickle.load(tfile)
tfile.close()

@lru_cache(maxsize=16384)
def convert_single_word_to_pinyin(char,heteronym=False):
    assert len(char) == 1
    return pypinyin.pinyin(char,style=Style.TONE3,heteronym=heteronym,neutral_tone_with_five=True)[0]
    

def convert_to_pinyin(pinyin_list):
    '''
    convert a list of pypinyin format pinyin to customized pinyin format
    '''
    return tuple(map(lambda x:Pinyin(x),pinyin_list))

@lru_cache(maxsize=24)
def list_all_pinyin(utterance):
    #pinyin_lists = [convert_to_pinyin(pypinyin.pinyin(char,style=Style.TONE3,heteronym=True,neutral_tone_with_five=True)[0]) for char in utterance]
    pinyin_lists = tuple(convert_to_pinyin(convert_single_word_to_pinyin(char,heteronym=True)) for char in utterance)
    all_pinyin = [[]]
    for pinyins in pinyin_lists:
        next_pinyin = []
        for cur_pinyin in pinyins:
            for pinyin_comb in all_pinyin:
                next_pinyin.append(pinyin_comb+[cur_pinyin])
        all_pinyin = next_pinyin
    return all_pinyin

@lru_cache(maxsize=8192)
def get_minimum_distance(utterA,utterB,threshold=None):
    assert len(utterA) == len(utterB)
    l = len(utterA)
    utterAp = '';utterBp = ''
    for cA,cB in zip(utterA,utterB):
        if cA != '_' and cB != '_':
            utterAp += cA;utterBp += cB
    minimal_distance = sys.float_info.max
    for pA in list_all_pinyin(utterAp):
        for pB in list_all_pinyin(utterBp):
            print(pA,pB)
            minimal_distance = min(minimal_distance,get_pinyin_distance(pA,pB,length = l))
            if threshold and minimal_distance <= threshold:
                return True
    if threshold: return False
    return minimal_distance

@lru_cache(maxsize=8192)
def to_pinyin(utterance):
    '''
    convert utterance to lists of pinyin
    '''
    translated = []
    pinyin_encodings = tuple(x[0] for x in pypinyin.pinyin(utterance,style=Style.TONE3,neutral_tone_with_five=True))
    return pinyin_encodings
    translated = [putToneToEnd(curPinyin[0]) for curPinyin in pinyin_encodings]

    return translated

def putToneToEnd(input_pinyin):
    '''
    convert pinyin format,
    put the tone at the end
    '''
    if len(input_pinyin) == 1:
        return input_pinyin + '1'
    tone_index = 0
    tone = '1'
    for index, character in enumerate(input_pinyin):
        if character in "1234":
            tone_index = index
            tone = input_pinyin[index]
            break;
    else:
        return input_pinyin + "5"
    return input_pinyin[0:index] + input_pinyin[index+1:] + tone

def get_distance(utterance1, utterance2):
    assert len(utterance1) == len(utterance2), f'Inputs {utterance1} and {utterance2} has different length'
    u1 = to_pinyin(utterance1)
    u2 = to_pinyin(utterance2)
    assert len(u1) == len(u2)

    la = tuple((Pinyin(py) for py in u1))
    lb = tuple((Pinyin(py) for py in u2))
    return get_pinyin_distance(la,lb)

@lru_cache(maxsize=4096)
def get_spinyin_distance(apy,bpy):
    res = getEditDistanceClose_TwoDCode(apy,bpy)
    nD = (apy.consonant!=bpy.consonant)+(apy.vowel!=bpy.vowel)+0.01*(apy.tone!=bpy.tone)
    return res,nD

def get_pinyin_distance(la,lb,length = None):
    if not length:
        length = len(la)
    res = 0.0
    numDiff = 0        
    tot = length*2.1
    for apy,bpy in zip(la,lb):
        rres,rnD = get_spinyin_distance(apy,bpy)
        res += rres;numDiff += rnD
                
    diffRatio = (numDiff)/tot;
    return res*diffRatio;
            
@lru_cache(maxsize=4096)
def getEditDistanceClose_TwoDCode(a, b):
    '''
    Function measuring Edit Distance between two Pinyin Object.
    Use the minimum of distance between consonants, vowels, and hardcoded distance, adding the tone difference.
    '''
    res = 0
    try:
        if (not a) or (not b):
            #print(f'Error:pinyin({a},{b})')
            return sys.float_info.max
        
        twoDcode_consonant_a = consonantMap_TwoDCode[a.consonant]
        twoDcode_consonant_b = consonantMap_TwoDCode[b.consonant]
        
        cDis = getDistance_TwoDCode(twoDcode_consonant_a, twoDcode_consonant_b)
        
        twoDcode_vowel_a = vowelMap_TwoDCode[a.vowel]
        twoDcode_vowel_b = vowelMap_TwoDCode[b.vowel]
        
        vDis = getDistance_TwoDCode(twoDcode_vowel_a, twoDcode_vowel_b)

        hcDis = getSimDisFromHardcodMap(a,b)
        
        res = min((cDis+vDis),hcDis) + abs(a.tone-b.tone)/10
        
    except:
        raise
    return res

@lru_cache(maxsize=512)
def getSimDisFromHardcodMap(a, b):
    '''
    Tool function measuring Hardcode Map
    Input: a,b two Pinyin object
    Output: 2.0 if a,b is in hardcode Map, else Infinity.
    '''
    if a.toStringNoTone() not in hardcodeMap:
        a,b = b,a
    if a.toStringNoTone() not in hardcodeMap or b.toStringNoTone() != hardcodeMap[a.toStringNoTone()]:
        return sys.float_info.max
    return 2.0
    
@lru_cache(maxsize=512)
def getDistance_TwoDCode(X, Y):
    '''
    2D distance function
    '''
    x1, x2 = X;y1, y2 = Y

    x1d = x1-y1
    x2d = x2-y2
    
    return sqrt(x1d*x1d + x2d*x2d)


consonantMap_TwoDCode ={
    "b":(1.0,0.5),
    "p":(1.0,1.5), 

    "g":(7.0,0.5), 
    "k":(7.0,1.5), 
    "h":(7.0,3.0), 
    "f":(7.0,4.0), 

    "d":(12.0,0.5), 
    "t":(12.0,1.5), 

    "n":(22.5,0.5), 
    "l":(22.5,1.5), 
    "r":( 22.5,2.5), 

    
    "zh":(30,1.7), 
    "z":(30,1.5), 
    "j":(30.0,0.5), 

    "ch":(31,1.7), 
    "c":(31,1.5), 
    "q":(31.0,0.5), 

    "sh":(33,3.7),
    "s":(33,3.5),
    "x":(33,2.5),

    
    "m":(50.0,3.5), 

    "y":(40.0,0.0), 
    "w":(40,5.0),
    
    "":(99999.0,99999.0)
}

vowelMap_TwoDCode = {
    "a":(1.0,0.0),
    "an":(1.0,1.0),
    "ang":(1.0,1.5),

    
    "ia":(0.0,0.0),
    "ian":(0.0,1.0),
    "iang":(0.0,1.5),

    "ua":(2.0,0.0),
    "uan":(2.0,1.0),
    "uang":(2.0,1.5),
    "u:an":(2.0,1.0),

    
    "ao":(5.0,0.0),
    "iao":(5.0,1.5),

    "ai":(8.0,0.0),
    "uai":(8.0,1.5),

    

    "o":(20,0.0),
    "io":(20,2.5),
    "iou":(20,4),
    "iu":(20,4),
    "ou":(20,5.5),
    "uo":(20,6.0),

    "ong":(20,8.0),
    "iong":(20,9.5),

    
    "er":(41,1),
    "e":(41,0.0),

    "u:e":(40,5.0),
    "ve":(40,5.0),
    "ue":(40,5.0),
    "ie":(40,4.5),
    "ei":(40,4.0),
    "uei":(40,3.0),
    "ui":(40,3.0),

    "en":(42,0.5),
    "eng":(42,1.0),

    "uen":(43,0.5),
    "un":(43,0.5),
    "ueng":(43,1.0),

    
    "i":(60,1.0),
    "in":(60,2.5),
    "ing":(60,3.0),

    "u:":(61,1.0),
    "v":(61,1.0),
    "u:n":(61,2.5),
    "vn":(61,2.5),

    "u":(80,0.0),

    "":(99999.0,99999.0)
}


consonantList = ("b", "p", "m", "f", "d", "t", "n", "l", "g", "k","h", "j", "q", "x", "zh", "ch", "sh", "r", "z", "c", "s", "y", "w")


vowelList = ("a", "o", "e", "i", "u", "v","u:","er", "ao","ai", "ou","ei", "ia", "iao", "iu", "iou","ie", "ui","uei","ua","uo","uai", "u:e","ve",  "an", "en", "in", "un","uen", "vn", "u:n", "ian", "uan", "u:an", "van", "ang", "eng", "ing", "ong", "iang", "iong", "uang", "ueng")

@lru_cache(maxsize=1058)
def parseConsonant(pinyin):
    for consonant in consonantList:
        if pinyin.startswith(consonant):
            return (consonant, pinyin[len(consonant):])
    if pinyin in vowelList:
        return None, pinyin
        
    assert False,f"Invalid Pinyin {pinyinstr}, Please check!"
    return None, None

@lru_cache(maxsize=1058)
def pinyinRewrite(consonant,vowel):
    '''
    Rewrite Pinyin format.
    '''
    yVowels = {"u","ue","uan","un","u:","u:e","u:an","u:n"}
    tconsonant = {"j","g","x"}
    vowel = vowel.replace("v","u:")
    replace_map = dict(iou='iu',uei='ui',uen='un')
            
    if not consonant:
        return vowel,consonant

    if "y" == consonant:
        if vowel in yVowels:
            if "u:" not in vowel:
                vowel = vowel.replace("u","u:")
        else:
            vowel="i"+vowel
            vowel = vowel.replace("iii","i")
            vowel = vowel.replace("ii","i")
            consonant=""
        
    elif "w" == consonant:
        vowel="u"+vowel;
        vowel=vowel.replace("uuu","u")
        vowel=vowel.replace("uu","u")
        consonant = ""
        
    elif (consonant in tconsonant) and ("u" == vowel) or ("v" == vowel):
        vowel= "u:"
        
    elif vowel in replace_map:
        vowel = replace_map[vowel]
    return consonant,vowel

class Pinyin:
    
    def __init__(self, pinyinstr):
        self.tone = int(pinyinstr[-1])
        self.consonant, self.vowel = pinyinRewrite(*parseConsonant(pinyinstr[0:-1].lower()))

    def __repr__(self):
        return self.toStringWithTone()
    
        
    def toStringNoTone(self):
        return f"{self.consonant}{self.vowel}"
    
    def toStringWithTone(self):
        return f"{self.consonant}{self.vowel}{self.tone}"
        


hardcodeMap = {
    "hua":"fa",
    "fa":"hua",
    "huan":"fan",
    "fan":"huan",
    "hui":"fei",
    "jie":"zhe",
    "kou":"ke",
    "gou":"ge",
    "zhong":"zen",
    "san":"shang"
}


consonantMap = {
    "b":1.0,
    "p":2.0,
    
    "m":11.0,
    "f":12.0,
    
    "d":21.0,
    "t":22.0,
    
    "n":31.0,
    "l":31.0,
    "r":32.0,
    
    "g":41.0,
    "k":42.0,
    "h":43.0,
    
    "j":46.0,
    "q":47.0,
    "x":48.0,
    
    "z":61.0,
    "c":62.0,
    
    "zh":71.0,
    "ch":72.0,
    
    "sh":81.0,
    "s":82.0,
    
    "y":90.0,
    "w":100.0,
    
    "":99999.0,
    "__v":99999.0
}



vowelMap = {
    "ia":0.0,
    "a":2.0,
    "ai":3.0,
    "uai":4.0,
    "iao":6.0,
    "ao":7.0,
    
    "uan":10.0,
    "an":11.0,
    "ang":12.0,
    "ian":14.0,
    "iang":15.0,
    "uang":17.0,
    "ua":18.0,
    
    "o":21.0,
    "io":22.0,
    "ou":23.0,
    "uo":24.0,
    "ong":26.0,
    "iong":27.0,
    
    "e":31.0,
    "ei":33.0,
    "ie":34.0,
    "er":37.0,
    
    "ve":40.0,
    "ue":40.0,
    "u:e":40.0,
    
    "en":43.0,
    "eng":44.0,
    
    "uen":45.0,
    "ueng":45.0,
    
    "u:en":42.0,
    "ven":42.0,
    
    "i":50.0,
    "u:":51.0,
    "v":51.0,
    "u:n":53.0,
    "vn":53.0,
    "u:an":55.0,
    "v:an":55.0,
    
    "in":53.0,
    "ing":55.0,
    
    "u":60.0,
    "ui":63.0,
    "uei":63.0,
    "iu":64.0,
    "iou":64.0,
    "un":66.0,
    
    "":99999.0,
    "__v":99999.0
}



doubleConsonantsMap = {}
doubleVowelsMap = {}

def getClosePinyinCandids(word, theta=2):
    res = []
    word_pinyin = to_pinyin(word)
    word_py = Pinyin(word_pinyin[0])
    
    cCandids = getConsonantCandids(theta, word_py)
    for i in range(len(cCandids)):
        if cCandids[i] == word_py.consonant:
            continue
        for j in range(1,5,1):
            newPy = cCandids[i]+word_py.vowel+str(j)
            res.append(Pinyin(newPy))
    
    vCandids = getVowelCandids(theta, word_py)
    for i in range(len(vCandids)):
        for j in range(1,5,1):
            newpy = (word_py.consonant if word_py.consonant else '')+vCandids[i]+str(j)
            res.append(Pinyin(newPy))
    return res
            
    
    
def getConsonantCandids(theta, word_py):
    populateDoubleConsonantsMap()
    res = []
    curCode = 0        
    if word_py.consonant:
        orgCode = consonantMap[word_py.consonant]
        for i in range(int(orgCode-theta), int(orgCode+theta), 1):
            if float(i) in doubleConsonantsMap:
                cand = doubleConsonantsMap[float(i)]
                if cand is not None:
                    res += cand
    else:
        orgCode = consonantMap["__v"]
    return res
    

def getVowelCandids(theta, word_py):
    populateDoubleVowelsMap()
    res = []
    curCode = 0        
    orgCode = vowelMap[word_py.vowel]
    for i in range(int(orgCode-theta), int(orgCode+theta), 1):
        if float(i) in doubleVowelsMap:
            cand = doubleVowelsMap[float(i)]
            if cand:
                res += cand
    return res

def populateDoubleConsonantsMap():
    if len(doubleConsonantsMap):
        return
    hmCdouble = consonantMap
    for consonant in hmCdouble:
        if hmCdouble[consonant] not in doubleConsonantsMap:
            doubleConsonantsMap[hmCdouble[consonant]] = []
            
        doubleConsonantsMap[hmCdouble[consonant]].append(consonant)
        
def populateDoubleVowelsMap():
    if len(doubleVowelsMap):
        return
    hmVdouble = vowelMap
    for vowel in hmVdouble:
        if hmVdouble[vowel] not in doubleVowelsMap:
            doubleVowelsMap[hmVdouble[vowel]] = []
            
        doubleVowelsMap[hmVdouble[vowel]].append(vowel)        
        

def getCandidates(sentence, mode="simplified", theta=1):
    candidates = []
    words_candidates = []
    for word in sentence:
        candid = getClosePinyinCandids(word, theta)
        words_candidates.append(candid)
    all_combinations = itertools.product(*words_candidates)
    counter = 0
    for combination in all_combinations:
        counter+=1
        searchKey = ""
        for i in combination:
            searchKey = searchKey + i.toStringWithTone().replace("None","") + " "
        if mode == "simplified":
            if searchKey.strip() in pinyin_to_simplified:
                candidates+=pinyin_to_simplified[searchKey.strip()]
        else:
            if searchKey.strip() in pinyin_to_traditional:
                candidates+=pinyin_to_traditional[searchKey.strip()]
    return candidates

if __name__ == '__main__':
    print(get_minimum_distance('瓦缶','挖否'))
    print(get_minimum_distance('东去秋来','东躲西藏'))
    print(get_distance('东去秋来','东躲西藏'))
    print(get_minimum_distance('东_秋_','东躲秋藏'))
