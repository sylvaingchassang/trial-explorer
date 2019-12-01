"""
module for determining the similarity of a study in terms of the conditions studied and the intervention used
"""
import nltk
from nltk.corpus import stopwords
from nltk.probability import FreqDist
import re
import string
import numpy as np
from fuzzywuzzy import fuzz


######################
# --- FEATURIZERS ---#
######################

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


def mesh_jaccard_sim(nctid1, nctid2, data):
    s1terms, s2terms = get_mesh_terms(nctid1, nctid2, data)
    return list_jaccard_sim(s1terms, s2terms)


def mesh_tree_dist(nctid1, nctid2, data, mc):
    """ compute the set of all tree distances and returns tuple of min, max, mean """
    s1terms, s2terms = get_mesh_terms(nctid1, nctid2, data)

    all_dist = []
    for t1 in s1terms:
        for t2 in s2terms:
            cur_dist = mc.shortest_mesh_dist(t1, t2)
            all_dist.append(cur_dist)

    return min(all_dist), max(all_dist), np.mean(all_dist)


######################
# --- FUZZYWUZZY ---#
######################


def noun_partial_fuzzy_dist(c1, c2):
    cur_tokens1 = nltk.word_tokenize(c1)
    pos_tags1 = nltk.pos_tag(cur_tokens1)
    cur_nouns1 = ' '.join([x[0] for x in pos_tags1 if x[1] in ('NN', 'NNS')])

    cur_tokens2 = nltk.word_tokenize(c2)
    pos_tags2 = nltk.pos_tag(cur_tokens2)
    cur_nouns2 = ' '.join([x[0] for x in pos_tags2 if x[1] in ('NN', 'NNS')])
    return fuzz.partial_ratio(cur_nouns1, cur_nouns2)


def extract_nouns(c_in):
    cur_tokens = nltk.word_tokenize(c_in)
    pos_tags = nltk.pos_tag(cur_tokens)
    cur_nouns = ' '.join([x[0] for x in pos_tags if x[1] in ('NN', 'NNS')])
    return cur_nouns


def fuzzy_noun_dist(c1, c2):
    n1 = extract_nouns(c1)
    n2 = extract_nouns(c2)
    return fuzz.ratio(n1, n2)


######################
# --- ADJECTIVES AND VERBS ---#
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


def adj_and_vb_dist(adjvb1, adjvb2):
    adj1, vb1 = adjvb1[0], adjvb1[1]
    adj2, vb2 = adjvb2[0], adjvb2[1]
    adj_sim = list_jaccard_sim(adj1, adj2)
    vb_sim = list_jaccard_sim(vb1, vb2)
    return 1 - adj_sim, 1 - vb_sim

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

full_dissim_score = 10.


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


def calc_stage_diff(s1, s2):
    """ compute distance between 3b and 1 for example """
    enumeratable_letters = 'abcdef'
    d1, c1 = digstr2parts(s1)
    d2, c2 = digstr2parts(s2)

    # case 1, both digits are None
    if d1 is None and d2 is None and \
            c1 in enumeratable_letters and \
            c2 in enumeratable_letters:
        return abs(ord(c2) - ord(c1))

    # case 2, 1 digit is None
    if d1 is not None and d2 is None:
        return full_dissim_score
    if d1 is None and d2 is not None:
        return full_dissim_score

    # case 3,
    if d1 is not None and d2 is not None:
        if c1 == '' and c2 == '':
            return abs(d2 - d1)
        elif c1 != '' and c1 == c2:
            return abs(d2 - d1)
        else:
            return abs(d2 - d1) + .5

    return full_dissim_score


