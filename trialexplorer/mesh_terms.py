"""
Module for working with MeSH terms
"""
import os
from ftplib import FTP
from xml.etree import ElementTree
from trialexplorer import config

"""
Relevant XML paths

ROOT
- DescriptorRecord
-- DescriptorName
--- String: The MeSH term is located here (ex. Calcimycin)
-- TreeNumberList
--- TreeNumber: dot delimited Tree address is located here (ex. D03.633.100.221.173)
-- ConceptList
--- Concept
---- TermList
----- Term
------ String: The alias terms are located here, has n-to-1 relationship with the DescriptorName.String attr above
"""


class MeSHCatalog:
    """
    handles the downloading of the MeSH xml, the parsing of the terms and lookup of terms
    """
    def __init__(self, filename='desc2020.xml'):
        self.root = None
        self.tree2term = {}
        self.term2trees = {}
        self.load_file(filename=filename)
        self._map_term2tree()
        self._map_tree2term()

    def load_file(self, filename='desc2020.xml'):
        if not os.path.exists('xml'):
            os.makedirs('xml')
            _fetch_ftp_file(filename)
        elif not os.path.isfile("xml/%s" % filename):
            _fetch_ftp_file(filename)

        self._load_from_local(filename)

    def get_trees(self, mesh_term):
        return self.term2trees[mesh_term]

    def get_levels(self, mesh_term):
        """
        returns the level(s) of a particular term
        """
        tree_nums = self.term2trees[mesh_term]
        all_levels = []
        for tree_num in tree_nums:
            cur_level = len(tree_num.split('.'))
            if cur_level not in all_levels:
                all_levels.append(cur_level)
        return sorted(all_levels)

    def lookup_higher_level(self, mesh_term, level):
        """ looksup a term that is at a higher or equal level than at least 1 of the current term's levels """
        tree_nums = self.term2trees[mesh_term]
        all_lookups = []
        for tree_num in tree_nums:
            cur_split_tree = tree_num.split('.')
            cur_level = len(cur_split_tree)
            if level <= cur_level:
                cur_lookup = '.'.join(cur_split_tree[:level])
                if cur_lookup not in all_lookups:
                    all_lookups.append(cur_lookup)

        all_terms = []
        for cur_lookup in all_lookups:
            if cur_lookup in self.tree2term.keys():
                cur_term = self.tree2term[cur_lookup]
                if cur_term not in all_terms:
                    all_terms.append(cur_term)
        return sorted(all_terms)

    def _load_from_local(self, filename):
        print("Parsing MeSH xml: xml/%s ..." % filename)
        tree = ElementTree.parse('xml/%s' % filename)
        self.root = tree.getroot()
        print("Parse Complete! (parsed ElementTree root can be found in the .root attribute)")

    def _map_tree2term(self):
        self.tree2term = {}  # reset the dict
        for c in self.root.getchildren():
            cur_term = c.find('DescriptorName').findtext('String')
            cur_treenums = c.find('TreeNumberList')
            if cur_treenums:
                for tn in cur_treenums.getchildren():
                    self.tree2term[tn.text] = cur_term

    def _map_term2tree(self):
        self.term2trees = {}
        for c in self.root.getchildren():
            # collect terms
            terms_to_process = [c.find('DescriptorName').findtext('String')]  # main term
            cl = c.find('ConceptList')
            if cl is not None:
                for concept in cl.getchildren():
                    term_list = concept.find('TermList')
                    if term_list is not None:
                        for term in term_list.getchildren():
                            cur_term = term.findtext('String')
                            if cur_term not in terms_to_process:
                                terms_to_process.append(cur_term)

            # collect tree nums
            tree_num_to_process = []
            tree_list = c.find('TreeNumberList')
            if tree_list is not None:
                for tree_num in tree_list.getchildren():
                    cur_tree_num = tree_num.text
                    if cur_tree_num not in tree_num_to_process:
                        tree_num_to_process.append(cur_tree_num)

            # map both
            for cur_term in terms_to_process:
                for tree_num in tree_num_to_process:
                    if cur_term in self.term2trees.keys():
                        self.term2trees[cur_term].append(tree_num)
                    else:
                        self.term2trees[cur_term] = [tree_num]


def _fetch_ftp_file(filename):
    print("No Local XML detected at xml/%s, Fetching file from FTP server for the first time ..." % filename)
    print('Remote Server: %s' % config.MESH_SERVER)
    print('Remote Dir: %s' % config.MESH_DIR)
    ftp = FTP(config.MESH_SERVER)
    ftp.login()
    ftp.cwd(config.MESH_DIR)
    with open('xml/%s' % filename, 'wb') as fp:
        ftp.retrbinary('RETR %s' % filename, fp.write)
    ftp.quit()
    print('local file written to xml/%s' % filename)
