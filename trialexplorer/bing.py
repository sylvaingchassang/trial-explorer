"""
module that search the web for features of a certain condition or treatment
"""
from bs4 import BeautifulSoup
import urllib
import requests
import numpy as np
import time

WAIT_TIME_MEAN = 1.0
WAIT_TIME_STD = 0.2
WAIT_TIME_FLOOR = 0.5
WAIT_TIME_CAP = 2.0

user_agent_list = [
    'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322)',
    'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36'
]


def random_ua():
    return np.random.choice(user_agent_list)


def do_wait(multiple=1.0):
    wait_time = np.random.normal(WAIT_TIME_MEAN, WAIT_TIME_STD)
    if wait_time < WAIT_TIME_FLOOR:
        wait_time = WAIT_TIME_FLOOR
    elif wait_time > WAIT_TIME_CAP:
        wait_time = WAIT_TIME_CAP
    time.sleep(wait_time * multiple)


def search(query):
    return "http://www.bing.com/search?q=%s" % (urllib.parse.quote_plus(query))


def begins_with(full_text, sub_text):
    if full_text[:len(sub_text)] == sub_text:
        return True
    return False


def include_content(cur_text, tag):
    exclude_prefixes = ['Click to view', 'See more on', 'Advertise', 'Help', 'Image:']
    if len(cur_text) == 0:
        return False
    for excl in exclude_prefixes:
        if begins_with(cur_text, excl):
            return False

    if 'href' in tag.attrs:
        if begins_with(tag['href'], 'https://'):
            return True

    return False


def print_sres(content_list):
    for i, c in enumerate(content_list):
        if include_content(c):
            print(c.get_text().strip() + "\n" + c['href'] + "\n")


def bing(search_term, do_print=True):
    if do_print:
        print("binging the term: %s" % search_term)
    wiki_prefix = 'https://en.wikipedia.org/'
    feat_doc = []
    feat_links = []
    feat_wiki = []

    url = search(search_term)
    headers = {'User-Agent': random_ua()}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content, 'html5lib')
    content_list = soup.find_all('a')

    # collecting terms
    for i, c in enumerate(content_list):
        cur_text = c.get_text().strip()

        if 'href' in c.attrs:
            cur_link = c['href']
        else:
            cur_link = 'NO LINK'

        if include_content(cur_text, c):
            feat_doc.append(cur_text)
            feat_links.append(cur_link)

            if begins_with(cur_link, wiki_prefix) and len(feat_wiki) == 0:
                wikiurl = cur_link
                wiki_r = requests.get(wikiurl, headers=headers)
                wiki_soup = BeautifulSoup(wiki_r.content, 'html5lib')
                wiki_title = wiki_soup.find('title').get_text()
                feat_wiki.append(wiki_title)

    if len(feat_wiki) == 0:
        # if the wiki page was not found, try bing again with a "wiki" prefix
        do_wait()
        url_wiki = search('wiki ' + search_term)
        r_wiki = requests.get(url_wiki, headers=headers)
        soup_wiki = BeautifulSoup(r_wiki.content, 'html5lib')
        cl_wiki = soup_wiki.find_all('a')
        for i, c in enumerate(cl_wiki):
            if 'href' in c.attrs and begins_with(c['href'], wiki_prefix):
                wikiurl = c['href']
                wiki_r = requests.get(wikiurl, headers=headers)
                wiki_soup = BeautifulSoup(wiki_r.content, 'html5lib')
                wiki_title = wiki_soup.find('title').get_text()
                feat_wiki.append(wiki_title)
                break

    return feat_doc, feat_links, feat_wiki