# function to compute simiarity between two extracted stage dicts
def stage_sim_dist(stage_dict1, stage_dict2):
    """ stage_dict has key type, grade etc
    if dissimilar, returns 10
    if stage, type, grade, returns number diff
    if both letters, returns char ord diff

    for full_match types applies an (1 - jaccard multiplier) to list diffs
    """
    # if 1 of the dict is blank, return full dissimilarity
    if stage_dict1 is None and stage_dict2 is None:
        return 0.
    elif stage_dict1 is None or stage_dict2 is None:
        return full_dissim_score

    # hepatitis, genotype, ajcc must be full match
    full_sim_required_types = ['hepatitis', 'ajcc', 'genotyp_']
    full_match_scores = []
    for cur_type in full_sim_required_types:
        if len(stage_dict1[cur_type]) > 0 and len(stage_dict2[cur_type]) > 0:
            one_m_jdist = 1 - list_jaccard_sim(stage_dict1[cur_type], stage_dict2[cur_type])
            full_match_scores.append(one_m_jdist * full_dissim_score)
        elif len(stage_dict1[cur_type]) > 0 or len(stage_dict2[cur_type]) > 0:
            full_match_scores.append(full_dissim_score)
    # if any was filled, then it means some full-match dicts were not null
    if len(full_match_scores) > 0:
        max_full_score = max(full_match_scores)
        if max_full_score > 0:  # only returns if the full match was non-zero other wise check part matches
            return max_full_score

    # grade, type, stage can be partially matched
    partial_sim_required_types = ['grade', 'type', 'stage']
    l1, l2 = [], []
    for cur_type in partial_sim_required_types:
        for cur_item in stage_dict1[cur_type]:  # append to l1
            if cur_item not in l1 and cur_item != '':
                l1.append(cur_item)
        for cur_item in stage_dict2[cur_type]:  # append to l2
            if cur_item not in l2 and cur_item != '':
                l2.append(cur_item)

    # the elements that are not matching contribute to the difference (if they match, they contribute 0 score)
    l1_diff, l2_diff = [], []
    l1_diff = [x for x in l1 if x not in l2]
    l2_diff = [x for x in l2 if x not in l1]

    # how many were matched?
    num_matched = len(l1) - len(l1_diff)
    num_diff = len(l1_diff) + len(l2_diff)

    # compute the average distance between l1 and l2 values
    all_min_dist = []
    for l1_diff_val in l1_diff:
        if len(l2_diff) > 0:  # exit condition
            all_dist = [calc_stage_diff(l1_diff_val, x) for x in l2_diff]
            min_dist = min(all_dist)
            min_idx = all_dist.index(min_dist)
            del l2_diff[min_idx]
            all_min_dist.append(min_dist)
        else:
            all_min_dist.append(full_dissim_score)

    # if any left in l2_diff, add them as fully dissim
    for l2_diff_val in l2_diff:
        all_min_dist.append(full_dissim_score)

    if len(all_min_dist) == 0:
        return 0.

    mean_dist = sum(all_min_dist) / len(all_min_dist)
    return mean_dist * num_diff / (num_matched + num_diff)


######################
# --- BAG OF WORDS FOR BING RESULTS ---#
######################

bag_of_words_topx = 25
stop_words = set(stopwords.words('english'))


def get_top_x_words(fdist_mc, x=bag_of_words_topx):
    """ only gets the top x words by count """
    cur_w_c = 0
    res_mc = []
    for word, n_occ in fdist_mc:
        if cur_w_c + n_occ < x:  # case 1 we haave capacity
            res_mc.append((word, n_occ))
            cur_w_c += n_occ
        else:  # case 2 fill to capacity
            n_capacity = x - cur_w_c
            res_mc.append((word, n_capacity))
            cur_w_c = x
            return dict(res_mc)
    return dict(res_mc)


def doc_to_tokencount(cur_doc, num_words=bag_of_words_topx):
    merged_cur_doc = ' '.join(cur_doc)
    cur_tokens = nltk.word_tokenize(merged_cur_doc)
    table = str.maketrans('', '', string.punctuation)
    stripped = [w.translate(table) for w in cur_tokens]
    no_blank_lower = [w.lower() for w in stripped if w != '']
    no_stop_words = [w for w in no_blank_lower if not w in stop_words]
    fdist = FreqDist(no_stop_words)
    most_common_100token = fdist.most_common(num_words)
    most_common_100w = get_top_x_words(most_common_100token, x=num_words)
    return most_common_100w


def wasserstein_dist(token_counts1, token_counts2):
    total_dist = 0
    # building dict of all keys
    full_list = list(token_counts1.keys())
    for k in token_counts2.keys():
        if k not in full_list:
            full_list.append(k)

    # looping through all keys
    for k in full_list:
        if k in token_counts1.keys() and k in token_counts2.keys():
            total_dist += abs(token_counts1[k] - token_counts2[k])  # add diff in counts
        elif k in token_counts1.keys():
            total_dist += token_counts1[k]  # add full count from token_count1
        elif k in token_counts2.keys():
            total_dist += token_counts2[k]  # add full count from token_count2

    return total_dist


######################
# --- LIST OF LINKS ---#
######################

def compute_link_list_sim(uniql1, uniql2):
    if len(uniql1) == 0 or len(uniql2) == 0:
        return 0.  # not similar if either is blank (jaccard returns 1 if both blank)
    else:
        return list_jaccard_sim(uniql1, uniql2)


######################
# --- WIKI---#
######################


def compute_wiki_sim(w1, w2):
    if len(w1) == 0 or len(w2) == 0:
        return 0.
    elif w1 == w2:
        return 1.
    else:
        return 0.


######################
# --- HELPERS ---#
######################


def list_jaccard_sim(l1, l2):
    """ provided 2 lists, compute the jacard similarity between them """
    full_list = []
    for cur_term in l1:
        full_list.append(cur_term)
    for cur_term in l2:
        if cur_term not in full_list:
            full_list.append(cur_term)

    if len(full_list) == 0:
        return 1.
    intersect_count = 0
    for term in full_list:
        if term in l1 and term in l2:
            intersect_count += 1

    return intersect_count / len(full_list)


def unique_list(cl):
    ul = []
    for i in cl:
        if i not in ul:
            ul.append(i)

    return ul

