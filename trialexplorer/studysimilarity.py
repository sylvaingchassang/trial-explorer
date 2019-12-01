"""
module for determining the similarity of a study in terms of the conditions studied and the intervention used
"""
import nltk
import re
import string


def featurize_conditions(df):
    """
    takes a dataframe of studies and featurizes it into the the features used to determine similarity to other studies
    """


######################
# --- MESH ---#
######################


def get_mesh_terms(nctid1, nctid2, data):
    """ returns 2 lists of mesh terms """
    if nctid1 not in data.index:
        s1terms = []
    else:
        sub_df1 = data.loc[[nctid1]]
        s1terms = list(sub_df1['mesh_term'].unique())

    if nctid2 not in data.index:
        s2terms = []
    else:
        sub_df2 = data.loc[[nctid2]]
        s2terms = list(sub_df2['mesh_term'].unique())
    return s1terms, s2terms


def mesh_jaccard_dist(nctid1, nctid2, data):
    s1terms, s2terms = get_mesh_terms(nctid1, nctid2, data)
    return list_jaccard_dist(s1terms, s2terms)


######################
# --- NLTK ---#
######################


def extract_adj_and_vb(condition_str):
    cur_cond = condition_str.lower()
    cur_tokens = nltk.word_tokenize(cur_cond)
    pos_tags = nltk.pos_tag(cur_tokens)

    all_jj, all_vb = [], []
    for word, tag in pos_tags:
        if tag[:2] == 'JJ':
            if word not in all_jj:
                all_jj.append(word)
        if tag[:2] == 'VB':
            if word not in all_vb:
                all_vb.append(word)
    return all_jj, all_vb


######################
# --- STAGE, TYPE, GRADES ---#
######################


all_keywords = ['type', 'genotyp_', 'grade', 'stage', 'ajcc', 'hepatitis']

word_nums = [
    'zero', 'one', 'two', 'three', 'four',
    'five', 'six', 'seven', 'eight', 'nine',
    'ten', 'eleven', 'twelve', 'thirteen', 'fourteen',
    'fifteen', 'sixteen', 'seventeen', 'eighteen', 'ninteen',
    'twenty'
]

word2num = dict(zip(word_nums, range(0, 21)))


######################################################
# stage 1 preprocessing that occurs on the raw string:
######################################################

def convert_word2num(cur_text):
    """ finds all of the english numbers in a string and replace with numerical numbers """
    rex = r'\s' + "|".join(word_nums) + r'\s'
    found_list = re.findall(rex, cur_text)
    if len(found_list) > 0:
        for found_text in found_list:
            sub_to = word2num[found_text.strip()]
            cur_text = re.sub(rex, str(sub_to), cur_text)
    return cur_text


def convert_roman_to_str(cur_text):
    """ remove roman numeral charsets """
    # only first 7
    rn_map = {
        chr(8544): 'i',
        chr(8545): 'ii',
        chr(8546): 'iii',
        chr(8547): 'iv',
        chr(8548): 'v',
        chr(8549): 'vi',
        chr(8550): 'vii',
        chr(8560): 'i',
        chr(8561): 'ii',
        chr(8562): 'iii',
        chr(8563): 'iv',
        chr(8564): 'v',
        chr(8565): 'vi',
        chr(8566): 'vii',
    }

    for k, v in rn_map.items():
        cur_text = cur_text.replace(k, v)
    return cur_text


def preprocess_cond_str(cur_cond):
    """ all preprocessing routines """
    # word2num
    cur_cond = convert_word2num(cur_cond)

    # "through" delim
    cur_cond = cur_cond.replace(' through ', '-')

    # "and" delim
    cur_cond = cur_cond.replace(' and ', ',')

    # plural keywords
    pl_kw = {
        'stages': 'stage',
        'grades': 'grade',
        'types': 'type',
        'genotypes': 'genotyp_',
        'genotype': 'genotyp_'
    }
    for k, v in pl_kw.items():
        cur_cond = cur_cond.replace(k, v)

    # connector delims
    range_delims = {
        " - ": "-",
        " -": "-",
        "- ": "-",
        " / ": "/",
        " /": "/",
        "/ ": "/",
    }
    for k, v in range_delims.items():
        cur_cond = cur_cond.replace(k, v)

    # inherient roman numerals in symbol
    cur_cond = convert_roman_to_str(cur_cond)

    # ajcc abbrev.
    ajcc_re = r'\s?\(american joint committee on cancer\s?\)\s?'
    cur_cond = re.sub(ajcc_re, '', cur_cond)
    return cur_cond


#########################################################
# stage 2 preprocessing that occurs at the kw_split level
#########################################################

