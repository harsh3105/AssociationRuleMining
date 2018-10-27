#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import csv
import itertools

# generate the first largeset L1 by check the support of each item
def large1item_set_gen(tablename, min_sup, sup_table):
    large1item_list = []
    num_trans = 0.0
    # open csv file
    with open(tablename, 'rU') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        # get the headers
        headers = spamreader.next()
        # each row is a transaction
        for row in spamreader:
            # count total num of transactions
            num_trans += 1
            # collection items
            for i, item in enumerate(row):
                item_id = 'id_%02d_%s'%(i, item)
                large1item_list.append(item_id)
    # list -> set: remove the repeated items
    large1item_set = set(large1item_list)  
    # filter items by sup_min  
    large1item_set_pass = set([])
    for item in large1item_set:
        sup = large1item_list.count(item)/num_trans
        if sup >= min_sup:
            large1item_set_pass.add(item)
            # save supports to sup_table
            sup_table[item] = sup
    
    return large1item_set_pass, num_trans, sup_table, headers

# generate candidate itemset Ck by Lk-1 
def candidate_gen(previous_list, size):
    candidate_list = []
    # for p, q in Ck-1 
    for p in previous_list:
        for q in previous_list:
            candidate = p[:]
            if size < 2:
                print ('size should be >= 2')
                exit()
            elif size == 2:
                if p[0] < q[0]:
                    candidate.append(q[0])
                    #print 'candidate1: ', candidate 
                    candidate_list.append(candidate)
            elif p[0:size-2] == q[0:size-2]:
                if p[size-2] < q[size-2]:
                    candidate.append(q[size-2])
                    # check each subset in generated itemset is also included in Lk-1           
                    candidate_subsets = itertools.combinations(candidate, size-1)
                    check = True
                    for subset in candidate_subsets:
                        if list(subset) not in previous_list:
                            check = False
                            break
                    if check:
                        candidate_list.append(candidate)
                        #print 'candidate2: ', candidate 
    return candidate_list

class Tee(object):
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj)

# compute the supports for each itemset
def scan_table_sup(tablename, candidate_list, min_sup, num_trans, sup_table):
    count_list = [0.0]*len(candidate_list)
    # opent the csv file
    with open(tablename, 'rU') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        # get the header
        headers = spamreader.next()
        # each row is an transaction
        for row in spamreader:
            #for each candidate itemset
            for c, candidate in enumerate(candidate_list):
                # check the items in this itemset occuring in the transcation
                check = True
                for attr in candidate:
                    #'id_04_XXXX', int(attr[3:5]) is the column index, attr[6:] is the string
                    if row[int(attr[3:5])] != attr[6:]:
                        check = False
                        break
                # if pass the check, count this itemset + 1
                if check:
                    count_list[c] += 1
    largeset = []
    # filter the itemset by min_sup, and save the score in sub_table
    for c, count in enumerate(count_list):
        sup = count/num_trans
        if  sup >= min_sup:
            largeset.append(candidate_list[c])
            sup_table[''.join(candidate_list[c])] = sup
    return largeset, sup_table

# substitute '-', ' ', '' as 'null'
def null_check(item_list):
    item_list_checked = []
    for item in item_list:
        #'id_04_XXXX'
        if (item != '-') and (item != ' ') and (item != ''):
            item_list_checked.append(item)
        else:
            item = 'null'
            item_list_checked.append(item)
    return item_list_checked

