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

DEBUG = False
VERBOSE = True
SEP = os.sep

xbrl_source = 'source/'
xbrl_source = xbrl_source.replace('/', SEP)
core_head = 'coreead.txt'
primarykey_file = 'primarykey.csv'

xbrl_base = 'taxonomy/H/'
# xbrl_base = xbrl_base.replace('/', SEP)
core_xsd = 'core.xsd'
core_label = 'core-lbl'
core_presentation = 'core-pre'
core_definition = 'core-def'
core_for_Card = 'core-for-Card'
core_for_Mandatory = 'core-for-Mandatory'

# shared_yaml = None

datatypeMap = {
    'Amount': {
        'adc':'amountItemType',
        'xbrli':'monetaryItemType'},
    'Binary Object': {
        'adc':'binaryObjectItemType',
        'xbrli':'stringItemType'},
    'Code': {
        'adc':'codeItemType',
        'xbrli':'tokenItemType'},
    'Date': {
        'adc':'dateItemType',
        'xbrli':'dateItemType'},
    'Document Reference': {
        'adc':'documentReferenceItemType',
        'xbrli':'tokenItemType'},
    'Identifier': {
        'adc':'identifierItemType',
        'xbrli':'tokenItemType'},
    'Indicator': {
        'adc':'indicatorItemType',
        'xbrli':'booleanItemType'},
    'Text': {
        'adc':'textItemType',
        'xbrli':'stringItemType'},
    'Time': {
        'adc':'timeItemType',
        'xbrli':'timeItemType'},
    'Percentage': {
        'adc':'percentageItemType',
        'xbrli':'pureItemType'},
    'Quantity': {
        'adc':'quantityItemType',
        'xbrli':'intItemType'},
    'Unit Price Amount': {
        'adc':'unitPriceAmountItemType',
        'xbrli':'monetaryItemType'},
 }