def preprocess_kw_split(kw_split):
    """ preprocessing for the kw split level """

    # replace leading dashes
    kw_split = re.sub(r'^\s?-', '', kw_split)

    # strip spaces
    kw_split = kw_split.strip()

    return kw_split


#########################################################
# stage 3 preprocessing that occurs at the element level
#########################################################

def preprocess_element(element):
    """ proprocessing for the element level """
    # replace roman numerals with numbers
    # possible extension, extend to full number system
    roman_map = {
        'i': 1,
        'ii': 2,
        'iii': 3,
        'iv': 4,
        'v': 5,
        'vi': 6,
        'vii': 7,
        'viii': 8,
        'ix': 9,
        'x': 10,
        'xi': 11,
        'xii': 12,
        'xiii': 13,
        'xiv': 14,
        'xv': 15,
        'xvi': 16,
        'xvii': 17,
        'xviii': 18,
        'xix': 19,
        'xx': 20,
    }

    src_roman = '^i[vx]|^i{1,3}|^vi{1,3}|^xi[vx]|^xi{1,3}|^xvi{0,3}|^[xv]'
    find_list = re.findall(src_roman, element)
    if len(find_list) > 0:
        found_str = find_list[0]
        to_rep = roman_map[found_str]
        element = re.sub(src_roman, str(to_rep), element)

    # replace brackets
    element = element.replace(')', '')
    element = element.replace('(', '')

    # replace 'diabetes' with ''
    element = element.replace('diabetes', '')

    return element


# some kws use 1 regex pattern, ajcc uses another
src1_delimiter = r'[\s*\,\-\;\)\(]'

src1 = r'^\d[\w\(\)]*' + src1_delimiter + '*|' + \
       r'^i{2,3}v?[\w\(\)]*' + src1_delimiter + '*|' + \
       r'^vi{2,3}[\w\(\)]*' + src1_delimiter + '*|' + \
       r'^iv?[a-e]?\d*' + src1_delimiter + '+|' + \
       r'^iv?[a-e]?\d*$|' + \
       r'^v\d*' + src1_delimiter + '+|' + \
       r'^v\d*$|' + \
       r'^vi[a-z]\d*' + src1_delimiter + '+|' + \
       r'^vi[a-z]\d*$|' + \
       r'^[A-Fa-f]\d*' + src1_delimiter + '+|' + \
       r'^[A-Fa-f]\d*$|' + \
       r'^her\d\+?'


src2 = r'^v\d[\w\(\)]*[\s*\,\-]*'  # ajcc

src3 = r'^[abcde]'
regex_dict = {
    'grade': src1,
    'type': src1,
    'genotyp_': src1,
    'stage': src1,
    'ajcc': src2,
    'hepatitis': src3,
}

# pattern for delimiter
src_delim = r'[\s*\,\-]+$'


def extract_elements_delims(cur_text, regex_str, kw, do_element_pp=True, do_print=False):
    elements = []
    delimiters = []

    kw_splits = cur_text.split(kw)
    if do_print:
        print(kw_splits)

    if len(kw_splits) == 1:
        return elements, delimiters  # kw not found

    for i, raw_kw_split in enumerate(kw_splits):
        if i == 0:  # if the first split has no space, then the kw was part of another word
            if len(raw_kw_split) != 0 and raw_kw_split[-1] in string.ascii_letters:
                if do_print: print('not a real split')
                break  # not a real split

        if i > 0:  # ignore first split
            cur_kw_split = preprocess_kw_split(raw_kw_split)
            if do_print: print(cur_kw_split)
            do_loop = True
            while do_loop:
                # find the element and delimiter
                cur_ele_list = re.findall(regex_str, cur_kw_split)
                if len(cur_ele_list) > 0:
                    remaining = cur_ele_list[0]
                    # if we have an element then look for the delimiter
                    delim = re.findall(src_delim, remaining)
                    if len(delim) > 0:
                        if delim[0].strip() == '-':
                            delim_char = '-'
                        else:
                            delim_char = ','
                        delimiters.append(delim_char)
                        # remove delimiter
                        remaining = re.sub(src_delim, '', remaining)
                    else:
                        do_loop = False

                    # append element
                    if do_element_pp:
                        elements.append(preprocess_element(remaining).strip())
                    else:
                        elements.append(remaining.strip())
                    # remove the element
                    cur_kw_split = re.sub(regex_str, '', cur_kw_split)
                else:
                    do_loop = False
    return elements, delimiters


def digstr2parts(digstr):
    """ returns a tuple of the digit and the string parts, if no num part, returns Null for that part """
    re_pattern = '^[0-9]+'
    f_list = re.findall(re_pattern, digstr)
    if len(f_list) == 0:
        return None, digstr  # no number part
    else:
        num_part = int(f_list[0])
        chr_part = re.sub(re_pattern, '', digstr)
        return num_part, chr_part