# compute confidence of each itemset
def conf_compute(largeset_list, sup_table, conf_min, headers):
    rule_confs = []
    rules = []
    # for each size of largerset
    for largeset in largeset_list[1:]:
        # for each itemset in largeset
        for items in largeset:
            # for each item in itemset, consider it as RHS (only one item) 
            for item in items:
                item_set = set(items)
                item_set.remove(item)
                RHS = [item]
                # for different size of LHS
                for k in range(1,len(item_set)+1):
                    # generate possible combinations for LHS from items with size k 
                    LHS_list = itertools.combinations(item_set, k)
                    for LHS in LHS_list:
                        # fix the order of item in LHS to avoid repetitions
                        LHS = sorted(LHS)
                        LHS_RHS = LHS[:]
                        LHS_RHS.append(RHS[0]) 
                        LHS_RHS_str = ''.join( sorted(LHS_RHS) ) # union of LHS and RHS
                        LHS_str = ''.join( LHS )
                        # compute the confidences by supports
                        sup_LHS_RHS = sup_table[LHS_RHS_str]
                        conf = sup_LHS_RHS / sup_table[LHS_str]
                        # filter the rules by conf_min
                        if conf >= conf_min:
                            # remove 'id_XX_'
                            LHS_short = [ x[6:] for x in LHS ]
                            RHS_short = [ RHS[0][6:] ]
                            # substitute '-', ' ', '' as 'null'
                            LHS_short = null_check(LHS_short)
                            RHS_short = null_check(RHS_short)
                            # get the headers of rules
                            LHS_header = [ headers[int(x[3:5])] for x in LHS ]
                            RHS_header = [ headers[int(RHS[0][3:5])] ]
                            # display the rules
                            rule = '['
                            for i, item in enumerate(zip(LHS_short, LHS_header)):
                                if i != 0:
                                    rule += ', '
                                rule += '(%s = %s)'%(item[1], item[0])
                            rule += '] => [(%s = %s)]'%(RHS_header[0], RHS_short[0])
                            if rule not in rules:
                                rules.append(rule)
                                rule_confs.append((rule, conf, sup_LHS_RHS))
    return rule_confs


def main():

    tablename = sys.argv[1]
    min_sup = float(sys.argv[2])
    min_conf = float(sys.argv[3])

    sup_table = {}

    # get the largeset with only one item
    large1item_set, num_trans, sup_table, headers = large1item_set_gen(tablename, min_sup, sup_table)
    large1item_list = sorted([[x] for x in large1item_set])
    
    # Largeset L1
    largeset = large1item_list
    largeset_list = []
    largeset_list.append(large1item_list)
    
    # loop for a-prior algorithm
    k = 2
    while True:
        # generate candidate set Ck
        candidate_list = candidate_gen(largeset, k)
        # Scan the table to get the supports for each itemset in Ck, and filter them by min_sup to get the largeset Lk 
        largeset, sup_table = scan_table_sup(tablename, candidate_list, min_sup, num_trans, sup_table)
        # if no item returned, break the loop
        if len(largeset) > 0:
            largeset_list.append(largeset)
            k += 1
        else:
            break

    f = open('output.txt', 'w')
    sys.stdout = Tee(sys.stdout, f)

    # Display frequent itemsets 
    print '==Frequent itemsets (min_sup=%d%%)'%(min_sup*100)
    largeset_all_level = []
    for k, largeset in enumerate(largeset_list):
        for items in largeset:
            items_str = ''.join(items)
            sup = sup_table[items_str]
            items_short = [x[6:] for x in items]
            items_short = null_check(items_short)
            items_header = [headers[int(x[3:5])] for x in items]
            largeset_all_level.append((zip(items_short, items_header,), sup))
    # Sort the itemsets by supports
    largeset_all_level.sort(key=lambda tup: tup[1])
    largeset_all_level.reverse()
    for items in largeset_all_level:
        print '[',
        for i, item in enumerate(items[0]):
            if i != 0:
                print ',',
            print '(%s = %s)'%(item[1], item[0]),
        print '], %d%%'%(items[1]*100)

    # Display High-confidence association rules 
    print '==High-confidence association rules (min_conf=%d%%)'%(min_conf*100)
    rule_confs = conf_compute(largeset_list, sup_table, min_conf, headers)
    # Sort the rules by confidence
    rule_confs.sort(key=lambda tup: tup[1])
    rule_confs.reverse()
    for rule_conf in rule_confs:
        print '%s (confidence = %d%%, support = %d%%)'%(rule_conf[0], rule_conf[1]*100, rule_conf[2]*100)


main()
