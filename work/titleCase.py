#!/usr/bin/env python3
# coding: utf-8
#
# generate Audit Data Collection xBRL-GD Taxonomy fron CSV file and header files
#
# designed by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)
# written by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)
#
# MIT License
#
# (c) 2023 SAMBUICHI Nobuyuki (Sambuichi Professional Engineers Office)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# from jsonschema import validate
from cgi import print_directory
# from distutils.debug import DEBUG
# import json
# from pyrsistent import b
import argparse
import os
# import yaml
import sys
import csv
import re
# import hashlib
# import datetime
abbreviation_map = {
    'ACC':'Account',
    'ADJ':'Adjustment',
    'BAS':'Base',
    'BEG':'Beginning',
    'CUR':'Currency',
    'CUS':'Customer',
    'FOB':'Free On Board',
    'FS':'Financial Statement',
    'INV':'Inventory',
    'IT':'Information Technology',
    'JE':'Journal Entry',
    'NUM':'Number',
    'ORG':'Organization',
    'PK':'Primary Key',
    'PO':'Purchase Order',
    'PPE':'Property Plant and Equipment',
    'PRV':'Province',
    'PUR':'Purchase',
    'REF':'Reference Identifier',
    'RFC':'Request For Comments',
    'SAL':'Sales',
    'TIN':'Tax Identification Number',
    'TRX':'Transactional',
    'UOM':'Unit of Measurement',
    'WIP':'Work In Progress'
}

SEP = os.sep

def file_path(pathname):
    if SEP == pathname[0:1]:
        return pathname
    else:
        pathname = pathname.replace('/',SEP)
        dir = os.path.dirname(__file__)
        new_path = os.path.join(dir, pathname)
        return new_path

# lower camel case concatenate
def LC3(term):
    if not term:
        return ''
    terms = term.split(' ')
    name = ''
    for i in range(len(terms)):
        if i == 0:
            if 'TAX' == terms[i]:
                name += terms[i].lower()
            elif len(terms[i]) > 0:
                name += terms[i][0].lower() + terms[i][1:]
        else:
            name += terms[i][0].upper() + terms[i][1:]
    return name

# snake concatenate
def SC(term):
    if not term:
        return ''
    terms = term.split(' ')
    name = '_'.join(terms)
    return name

def getLC3_DEN(adc_id):
    den = getDEN(adc_id)
    if den:
        den = den[:den.find('.')]
        return LC3(den)
    return ''

def getClassName(adc_id):
    den = getDEN(adc_id)
    if den:
        cn = den[5:den.find('.')]
        return cn
    return ''

def expand_abbreviations(s, abbreviation_map):
    words = s.split()
    expanded_words = []

    for word in words:
        if word.upper() in abbreviation_map:
            expanded_words.append(abbreviation_map[word.upper()])
        else:
            expanded_words.append(word.capitalize())

    return " ".join(expanded_words)

if __name__ == '__main__':

    class_name = []
    with open(file_path('referenced.txt'), encoding='utf-8', newline='') as f:
        reader = csv.reader(f)#, delimiter='\t')
        next(reader)
        for cols in reader:
            name = cols[0]
            name = expand_abbreviations(name, abbreviation_map)
            class_name.append(name)

    with open(file_path('referenced_name.txt'), mode="w", encoding="utf-8-sig") as file:
        file.write('Oject Class term (entity)\n')
        for d in class_name:
            file.write(f'{d}\n')

    print('END')