abbreviationMap = {
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
    'PPE':'Property, Plant and Equipment',
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

targetTables = ['GL02','GL55','GL56','GL57','GL58','GL59','GL60','GL61']

duplicateNames = set()
names = set()
adcDict = {}
targetRefDict = {}
associationDict = {}
referenceDict = {}
sourceRefDict = {}
locsDefined = {}
arcsDefined = {}
locsDefined = {}
alias = {}
targets = {}
roleMap = None
primaryKeys = set()

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

def getName(adc_id):
    record = getRecord(adc_id)
    if record:
        return record['name']
    return ''

def getDEN(adc_id):
    record = getRecord(adc_id)
    if record:
        return record['DEN']
    return ''

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

def getRecord(adc_id):
    if adc_id in adcDict:
        record = adcDict[adc_id]
    else:
        record = {}
    return record

def getParent(parent_id_list):
    parent_id = parent_id_list[-1]
    if parent_id in adcDict:
        parent = adcDict[parent_id]
    else:
        parent = None
    return parent

def getChildren(adc_id):
    record = getRecord(adc_id)
    if record:
        return record['children']
    return []

def domain_member(child_id, link_id, core_xsd, locsDefined, arcsDefined, lines):
    global count
    if not child_id in locsDefined[link_id]:
        locsDefined[link_id].add(child_id)
        lines.append(f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{child_id}" xlink:label="{child_id}" xlink:title="{child_id}"/>\n')
    count += 1
    arc_id = f'{link_id} {child_id}'
    if not arc_id in arcsDefined[link_id]:
        arcsDefined[link_id].add(arc_id)
        lines.append(f'\t\t<link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/domain-member" xlink:from="{link_id}" xlink:to="{child_id}" xlink:title="domain-member: {link_id} to {child_id}" order="{count}"/>\n')
    if DEBUG:
        print(f'domain-member: {link_id} to {child_id} order={count}')

def target_role(child_id, link_id, core_xsd, locsDefined, arcsDefined, targetRefDict, lines):
    global count
    target_id = targetRefDict[child_id]
    role_id = f'link_{target_id}'
    URI = f'/{role_id}'
    lines.append(f'\t\t<!-- {child_id} targetRole {role_id} -->\n')
    if not target_id in locsDefined[link_id]:
        locsDefined[link_id].add(target_id)
        lines.append(f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{target_id}" xlink:label="{target_id}" xlink:title="{target_id}"/>\n')
    count += 1
    arc_id = f'{link_id} {target_id}'
    if not arc_id in arcsDefined[link_id]:
        arcsDefined[link_id].add(arc_id)
        lines.append(f'\t\t<link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/domain-member" xbrldt:targetRole="http://www.xbrl.jp/audit-data-collection/role{URI}" xlink:from="{link_id}" xlink:to="{target_id}" xlink:title="domain-member: {link_id} to {target_id} in {role_id}" order="{count}"/>\n')
    if DEBUG:
        print(f'domain-member: {link_id} to {target_id} order={count} targetRole=http://www.xbrl.jp/audit-data-collection/role{URI} ')

def domain_children(adc_id, link_id, core_xsd, locsDefined, arcsDefined, lines):
    global count
    node = getRecord(adc_id)
    children = node['children']
    for child_id in children:
        child = getRecord(child_id)
        child_kind = child['kind']
        if child_id in targetRefDict:
            target_role(child_id, link_id, core_xsd, locsDefined, arcsDefined, targetRefDict, lines, count)
        else:
            if 'ASBIE'==child_kind and '1'==child['occMax']:
                domain_children(child_id, link_id, core_xsd, locsDefined, arcsDefined, lines, count)
            else:
                domain_member(child_id, link_id, core_xsd, locsDefined, arcsDefined, lines, count)

def defineHypercube(adc_id, role,n):
    global lines
    global locsDefined
    global arcsDefined
    global targetRefDict
    global referenceDict
    global count
    root_id = None
    root_id = adc_id
    root = getRecord(root_id)
    if not root:
        print(f'** {root_id} is not defined.')
        return None
    link_id = role['link_id']
    locsDefined[link_id] = set()
    arcsDefined[link_id] = set()
    URI = role['URI']
    role_id = role['role_id']
    hypercube_id = f"h_{link_id}"
    dimension_id_list = set()
    source_id = None
    if not '-' in adc_id:
        dimensions = root['parent']+[root_id]
        for dim in dimensions:
            dimension = f"d_{dim}"
            dimension_id_list.add(dimension)
    else:
        root_id = link_id[1+link_id.find('-'):]
        root_dimension_id = f'd_{root_id}'
        dimension_id_list.add(root_dimension_id)
        root = getRecord(root_id)
        source_id = link_id[:link_id.find('-')]
        source_dimension = f'd_{source_id}'
        dimension_id_list.add(source_dimension)
    lines.append(f'\t<link:definitionLink xlink:type="extended" xlink:role="http://www.xbrl.jp/audit-data-collection/role{URI}">\n')
    # all (has-hypercube)
    lines.append(f'\t\t<!-- {link_id} all (has-hypercube) {hypercube_id} {role_id} -->\n')
    lines.append(f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{link_id}" xlink:label="{link_id}" xlink:title="{link_id}"/>\n')
    lines.append(f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{hypercube_id}" xlink:label="{hypercube_id}" xlink:title="{hypercube_id}"/>\n')
    lines.append(f'\t\t<link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/all" xlink:from="{link_id}" xlink:to="{hypercube_id}" xlink:title="all (has-hypercube): {link_id} to {hypercube_id}" order="1" xbrldt:closed="true" xbrldt:contextElement="segment"/>\n')
    if DEBUG:
        print(f'all(has-hypercube) {link_id} to {hypercube_id} ')
    # hypercube-dimension
    lines.append('\t\t<!-- hypercube-dimension -->\n')
    count = 0
    for dimension_id in dimension_id_list:
        lines.append(f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{dimension_id}" xlink:label="{dimension_id}" xlink:title="{dimension_id}"/>\n')
        count += 1
        lines.append(f'\t\t<link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/hypercube-dimension" xlink:from="{hypercube_id}" xlink:to="{dimension_id}" xlink:title="hypercube-dimension: {hypercube_id} to {dimension_id}" order="{count}"/>\n')
        if DEBUG:
            print(f'hypercube-dimension {hypercube_id} to {dimension_id} ')
    # domain-member
    lines.append('\t\t<!-- domain-member -->\n')
    count = 0
    if 'children' in root and len(root['children']) > 0:
        children =  root['children']
        for child_id in children:
            child = getRecord(child_id)#[-8:])
            child_kind = child['kind']
            if child_id in targetRefDict:
                target_role(child_id, link_id, core_xsd, locsDefined, arcsDefined, targetRefDict, lines)
            else:
                if 'ASBIE'==child_kind and '1'==child['occMax']:
                    domain_children(child_id, link_id, core_xsd, locsDefined, arcsDefined, lines)
                else:
                    domain_member(child_id, link_id, core_xsd, locsDefined, arcsDefined, lines)

    lines.append('\t</link:definitionLink>\n')

def addChild(parent_id_list,adc_id):
    record = getRecord(adc_id)
    if not record:
        return
    parent = getParent(parent_id_list)
    if not parent:
        return
    if not adc_id in adcDict:
        print(adc_id)
    if not 'children' in parent:
        parent['children'] = []
    if not adc_id in parent['children']:
        parent['children'].append(adc_id)
    if DEBUG:
        print(f'   {parent_id_list} add {adc_id}')
    return adc_id

def addChildren(parent_id_list,adc_id):
    global targetRefDict
    global referenceDict
    record = getRecord(adc_id)
    if not record:
        return
    kind = record['kind']
    ref_id = None
    targetRef_id = None
    if kind in ['IDBIE','BBIE']:
        if DEBUG: print(f'(a) addChild( {parent_id_list}, {adc_id} )[{kind}]{getDEN(adc_id)}({adc_id})')
        addChild(parent_id_list,adc_id)
    elif 'RFBIE'==kind:
        if DEBUG: print(f'(a) addChild( {parent_id_list}, {adc_id} )[{kind}]{getDEN(adc_id)}({adc_id})')
        addChild(parent_id_list,adc_id)
    elif 'ABIE'==kind:
        if adc_id in associationDict:
            ref_id = associationDict[adc_id]
            if DEBUG: print(f'(b) addChild ( {parent_id_list}, {adc_id} )<{kind}>{getDEN(ref_id)}({ref_id})')
        elif adc_id in targetRefDict:
            targetRef_id =  targetRefDict[adc_id]
            if DEBUG: print(f'(c) addChild ( {parent_id_list}, {adc_id} )<{kind}>{getDEN(targetRef_id)}({targetRef_id})')
    elif 'ASBIE'==kind:# and 'n'==record['occMax']:
        record2 = None
        if adc_id in associationDict:
            ref_id = associationDict[adc_id]
            record2 = getRecord(ref_id)
            if DEBUG: print(f'(c) addChild( {parent_id_list}, {adc_id} )<{kind}>{getDEN(ref_id)}({ref_id})')
            addChild(parent_id_list,adc_id)
            parent_id_list += [adc_id]
        elif adc_id in targetRefDict:
            targetRef_id = targetRefDict[adc_id]
            record2 = getRecord(targetRef_id)
            if DEBUG: print(f'(c) addChild( {parent_id_list}, {adc_id} )<{kind}>{getDEN(targetRef_id)}({targetRef_id})')
            addChild(parent_id_list,adc_id)
            parent_id_list += [adc_id]
        else:
            associatedClass = record['associatedClass']
            for adc2_id,record2 in adcDict.items():
                if associatedClass==record2['class']:
                    targetRefDict[adc_id] = adc2_id
                    targetRef_id = adc2_id
                    addChild(parent_id_list,adc_id)
                    break
        if not record2 or not 'children' in record2:
            print(f'-ERROR- addChildren [{kind}] {adc_id}')
        children = record2['children']
        children0 = [x for x in children]
        for child_id in children0:
            child = getRecord(child_id)
            child_kind = child['kind']
            if 'ABIE'==child_kind:
                if DEBUG: print(f'(d) NOT ( {parent_id_list}, {child_id} )<{child_kind}>{getDEN(child_id)}({child_id})')
            if 'ASBIE'==child_kind:# and 'n'==child['occMax']:
                if DEBUG: print(f'(e)*addChildren( {parent_id_list}, {child_id} )<{child_kind}>{getDEN(child_id)}({child_id})')
                addChildren(parent_id_list,child_id)
            else:
                if not adc_id in parent_id_list: parent_id_list += [adc_id]
                if DEBUG: print(f'(f) addChild( {parent_id_list}, {child_id} )[{child_kind}]{getDEN(child_id)}({child_id})')
                addChild(parent_id_list,child_id)
    parent_id_list.pop()
    return adc_id

if __name__ == '__main__':
    # Create the parser
    parser = argparse.ArgumentParser(prog='ADCS_H2xBRL-taxonomy.py',
                                     usage='%(prog)s infile -o outfile -e encoding [options] ',
                                     description='Audit data collection 定義CSVファイルをxBRLタクソノミに変換')
    # Add the arguments
    parser.add_argument('inFile', metavar='infile', type=str, help='Audit data collection 定義CSVファイル')
    parser.add_argument('-o', '--outfile')  # core.xsd
    parser.add_argument('-e', '--encoding') # 'Shift_JIS' 'cp932' 'utf-8-sig'
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-d', '--debug', action='store_true')

    args = parser.parse_args()
    in_file = None
    if args.inFile:
        in_file = args.inFile.strip()
        in_file = in_file.replace('/', SEP)
        in_file = file_path(args.inFile)
    if not in_file or not os.path.isfile(in_file):
        print('入力ADC定義CSVファイルがありません')
        sys.exit()
    adc_file = in_file
    if args.outfile:
        out_file = args.outfile.lstrip()
        out_file = out_file.replace('/', SEP)
        out_file = file_path(out_file)
        xbrl_base = os.path.dirname(out_file)
    xbrl_base = xbrl_base.replace('/', SEP)
    if not os.path.isdir(xbrl_base):
        print('タクソノミのディレクトリがありません')
        sys.exit()

    ncdng = args.encoding
    if ncdng:
        ncdng = ncdng.lstrip()
    else:
        ncdng = 'utf-8-sig'
    VERBOSE = args.verbose
    DEBUG = args.debug

    # ====================================================================
    # 1. audit_data_collection.csv -> schema
    def lookupModule(table_id):
        module = None
        prefix = table_id[:2]
        if 'BS'==prefix: module = 'Base'
        if 'GL'==prefix: module = 'GL'
        if 'CM'==prefix: module = 'Common'
        return module

    records = []
    adc_file = file_path(adc_file)
    parentIDs = []
    classDict = {}
    header = ['no','module','table_id','field_id','kind','level','occurrence','class','propertyTerm','representation','associatedClass','referencedClass','datatype','tag','desc','refClass','refProperty']
    with open(adc_file, encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f)#, delimiter='\t')
        next(reader)
        for cols in reader:
            record = {}
            for i in range(len(cols)):
                col = cols[i]
                record[header[i]] = col.strip()
            if not record['module']:
                continue
            kind = record['kind']
            if 'ABIE'==kind:
                module = record['module']
                cls = record['class']
                table_id = record['table_id']
                classDict[table_id] = cls
            elif 'ASBIE'==kind:
                cls = record['associatedClass']
                table_id = record['field_id']
                classDict[table_id] = cls

    with open(adc_file, encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f)#, delimiter='\t')
        next(reader)
        this_class = None
        this_table_id = None
        for cols in reader:
            record = {}
            for i in range(len(cols)):
                col = cols[i]
                record[header[i]] = col.strip()
            # if not record['module']:
            #     continue
            # if not record['table_id'] in targetTables:
            #     continue
            adc_id = ''
            name = ''
            type = ''
            kind = record['kind']
            cls = record['class']
            occurrence = record['occurrence']
            record['occMin'] = occurrence[0]
            record['occMax'] = occurrence[-1]
            if len(kind) > 5 and 'IDBIE' == kind[:5]:
                kind = 'IDBIE'
            record['kind'] = kind
            level = record['level']
            if re.match('[0-9]+',level):
                level = int(level)
            else:
                level = 0
            record['level'] = level
            table_id = record['table_id']
            if 'ABIE'==kind:
                adc_id = table_id
            else:
                field_id = record['field_id']
                if re.match('[0-9]+',field_id):
                    adc_id = f'{table_id}-{field_id.zfill(2)}'
                else:
                    adc_id = f'{table_id}-{field_id}'
            if kind == 'ABIE':
                record['parent'] = []
                parentIDs = [adc_id]
            else:
                record['parent'] = parentIDs
            record['children'] = []
            record['adc_id'] = adc_id
            if 'ABIE'==kind:
                DEN = f'{cls}. Details'
                record['DEN'] = DEN
                if adc_id in adcDict:
                    if DEBUG: print(f'** Duplicate {adc_id} is already in adcDict.')
                    continue
                record['name'] = cls
                record['type'] = ''
                adcDict[adc_id] = record
                this_class = cls
                this_table_id = table_id
            else:
                propertyTerm = record['propertyTerm']
                if 'ASBIE'==kind:
                    associatedClass = record['associatedClass']
                    DEN = f'{cls}. {propertyTerm}. {associatedClass}'
                elif 'RFBIE'==kind:
                    associatedClass = record['referencedClass']
                    DEN = f'{cls}. {propertyTerm}. {associatedClass}'
                else:
                    representation = record['representation']
                    DEN = f'{cls}. {propertyTerm}. {representation}'
                record['DEN'] = DEN
                if level > 0:
                    parent_id = parentIDs[level-2]
                else:
                    parent_id = ''
                if 'ASBIE'==kind:
                    record['name'] = associatedClass
                elif 'RFBIE'==kind:
                    record['name'] = re.sub('\. ',' ',DEN)
                else:
                    class_name_words = cls.split()
                    property_name_words = propertyTerm.split()                    
                    for word in class_name_words:
                        if word not in property_name_words:
                            property_name_words.insert(0, word)                    
                    combined_name = " ".join(property_name_words)
                    record['name'] = combined_name
                    # if cls not in propertyTerm:
                    #     record['name'] = f"{cls} {propertyTerm}"
                    # else:
                    #     index = propertyTerm.index(cls) + len(cls)
                    #     record['name'] = f"{propertyTerm[:index]} {propertyTerm[index:].strip()}"
                datatype = record['representation']
                if datatype in datatypeMap:
                    type = datatypeMap[datatype]['adc']
                else:
                    type = 'stringItemType'
                record['type'] = type
                if not adc_id in adcDict[parent_id]['children']:
                    adcDict[parent_id]['children'].append(adc_id)
                    if 9==len(parent_id):
                        parent_id2 = parent_id[-4:]
                        if 0==len(adcDict[parent_id2]['parent']):
                            adcDict[parent_id2]['parent'] = parentIDs[:level-1]
                        if not adc_id in adcDict[parent_id2]['children']:
                            adcDict[parent_id2]['children'].append(adc_id)
                adcDict[adc_id] = record
                if 'ASBIE' == kind:
                    while len(parentIDs) > level-1:
                        parentIDs.pop()
                    while len(parentIDs) <= level-1:
                        parentIDs.append('')
                    parentIDs[level-1] = adc_id[1+adc_id.find('-'):]
            records.append(record)
            if 'ASBIE' == kind and len(adc_id) > 8:
                d = {}
                for i in range(len(cols)):
                    col = cols[i]
                    d[header[i]] = ''
                table_id = adc_id[1+adc_id.find('-'):]
                d['no'] = record['no']
                d['module'] = lookupModule(table_id)
                d['kind'] = 'ABIE'
                d['adc_id'] = table_id
                d['table_id'] = table_id
                d['class'] = classDict[table_id]
                d['field_id'] = '0'
                d['occurrence'] = '--'
                d['occMin'] = '-'
                d['occMax'] = '-'
                d['parent'] = parentIDs[:-1]
                d['children'] = []
                d['name'] = d['class']
                d['DEN'] = f'{d["name"]}. Details'
                adcDict[table_id] = d
                records.append(d)

    targetRefDict = {}
    associationDict = {}
    for adc_id, record in adcDict.items():
        kind = record['kind']
        if 'ASBIE'==kind:
            if 'n' == record['occMax']:
                targetRefDict[adc_id] = adc_id[1+adc_id.find('-'):]
            else:
                referenceDict[adc_id] = adc_id[1+adc_id.find('-'):]

    roleMap = {}

    for adc_id,record in adcDict.items():
        den = getLC3_DEN(adc_id)
        if 'ABIE'==record['kind'] and not adc_id in roleMap:
            link_id = adc_id
            den = getLC3_DEN(link_id)
            role_id = f'link_{link_id}'
            URI = f'/{role_id}'
            roleMap[link_id] = {'adc_id':link_id,'link_id':link_id,'URI':URI,'role_id':role_id,'den':den}

    ###################################
    # core.xsd
    #
    def get_element_datatype(adc_id,type,kind):
        if not type:
            type = 'xbrli:stringItemType'
            if DEBUG: print(f'{adc_id} [{kind}] type not defined.')
        elif not 'xbrli:' in type and not 'adc:'in type:
            if not type:
                type = 'xbrli:stringItemType'
                if DEBUG: print(f'{adc_id} [{kind}] type not defined.')
            else:
                type=F'adc:{type}'
        return type

    def defineElement(adc_id,record):
        global lines
        global elementsDefined
        if not adc_id in elementsDefined:
            elementsDefined.add(adc_id)
            if not record:
                print(f'NOT DEFINED {adc_id} record')
                return
            kind = record['kind']
            if 'ABIE'==kind or adc_id in targetRefDict or adc_id in referenceDict:
                line = f'\t\t<element name="{adc_id}" id="{adc_id}" abstract="true" type="xbrli:stringItemType" nillable="true" substitutionGroup="xbrli:item" xbrli:periodType="instant"/>\n'
            else:
                type = record['type']
                type = get_element_datatype(adc_id,type,kind)
                line = f'\t\t<element name="{adc_id}" id="{adc_id}" type="{type}" nillable="false" substitutionGroup="xbrli:item" xbrli:periodType="instant"/>\n'
            lines.append(line)

    def lookupPrimarykey(link_id):
        source_id = link_id[:4]
        adc_id = link_id[5:]
        children = [record for record in records if adc_id==record['adc_id'][:4]]
        for child in children:
            child_kind = child['kind']
            child_id = child['adc_id']
            child_id =f'{source_id}-{child_id}'
            defineElement(child_id,child)
            if 'IDBIE'==child_kind:
                primaryKeys[link_id] = child_id
        if link_id in primaryKeys:
            return primaryKeys[link_id]
        return None

    html_head = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<!-- (c) 2022 XBRL Japan  inc. -->\n',
        '<schema \n',
        '\ttargetNamespace="http://www.xbrl.jp/audit-data-collection" \n',
        '\telementFormDefault="qualified" \n',
        '\txmlns="http://www.w3.org/2001/XMLSchema" \n',
        '\txmlns:adc="http://www.xbrl.jp/audit-data-collection" \n',
        '\txmlns:xlink="http://www.w3.org/1999/xlink" \n',
        '\txmlns:link="http://www.xbrl.org/2003/linkbase" \n',
        '\txmlns:xbrli="http://www.xbrl.org/2003/instance" \n',
        '\txmlns:xbrldt="http://xbrl.org/2005/xbrldt"> \n',
        '\t<import namespace="http://www.xbrl.org/2003/instance" schemaLocation="http://www.xbrl.org/2003/xbrl-instance-2003-12-31.xsd"/>\n',
        '\t<import namespace="http://xbrl.org/2005/xbrldt" schemaLocation="http://www.xbrl.org/2005/xbrldt-2005.xsd"/>\n',
        '\t<import namespace="http://www.xbrl.org/dtr/type/numeric" schemaLocation="http://www.xbrl.org/dtr/type/numeric-2009-12-16.xsd"/>\n',
        '\t<import namespace="http://www.xbrl.org/dtr/type/non-numeric" schemaLocation="http://www.xbrl.org/dtr/type/nonNumeric-2009-12-16.xsd"/>\n']
    lines = html_head
    html_annotation_head = [
        '\t<annotation>\n',
        '\t\t<appinfo>\n',
        '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:role="http://www.xbrl.org/2003/role/labelLinkbaseRef" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-lbl-en.xml"/>\n',
        '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:role="http://www.xbrl.org/2003/role/presentationLinkbaseRef" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-pre.xml"/>\n',
        '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:role="http://www.xbrl.org/2003/role/definitionLinkbaseRef" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-def.xml"/>\n',
        # '\t\t\t<!-- formula -->\n',
        # '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Mandatory-Base.xml"/> \n',
        # '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Mandatory-GL.xml"/> \n',
        # '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Mandatory-O2C.xml"/> \n',
        # '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Mandatory-P2P.xml"/> \n',
        # '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Mandatory-Core.xml"/> \n',
        # '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Card-Base.xml"/> \n',
        # '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Card-GL.xml"/> \n',
        # '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Card-O2C.xml"/> \n',
        # '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Card-P2P.xml"/> \n',
        # '\t\t\t<link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Card-Core.xml"/> \n',
    ]
    lines += html_annotation_head
    html = [
        '\t\t\t<!-- \n',
        '\t\t\t\trole type\n',
        '\t\t\t-->\n'
        f'\t\t\t<link:roleType id="audit-data-collection-role" roleURI="http://www.xbrl.jp/audit-data-collection/role">\n',
        f'\t\t\t\t<link:definition>link audit-data-collection</link:definition>\n',
        f'\t\t\t\t<link:usedOn>link:definitionLink</link:usedOn>\n',
        f'\t\t\t\t<link:usedOn>link:presentationLink</link:usedOn>\n',
        '\t\t\t</link:roleType>\n',
    ]
    for adc_id,role in roleMap.items():
        role_id = role["role_id"]
        URI = role['URI']
        link_id = role['link_id']
        den = role["den"]
        if 4==len(adc_id):
            html.append(f'\t\t\t<link:roleType id="{role_id}" roleURI="http://www.xbrl.jp/audit-data-collection/role{URI}">\n')
            html.append(f'\t\t\t\t<link:definition>{den}</link:definition>\n')
            html.append(f'\t\t\t\t<link:usedOn>link:definitionLink</link:usedOn>\n')
            html.append('\t\t\t</link:roleType>\n')
        else:
            source_den = den[:den.index('-')]
            target_den = den[den.index('-')+1:]
            html.append(f'\t\t\t<link:roleType id="{role_id}" roleURI="http://www.xbrl.jp/audit-data-collection/role{URI}">\n')
            html.append(f'\t\t\t\t<link:definition>{source_den} to {target_den}</link:definition>\n')
            html.append(f'\t\t\t\t<link:usedOn>link:definitionLink</link:usedOn>\n')
            html.append('\t\t\t</link:roleType>\n')
    lines += html

    html = [
        '\t\t\t<!--\n',
        '\t\t\t\tdescription: roleType arcroleType\n',
        '\t\t\t-->\n'
        '\t\t\t<link:roleType id="description" roleURI="http://www.xbrl.jp/audit-data-collection/role/description">\n',
        '\t\t\t\t<link:definition>description</link:definition>\n',
        '\t\t\t\t<link:usedOn>link:label</link:usedOn>\n',
        '\t\t\t</link:roleType>\n',
        '\t\t\t<link:arcroleType id="concept-description" cyclesAllowed="undirected" arcroleURI="http://www.xbrl.jp/audit-data-collection/arcrole/concept-description">\n',
        '\t\t\t\t<link:definition>concept to description</link:definition>\n',
        '\t\t\t\t<link:usedOn>link:labelArc</link:usedOn>\n',
        '\t\t\t</link:arcroleType >\n',
    ]
    lines += html

    html = [
        '\t\t\t<!--\n',
        '				primary key: roleType arcroleType\n',
        '\t\t\t-->\n'
        '\t\t\t<link:roleType id="primary-key" roleURI="http://www.xbrl.jp/audit-data-collection/role/primary-key">\n',
        '\t\t\t\t<link:definition>primary key</link:definition>\n',
        '\t\t\t\t<link:usedOn>link:definitionLink</link:usedOn>\n',
        '\t\t\t</link:roleType>\n',
        '\t\t\t<link:arcroleType id="concept-primary-key" cyclesAllowed="undirected" arcroleURI="http://www.xbrl.jp/audit-data-collection/arcrole/concept-primary-key">\n',
        '\t\t\t\t<link:definition>concept primary key</link:definition>\n',
        '\t\t\t\t<link:usedOn>link:definitionArc</link:usedOn>\n',
        '\t\t\t</link:arcroleType >\n',
    ]
    lines += html

    html = [
        '\t\t\t<!--\n',
        '\t\t\t\treference identifier: roleType arcroleType\n',
        '\t\t\t-->\n'
        '\t\t\t<link:roleType id="reference-identifier" roleURI="http://www.xbrl.jp/audit-data-collection/role/reference-identifier">\n',
        '\t\t\t\t<link:definition>reference identifier</link:definition>\n',
        '\t\t\t\t<link:usedOn>link:definitionLink</link:usedOn>\n',
        '\t\t\t</link:roleType>\n',
        '\t\t\t<link:arcroleType id="concept-reference-identifier" cyclesAllowed="undirected" arcroleURI="http://www.xbrl.jp/audit-data-collection/arcrole/concept-reference-identifier">\n',
        '\t\t\t\t<link:definition>concept reference identifier</link:definition>\n',
        '\t\t\t\t<link:usedOn>link:definitionArc</link:usedOn>\n',
        '\t\t\t</link:arcroleType >\n',
    ]
    lines += html

    html = [
        '\t\t\t<!--\n',
        '\t\t\t\trequire: roleType\n',
        '\t\t\t-->\n'
        '\t\t\t<link:roleType id="require" roleURI="http://www.xbrl.jp/audit-data-collection/role/require">\n',
        '\t\t\t\t<link:definition>require</link:definition>\n',
        '\t\t\t\t<link:usedOn>link:definitionLink</link:usedOn>\n',
        '\t\t\t</link:roleType>\n',
    ]
    lines += html

    html_annotation_tail = [
        '\t\t</appinfo>\n',
        '\t</annotation>\n'
    ]
    lines += html_annotation_tail

    html_type = [
        '\t<!-- typed dimension referenced element -->\n',
        '\t<element name="_v" id="_v">\n',
        '\t\t<simpleType>\n',
        '\t\t\t<restriction base="string"/>\n',
        '\t\t</simpleType>\n',
        '\t</element>\n',
        '\t<element name="_activity" id="_activity">',
        '\t\t<simpleType>',
        '\t\t\t<restriction base="string">',
        '\t\t\t\t<pattern value="\s*(Created|Approved|LastModified|Entered|Posted)\s*"/>',
        '\t\t\t</restriction>',
        '\t\t</simpleType>',
        '\t</element>'
    ]
    lines += html_type

    html_hypercube = [
        '\t<!-- Hypercube -->\n'
    ]
    # Hypercube
    for adc_id,role in roleMap.items():
        link_id = role['link_id']
        html_hypercube.append(f'\t<element name="h_{link_id}" id="h_{link_id}" substitutionGroup="xbrldt:hypercubeItem" type="xbrli:stringItemType" nillable="true" abstract="true" xbrli:periodType="instant"/>\n')
    lines += html_hypercube

    html_dimension = [
        '\t<!-- Dimension -->\n'
    ]
    # Dimension
    for adc_id,role in roleMap.items():
        link_id = role['link_id']
        html_dimension.append(f'\t<element name="d_{link_id}" id="d_{link_id}" substitutionGroup="xbrldt:dimensionItem" type="xbrli:stringItemType" abstract="true" xbrli:periodType="instant" xbrldt:typedDomainRef="#_v"/>\n')
    lines += html_dimension

    html_itemtype = [
        '\t<!-- item type -->\n'
    ]
    # complexType
    complexType = [
        '\t\t<complexType name="stringItemType">\n',
        '\t\t\t<simpleContent>\n',
        '\t\t\t\t<restriction base="xbrli:stringItemType"/>\n',
        '\t\t\t</simpleContent>\n',
        '\t\t</complexType>\n',
    ]
    html_itemtype += complexType
    for name,type in datatypeMap.items():
        adc = type['adc']
        xbrli = type['xbrli']
        complexType = [
            f'\t\t<complexType name="{adc}">\n',
            '\t\t\t<simpleContent>\n',
            f'\t\t\t\t<restriction base="xbrli:{xbrli}"/>\n',
            '\t\t\t</simpleContent>\n',
            '\t\t</complexType>\n',
        ]
        html_itemtype += complexType
    lines += html_itemtype
    # element
    lines.append('\t<!-- element -->\n')
    elementsDefined = set()
    primaryKeys = {}
    for record in adcDict.values():
        adc_id = record['adc_id']
        kind = record['kind']
        referenced_id = None
        defineElement(adc_id,record)
        if 'IDBIE'==kind:
            primaryKeys[adc_id[:4]] = adc_id

    for link_id,role in roleMap.items():
        if 4==len(link_id):
            continue
        adc_id = link_id[5:]
        record = getRecord(adc_id)
        defineElement(link_id,record)
        lookupPrimarykey(link_id)

    lines.append('</schema>')

    adc_xsd_file = file_path(f'{xbrl_base}{core_xsd}')
    with open(adc_xsd_file, 'w', encoding='utf_8', newline='') as f:
        f.writelines(lines)
    if VERBOSE:
        print(f'-- {adc_xsd_file}')

    ###################################
    # labelLink en
    #
    def linkLabel(adc_id,name,Desc):
        global locsDefined
        global definedLabels
        global arcsDefined
        global definedDescs
        global definedDescArcs
        if ''==name:
            record = getRecord(adc_id)
            if 'ASBIE'==record['kind']:
                target_id = adc_id[1+adc_id.find('-'):]
                target = getRecord(target_id)
                name = target['name']
        lines.append(f'\t\t<!-- {adc_id} {name} -->\n')
        if not adc_id in locsDefined:
            locsDefined[adc_id] = adc_id
            line = f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{adc_id}" xlink:label="{adc_id}" xlink:title="{adc_id}"/>\n'
        else:
            line = f'\t\t\t<!-- link:loc defined -->\n'
        lines.append(line)
        # name
        if not adc_id in definedLabels:
            definedLabels[adc_id] = adc_id
            line = f'\t\t<link:label xlink:type="resource" xlink:label="label_{adc_id}" xlink:title="label_{adc_id}" id="label_{adc_id}" xml:lang="en" xlink:role="http://www.xbrl.org/2003/role/label">{name}</link:label>\n'
        else:
            line = f'\t\t\t<!-- link:label http://www.xbrl.org/2003/role/label defined -->\n'
        lines.append(line)
        if not adc_id in arcsDefined:
            arcsDefined[adc_id] = adc_id
            line = f'\t\t<link:labelArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/concept-label" xlink:from="{adc_id}" xlink:to="label_{adc_id}" xlink:title="label: {adc_id} to label_{adc_id}"/>\n'
        else:
            line = f'\t\t\t<!-- link:labelArc http://www.xbrl.org/2003/arcrole/concept-label defined -->\n'
        lines.append(line)
        # Desc
        if name != Desc:
            if not adc_id in definedDescs:
                definedDescs[adc_id] = adc_id
                line = f'\t\t<link:label xlink:type="resource" xlink:label="description_{adc_id}" xlink:title="description_{adc_id}" id="description_{adc_id}" xml:lang="en" xlink:role="http://www.xbrl.jp/audit-data-collection/role/description">{Desc}</link:label>\n'
            else:
                line = f'\t\t\t<!-- link:label http://www.xbrl.jp/audit-data-collection/role/description defined -->\n'
            lines.append(line)
            if not adc_id in definedDescArcs:
                definedDescArcs[adc_id] = adc_id
                line = f'\t\t<link:labelArc xlink:type="arc" xlink:arcrole="http://www.xbrl.jp/audit-data-collection/arcrole/concept-description" xlink:from="{adc_id}" xlink:to="description_{adc_id}" xlink:title="label: {adc_id} to label_{adc_id}"/>\n'
            else:
                line = f'\t\t\t<!-- link:labelArc http://www.xbrl.jp/audit-data-collection/arcrole/concept-description defined -->\n'
            lines.append(line)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<!--  (c) 2022 XBRL Japan inc. -->\n',
        '<link:linkbase\n',
        '\txmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n',
        '\txmlns:link="http://www.xbrl.org/2003/linkbase"\n',
        '\txmlns:xlink="http://www.w3.org/1999/xlink"\n',
        '\txsi:schemaLocation="http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd">\n',
        f'\t<link:roleRef roleURI="http://www.xbrl.jp/audit-data-collection/role/description" xlink:type="simple" xlink:href="{core_xsd}#description"/>\n',
        f'\t<link:arcroleRef arcroleURI="http://www.xbrl.jp/audit-data-collection/arcrole/concept-description" xlink:type="simple" xlink:href="{core_xsd}#concept-description"/>\n',
        '\t<link:labelLink xlink:type="extended" xlink:role="http://www.xbrl.org/2003/role/link">\n'
    ]
    locsDefined = {}
    arcsDefined = {}
    definedLabels = {}
    definedDescs = {}
    definedDescArcs = {}
    for record in adcDict.values():
        adc_id = record['adc_id']
        kind = record['kind']
        name = record['name']
        Desc = record['desc']
        linkLabel(adc_id,name,Desc)

    lines.append('\t</link:labelLink>\n')
    lines.append('</link:linkbase>\n')

    adc_label_file = file_path(f'{xbrl_base}{core_label}-en.xml')
    with open(adc_label_file, 'w', encoding='utf_8', newline='') as f:
        f.writelines(lines)
    if VERBOSE:
        print(f'-- {adc_label_file}')

    ###################################
    #   presentationLink
    #
    locsDefined = {}
    arcsDefined = {}
    def linkPresentation(adc_id,children,n):
        global lines
        global count
        global locsDefined
        global arcsDefined
        if not adc_id:
            return
        record = getRecord(adc_id)
        if not record:
            return
        if 'ASBIE'==record['kind']:
            target_id = adc_id[1+adc_id.find('-'):]
            record = getRecord(target_id)
        name = record['name']
        if not adc_id in locsDefined:
            locsDefined[adc_id] = name
            lines.append(f'\t\t<!-- {kind} {adc_id} {name} -->\n')
            lines.append(f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{adc_id}" xlink:label="{adc_id}" xlink:title="presentation: {adc_id} {name}"/>\n')
        for child_id in children:
            child = getRecord(child_id)
            child_kind = child['kind']
            child_name = child['name']
            level = child['level']
            if level != n:
                continue
            if 'ASBIE'==child_kind:
                if not child_id in locsDefined:
                    locsDefined[child_id] = child_name
                    lines.append(f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{child_id}" xlink:label="{child_id}" xlink:title="presentation parent: {child_id} {child_name}"/>\n')
                arc_id = F'{adc_id} {child_id}'
                if not arc_id in arcsDefined and adc_id!=child_id:
                    arcsDefined[arc_id] = f'{name} to {child_name}'
                    count += 1
                    lines.append(f'\t\t<link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="{adc_id}" xlink:to="{child_id}" order="{count}" xlink:title="presentation: {adc_id} {name} to {child_id} {child_name}"/>\n')
                if DEBUG:
                    print(f'presentation: {adc_id} {name} to {child_id} {child_name} order={count}')
                if 'children' in child and len(child['children']) > 0:
                    grand_children = child['children']
                    linkPresentation(child_id,grand_children,n+1)
                else:
                    target_id =  child_id[1+child_id.find('-'):]
                    target = getRecord(target_id)
                    if 'children' in target and len(target['children']) > 0:
                        grand_children = target['children']
                        linkPresentation(child_id,grand_children,n+1)                    
            else:
                if not child_id in locsDefined:
                    locsDefined[child_id] = child_name
                    lines.append(f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{child_id}" xlink:label="{child_id}" xlink:title="presentation parent: {child_id} {child_name}"/>\n')
                arc_id = F'{adc_id} {child_id}'
                if not arc_id in arcsDefined and adc_id!=child_id:
                    arcsDefined[arc_id] = f'{name} to {child_name}'
                    count += 1
                    lines.append(f'\t\t<link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="{adc_id}" xlink:to="{child_id}" order="{count}" xlink:title="presentation: {adc_id} {name} to {child_id} {child_name}"/>\n')
                    if DEBUG:
                        print(f'presentation: {adc_id} {name} to {child_id} {child_name} order={count}')
                if 'children' in child and len(child['children']) > 0:
                    grand_children = child['children']
                    linkPresentation(child_id,grand_children,n+1)
        children = None
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<!--  (c) 2022 XBRL Japan inc. -->\n',
        '<link:linkbase\n',
        '\txmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n',
        '\txsi:schemaLocation="http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd"\n',
        '\txmlns:link="http://www.xbrl.org/2003/linkbase"\n',
        '\txmlns:xlink="http://www.w3.org/1999/xlink">\n',
        f'\t<link:roleRef roleURI="http://www.xbrl.jp/audit-data-collection/role" xlink:type="simple" xlink:href="{core_xsd}#audit-data-collection-role"/>\n',
        '\t<link:presentationLink xlink:type="extended" xlink:role="http://www.xbrl.jp/audit-data-collection/role">\n',
    ]
    locsDefined = {}
    arcsDefined = {}
    abies = [x for x in records if 'ABIE'==x['kind']]
    for record in abies:
        adc_id = record['adc_id']
        kind = record['kind']
        count = 0
        children = record['children']
        linkPresentation(adc_id,children,2)

    lines.append('\t</link:presentationLink>\n')
    lines.append('</link:linkbase>\n')

    adc_presentation_file = file_path(f'{xbrl_base}{core_presentation}.xml')
    with open(adc_presentation_file, 'w', encoding='utf_8', newline='') as f:
        f.writelines(lines)
    if VERBOSE:
        print(f'-- {adc_presentation_file}')

    ###################################
    # definitionLink
    #
    locsDefined = {}
    arcsDefined = {}
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<!--(c) 2022 XBRL Japan inc. -->\n',
        '<link:linkbase\n',
        '\txmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n',
        '\txsi:schemaLocation="http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd"\n',
        '\txmlns:link="http://www.xbrl.org/2003/linkbase"\n',
        '\txmlns:xbrldt="http://xbrl.org/2005/xbrldt"\n',
        '\txmlns:xlink="http://www.w3.org/1999/xlink">\n'
    ]
    lines.append('\t<!-- roleRef -->\n')
    for role in roleMap.values():
        role_id = role["role_id"]
        link_id = role['link_id']
        URI = f"/{role_id}"
        lines.append(f'\t<link:roleRef roleURI="http://www.xbrl.jp/audit-data-collection/role{URI}" xlink:type="simple" xlink:href="{core_xsd}#{role_id}"/>\n')
    html = [
        f'\t<link:roleRef roleURI="http://www.xbrl.jp/audit-data-collection/role/primary-key" xlink:type="simple" xlink:href="{core_xsd}#primary-key"/>\n',
        f'\t<link:roleRef roleURI="http://www.xbrl.jp/audit-data-collection/role/reference-identifier" xlink:type="simple" xlink:href="{core_xsd}#reference-identifier"/>\n',
        f'\t<link:roleRef roleURI="http://www.xbrl.jp/audit-data-collection/role/require" xlink:type="simple" xlink:href="{core_xsd}#require"/>\n',
        '\t<!-- arcroleRef -->\n',
        '\t<link:arcroleRef arcroleURI="http://xbrl.org/int/dim/arcrole/all" xlink:type="simple" xlink:href="http://www.xbrl.org/2005/xbrldt-2005.xsd#all"/>\n',
        '\t<link:arcroleRef arcroleURI="http://xbrl.org/int/dim/arcrole/domain-member" xlink:type="simple" xlink:href="http://www.xbrl.org/2005/xbrldt-2005.xsd#domain-member"/>\n',
        '\t<link:arcroleRef arcroleURI="http://xbrl.org/int/dim/arcrole/hypercube-dimension" xlink:type="simple" xlink:href="http://www.xbrl.org/2005/xbrldt-2005.xsd#hypercube-dimension"/>\n',
        '\t<link:arcroleRef arcroleURI="http://xbrl.org/int/dim/arcrole/dimension-domain" xlink:type="simple" xlink:href="http://www.xbrl.org/2005/xbrldt-2005.xsd#dimension-domain"/>\n',
        f'\t<link:arcroleRef arcroleURI="http://www.xbrl.jp/audit-data-collection/arcrole/concept-primary-key" xlink:type="simple" xlink:href="{core_xsd}#concept-primary-key"/>\n',
        f'\t<link:arcroleRef arcroleURI="http://www.xbrl.jp/audit-data-collection/arcrole/concept-reference-identifier" xlink:type="simple" xlink:href="{core_xsd}#concept-reference-identifier"/>\n',
    ]
    lines += html

    for adc_id,role in roleMap.items():
        defineHypercube(adc_id, role, 2)

    lines.append('</link:linkbase>\n')

    adc_definition_file = file_path(f'{xbrl_base}{core_definition}.xml')
    with open(adc_definition_file, 'w', encoding='utf_8', newline='') as f:
        f.writelines(lines)
    if VERBOSE:
        print(f'-- {adc_definition_file}')

    print('** END **')