def post_process_element_delimiters(elements, delimiters):
    enumeratable_letters = 'abcdef'

    if '-' not in delimiters:
        return elements
    else:
        cur_elements = []
        prev_start_num = None

        for i, delim in enumerate(delimiters):
            # print(i, delim)
            if delim == '-':
                if len(elements) <= i + 1:
                    # print('returning cond')
                    return cur_elements  # return if there is no closing element for the current delimiter
                else:
                    start_num, start_letter = digstr2parts(elements[i])
                    end_num, end_letter = digstr2parts(elements[i + 1])
                    # print(start_num, end_num, start_letter, end_letter)

                    ####################
                    # handle cases here
                    ####################

                    # case 1: we have both start and end nums
                    if start_num and end_num:  # both not None
                        first_loop = True
                        for i in range(start_num, end_num):
                            cur_ele = str(i)
                            if first_loop:
                                cur_ele += start_letter

                            cur_elements.append(cur_ele)
                            first_loop = False

                        # on the end_num enumerate the letters
                        if end_letter != '' and end_letter in enumeratable_letters:
                            for j in range(ord('a'), ord(end_letter) + 1):
                                append_chr = chr(j)
                                cur_ele = str(end_num) + append_chr
                                cur_elements.append(cur_ele)
                        else:
                            cur_elements.append(str(end_num))

                    # case 2: have only letters - enumerate all the letters
                    elif start_num is None and end_num is None:
                        if start_letter != '' and end_letter != '' and \
                                start_letter in enumeratable_letters and \
                                end_letter in enumeratable_letters:
                            for j in range(ord(start_letter), ord(end_letter) + 1):
                                cur_ele = chr(j)
                                cur_elements.append(cur_ele)

                    # case 3: we have start num but no end nums - enumerate only the start num letters
                    elif start_num and end_num is None:
                        if start_letter != '' and end_letter != '' and \
                                start_letter in enumeratable_letters and \
                                end_letter in enumeratable_letters:
                            for j in range(ord(start_letter), ord(end_letter) + 1):
                                append_chr = chr(j)
                                cur_ele = str(start_num) + append_chr
                                cur_elements.append(cur_ele)

                    # case 4: no start num, but end num and prev num - enumerate all numbers except first
                    # and no end letter
                    elif start_num is None and end_num and prev_start_num and end_letter == '':
                        for i in range(prev_start_num + 1, end_num + 1):
                            cur_ele = str(i)
                            cur_elements.append(cur_ele)

                    # case 5: no start num, but end num and prev num - enumerate all numbers except first
                    # and has end letter
                    elif start_num is None and end_num and prev_start_num and end_letter != '':
                        for i in range(prev_start_num + 1, end_num):
                            cur_ele = str(i)
                            cur_elements.append(cur_ele)

                        if end_letter in enumeratable_letters:
                            for j in range(ord('a'), ord(end_letter) + 1):
                                append_chr = chr(j)
                                cur_ele = str(end_num) + append_chr
                                cur_elements.append(cur_ele)
                        else:
                            cur_ele = str(end_num) + end_letter
                            cur_elements.append(cur_ele)

                    # storing prev loop values
                    prev_start_num = start_num

        return cur_elements


def full_extract(orig_cond):
    """ fully extract elements and delimiters from a condition string """
    preped_cond = preprocess_cond_str(orig_cond)
    extracted_dict = {}
    has_val = False

    for kw in all_keywords:
        regex_str = regex_dict[kw]
        do_element_pp = True
        if kw == 'ajcc':
            do_element_pp = False  # no not subsitute romans for ajcc

        elements, delimiters = extract_elements_delims(preped_cond, regex_str, kw, do_element_pp=do_element_pp)

        """
        # count delimiters:
        dash_delim_count = 0
        for delim in delimiters:
            if delim == '-':
                dash_delim_count += 1
        if dash_delim_count >= 1:
            print(orig_cond)
            print(elements, delimiters)
        """

        # post process the elements and delimiters for all elements:
        all_elements = post_process_element_delimiters(elements, delimiters)
        if len(all_elements) > 0:
            has_val = True

        extracted_dict[kw] = all_elements

    if has_val:
        return extracted_dict
    else:
        return None


######################
# --- HELPERS ---#
######################


def list_jaccard_dist(l1, l2):
    """ provided 2 lists, compute the jacard similarity between them """
    full_list = []
    for cur_term in l1:
        full_list.append(cur_term)
    for cur_term in l2:
        if cur_term not in full_list:
            full_list.append(cur_term)

    if len(full_list) == 0:
        return -1.
    intersect_count = 0
    for term in full_list:
        if term in l1 and term in l2:
            intersect_count += 1

    return intersect_count / len(full_list)



