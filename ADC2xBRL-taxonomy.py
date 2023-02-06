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
core_head = 'core-head.txt'
primarykey_file = 'primarykey.csv'

xbrl_base = 'taxonomy/'
xbrl_base = xbrl_base.replace('/', SEP)
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

targetTables = ['A51','A52','A75','A81']

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
        den = den[5:den.find('.')]
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
        record = None
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

def defineHypercube(adc_id, role):
    global lines
    global locsDefined
    global arcsDefined
    global targetRefDict
    global referenceDict
    root_id = None
    root_id = adc_id
    root = getRecord(root_id)
    anchor_id = None
    link_id = role['link_id']
    locsDefined[link_id] = set()
    arcsDefined[link_id] = set()
    URI = role['URI']
    role_id = role['role_id']
    hypercube_id = f"h_{link_id}"
    dimension_id_list = set()
    source_id = None
    origin_id = None
    if 4==len(adc_id):
        root_dimension = f"d_{root_id}"
        dimension_id_list.add(root_dimension)
    if 9==len(adc_id):
        root_id = link_id[5:]
        root_dimension_id = f'd_{root_id}'
        dimension_id_list.add(root_dimension_id)
        root = getRecord(root_id)
        source_id = link_id[:4]
        source_dimension = f'd_{source_id}'
        dimension_id_list.add(source_dimension)
        # anchor_id = [x for x in sourceRefDict[root_id]['source'] if source_id==x[:4]][0]
        if source_id in sourceRefDict:
            origin = sourceRefDict[source_id]
            origin_id = origin['source'][0]
            origin_id = origin_id[:4]
            anchor_id = f'{origin_id}-{anchor_id}'
            origin_dimension = f'd_{origin_id}'
            dimension_id_list.add(origin_dimension)
    lines.append(f'    <link:definitionLink xlink:type="extended" xlink:role="http://www.xbrl.jp/audit-data-collection/role{URI}">\n')
    # all (has-hypercube)
    lines.append(f'        <!-- {link_id} all (has-hypercube) {hypercube_id} {role_id} -->\n')
    lines.append(f'        <link:loc xlink:type="locator" xlink:href="{core_xsd}#{link_id}" xlink:label="{link_id}" xlink:title="{link_id}"/>\n')
    lines.append(f'        <link:loc xlink:type="locator" xlink:href="{core_xsd}#{hypercube_id}" xlink:label="{hypercube_id}" xlink:title="{hypercube_id}"/>\n')
    lines.append(f'        <link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/all" xlink:from="{link_id}" xlink:to="{hypercube_id}" xlink:title="all (has-hypercube): {link_id} to {hypercube_id}" order="1" xbrldt:closed="true" xbrldt:contextElement="scenario"/>\n')
    if DEBUG:
        print(f'all(has-hypercube) {link_id} to {hypercube_id} ')
    # hypercube-dimension
    lines.append('        <!-- hypercube-dimension -->\n')
    count = 0
    for dimension_id in dimension_id_list:
        lines.append(f'        <link:loc xlink:type="locator" xlink:href="{core_xsd}#{dimension_id}" xlink:label="{dimension_id}" xlink:title="{dimension_id}"/>\n')
        count += 1
        lines.append(f'        <link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/hypercube-dimension" xlink:from="{hypercube_id}" xlink:to="{dimension_id}" xlink:title="hypercube-dimension: {hypercube_id} to {dimension_id}" order="{count}"/>\n')
        if DEBUG:
            print(f'hypercube-dimension {hypercube_id} to {dimension_id} ')
    # domain-member
    lines.append('        <!-- domain-member -->\n')
    count = 0
    if 'children' in root and len(root['children']) > 0:
        children =  root['children']
        for child_id in children:
            alias_id = not link_id[:4] in child_id and f"{link_id[:4]}-{child_id}" or child_id
            child = getRecord(child_id[-8:])
            child_kind = child['kind']
            if child_id[-8:] in targetRefDict:
                if 'ASBIE'!=child_kind or 'n'!=child['occMax']:
                    if not alias_id in locsDefined[link_id]:
                        locsDefined[link_id].add(alias_id)
                        lines.append(f'        <link:loc xlink:type="locator" xlink:href="{core_xsd}#{alias_id}" xlink:label="{alias_id}" xlink:title="{alias_id}"/>\n')
                    count += 1
                    arc_id = f'{link_id} {alias_id}'
                    if not arc_id in arcsDefined[link_id]:
                        arcsDefined[link_id].add(arc_id)
                        lines.append(f'        <link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/domain-member" xlink:from="{link_id}" xlink:to="{alias_id}" xlink:title="domain-member: {link_id} to {alias_id}" order="{count}"/>\n')
                # targetRole
                target_id = targetRefDict[child_id[-8:]]
                target_id = f'{child_id[:-4]}-{target_id}'
                role_id = f'link_{target_id}'
                URI = f'/{role_id}'
                lines.append(f'        <!-- {child_id} targetRole {role_id} -->\n')
                if not target_id in locsDefined[link_id]:
                    locsDefined[link_id].add(target_id)
                    lines.append(f'        <link:loc xlink:type="locator" xlink:href="{core_xsd}#{target_id}" xlink:label="{target_id}" xlink:title="{target_id}"/>\n')
                count += 1
                arc_id = f'{link_id} {target_id}'
                if not arc_id in arcsDefined[link_id]:
                    arcsDefined[link_id].add(arc_id)
                    lines.append(f'        <link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/domain-member" xbrldt:targetRole="http://www.xbrl.jp/audit-data-collection/role{URI}" xlink:from="{link_id}" xlink:to="{target_id}" xlink:title="domain-member: {link_id} to {target_id} in {role_id}" order="{count}"/>\n')
            else:
                if not alias_id in locsDefined[link_id]:
                    locsDefined[link_id].add(alias_id)
                    lines.append(f'        <link:loc xlink:type="locator" xlink:href="{core_xsd}#{alias_id}" xlink:label="{alias_id}" xlink:title="{alias_id}"/>\n')
                count += 1
                arc_id = f'{link_id} {alias_id}'
                if not arc_id in arcsDefined[link_id]:
                    arcsDefined[link_id].add(arc_id)
                    lines.append(f'        <link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/domain-member" xlink:from="{link_id}" xlink:to="{alias_id}" xlink:title="domain-member: {link_id} to {alias_id}" order="{count}"/>\n')
                if 'ASBIE'==child_kind and '1'==child['occMax']:
                    association_id = associationDict[child_id]
                    association = getRecord(association_id)
                    grand_children = association['children']
                    for grand_child_id in grand_children:
                        grand_alias_id = not link_id[:4] in grand_child_id and f"{link_id[:4]}-{grand_child_id}" or grand_child_id
                        if not grand_alias_id in locsDefined[link_id]:
                            locsDefined[link_id].add(grand_alias_id)
                            lines.append(f'        <link:loc xlink:type="locator" xlink:href="{core_xsd}#{grand_alias_id}" xlink:label="{grand_alias_id}" xlink:title="{grand_alias_id}"/>\n')
                        count += 1
                        arc_id = f'{alias_id} {grand_alias_id}'
                        if not arc_id in arcsDefined[link_id]:
                            arcsDefined[link_id].add(arc_id)
                            lines.append(f'        <link:definitionArc xlink:type="arc" xlink:arcrole="http://xbrl.org/int/dim/arcrole/domain-member" xlink:from="{alias_id}" xlink:to="{grand_alias_id}" xlink:title="domain-member: {alias_id} to {grand_alias_id}" order="{count}"/>\n')                    

    # essence-alias
    if len(link_id) > 4:
        lines.append('        <!-- essence-alias -->\n')
        count = 0
        if 'children' in root and len(root['children']) > 0:
            children =  root['children']
            for child_id in children:
                child = getRecord(child_id[-8:])
                child_kind = child['kind']
                essence_id = child_id
                if essence_id in targetRefDict:
                    continue
                if not essence_id in locsDefined[link_id]:
                    locsDefined[link_id].add(essence_id)
                    lines.append(f'        <link:loc xlink:type="locator" xlink:href="{core_xsd}#{essence_id}" xlink:label="{essence_id}" xlink:title="{essence_id}"/>\n')
                alias_id = f"{link_id[:4]}-{child_id}"
                if not alias_id in locsDefined[link_id]:
                    locsDefined[link_id].add(alias_id)
                    lines.append(f'        <link:loc xlink:type="locator" xlink:href="{core_xsd}#{alias_id}" xlink:label="{alias_id}" xlink:title="{alias_id}"/>\n')
                count += 1
                arc_id = f'{essence_id} {alias_id}'
                if not arc_id in arcsDefined[link_id]:
                    arcsDefined[link_id].add(arc_id)
                    lines.append(f'        <link:definitionArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/essence-alias" xlink:from="{essence_id}" xlink:to="{alias_id}" xlink:title="essence-alias: {essence_id} to {alias_id}" order="{count}"/>\n')
                if 'ASBIE'==child_kind and '1'==child['occMax']:
                    association_id = associationDict[child_id]
                    association = getRecord(association_id)
                    grand_children = association['children']
                    for grand_child_id in grand_children:
                        grand_essence_id = grand_child_id
                        if grand_essence_id in targetRefDict:
                            continue
                        if not grand_essence_id in locsDefined[link_id]:
                            locsDefined[link_id].add(grand_essence_id)
                            lines.append(f'        <link:loc xlink:type="locator" xlink:href="{core_xsd}#{grand_essence_id}" xlink:label="{grand_essence_id}" xlink:title="{grand_essence_id}"/>\n')
                        grand_alias_id = f"{link_id[:4]}-{grand_child_id}"
                        if not grand_alias_id in locsDefined[link_id]:
                            locsDefined[link_id].add(grand_alias_id)
                            lines.append(f'        <link:loc xlink:type="locator" xlink:href="{core_xsd}#{grand_alias_id}" xlink:label="{grand_alias_id}" xlink:title="{grand_alias_id}"/>\n')
                        count += 1
                        arc_id = f'{grand_essence_id} {grand_alias_id}'
                        if not arc_id in arcsDefined[link_id]:
                            arcsDefined[link_id].add(arc_id)
                            lines.append(f'        <link:definitionArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/essence-alias" xlink:from="{grand_essence_id}" xlink:to="{grand_alias_id}" xlink:title="essence-alias: {grand_essence_id} to {grand_alias_id}" order="{count}"/>\n')

    lines.append('    </link:definitionLink>\n')

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
        print(f'   {parent_id_list} + {adc_id}')
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
    if 'BBIE'==kind:
        # if DEBUG: print(f'(a) addChild( {parent_id_list}, {adc_id} )[{kind}]{getDEN(adc_id)}')
        addChild(parent_id_list,adc_id)
    elif 'RFBIE'==kind:
        # if DEBUG: print(f'(a) addChild( {parent_id_list}, {adc_id} )[{kind}]{getDEN(adc_id)}')
        addChild(parent_id_list,adc_id)
    elif 'ABIE'==kind:
        if adc_id in associationDict:
            ref_id = associationDict[adc_id]
            # if DEBUG: print(f'(b) addChild ( {parent_id_list}, {adc_id} )<{kind}>{getDEN(ref_id)}')
        elif adc_id in targetRefDict:
            targetRef_id =  targetRefDict[adc_id]
            # if DEBUG: print(f'(c) addChild ( {parent_id_list}, {adc_id} )<{kind}>{getDEN(targetRef_id)}')
    elif 'ASBIE'==kind:
        record2 = None
        if adc_id in associationDict:
            ref_id = associationDict[adc_id]
            record2 = getRecord(ref_id)
            # if DEBUG: print(f'(c) addChild( {parent_id_list}, {adc_id} )<{kind}>{getDEN(ref_id)}')
            addChild(parent_id_list,adc_id)
            parent_id_list += [adc_id]
        elif adc_id in targetRefDict:
            targetRef_id = targetRefDict[adc_id]
            record2 = getRecord(targetRef_id)
            # if DEBUG: print(f'(c) addChild( {parent_id_list}, {adc_id} )<{kind}>{getDEN(targetRef_id)}')
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
        if not record2:
            print(f'-ERROR- [{kind}] {adc_id}')
        children = record2['children']
        children0 = [x for x in children]
        for child_id in children0:
            child = getRecord(child_id)
            child_kind = child['kind']
            if 'ABIE'==child_kind:
                if DEBUG: print(f'(d) NOT ( {parent_id_list}, {child_id} )<{child_kind}>{getDEN(child_id)}')
            if 'ASBIE'==child_kind:
                # if DEBUG: print(f'(e)*addChildren( {parent_id_list}, {child_id} )<{child_kind}>{getDEN(child_id)}')
                addChildren(parent_id_list,child_id)
            else:
                if not adc_id in parent_id_list: parent_id_list += [adc_id]
                # if DEBUG: print(f'(f) addChild( {parent_id_list}, {child_id} )[{child_kind}]{getDEN(child_id)}')
                addChild(parent_id_list,child_id)
    parent_id_list.pop()
    return adc_id

if __name__ == '__main__':
    # Create the parser
    parser = argparse.ArgumentParser(prog='ADC2xBRL-taxonomy.py',
                                     usage='%(prog)s infile -o outfile -e encoding [options] ',
                                     description='Audit data collection 定義CSVファイルをxBRLタクソノミに変換')
    # Add the arguments
    parser.add_argument('inFile', metavar='infile', type=str, help='Audit data collection 定義CSVファイル')
    parser.add_argument('-o', '--outfile') # core.xsd
    parser.add_argument('-e', '--encoding')  # 'Shift_JIS' 'cp932' 'utf_8'
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
    else:
        xbrl_base = 'taxonomy'
        xbrl_base = xbrl_base.replace('/', SEP)
    if not os.path.isdir(xbrl_base):
        print('タクソノミのディレクトリがありません')
        sys.exit()
    xbrl_base = f'{xbrl_base}/'.replace('/', SEP)
    core_xsd = 'core.xsd'
    core_label = 'core-lbl'
    core_presentation = 'core-pre'
    core_definition = 'core-def'

    ncdng = args.encoding
    if ncdng:
        ncdng = ncdng.lstrip()
    else:
        ncdng = 'UTF-8'
    VERBOSE = args.verbose
    DEBUG = args.debug

    # ====================================================================
    # 1. audit_data_collection.csv -> schema
    records = []
    adc_file = file_path(adc_file)
    with open(adc_file, encoding='utf-8', newline='') as f:
        reader = csv.reader(f)#, delimiter='\t')
        header = next(reader)
        header = ['no','module','kind','table_id','class','level','occurrence','field_id','propertyTerm','representationQualifier','representation','associatedClass','datatype','desc','type','entity','attribute','domain','refClass','refProperty','tag']
        for cols in reader:
            record = {}
            for i in range(len(cols)):
                col = cols[i]
                record[header[i]] = col.strip()
            if not record['module']:
                continue
            adc_id = ''
            name = ''
            type = ''
            kind = record['kind']
            occurrence = record['occurrence']
            record['occMin'] = occurrence[:1]
            record['occMax'] = occurrence[-1:]
            if len(kind) > 5 and 'IDBIE' == kind[:5]:
                kind = 'IDBIE'
            level = record['level']
            if re.match('[0-9]+',level):
                level = int(level)
            else:
                level = 0
            record['level'] = level
            cls = record['class']
            if 'ABIE'==kind:
                adc_id = record['table_id']
            else:
                adc_id = f"{record['table_id']}-{record['field_id'].zfill(3)}"
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
            else:
                propertyTerm = record['propertyTerm']
                if kind in ['RFBIE','ASBIE']:
                    associatedClass = record['associatedClass']
                    DEN = f'{cls}. {propertyTerm}. {associatedClass}'
                else:
                    representationQualifier = record['representationQualifier']
                    representation = record['representation']
                    if representationQualifier:
                        DEN = f'{cls}. {propertyTerm}. {representationQualifier}_ {representation}'
                    else:
                        DEN = f'{cls}. {propertyTerm}. {representation}'                
                record['DEN'] = DEN                
                if level > 0:
                    parent_id = parentIDs[level-2]
                else:
                    parent_id = ''
                record['name'] = propertyTerm
                datatype = record['datatype']
                if datatype in ['PK','REF']:
                    type = datatypeMap['Identifier']['adc']
                elif datatype in datatypeMap:
                    type = datatypeMap[datatype]['adc']
                else:
                    type = 'stringItemType'
                record['type'] = type

                if not adc_id in adcDict[parent_id]['children']:
                    adcDict[parent_id]['children'].append(adc_id)
                adcDict[adc_id] = record
                if kind == 'ASBIE':
                    while len(parentIDs) > level-1:
                        parentIDs.pop()
                    while len(parentIDs) <= level-1:
                        parentIDs.append('')
                    parentIDs[level-1] = adc_id
            records.append(record)

        # header = ['module','table_id','kind','table','field_id','name','DEN','desc','XBRL-GL','classQualifier','class','propertyQualifier','property','datatypeQualifier','representation','associatedClassQualifier','associatedClass','datatype','presentation','level','key','refField','refTable','occMin','occMax']
        # header = ['Module	#	Kind	Table	No.	Name	Dictionary Entry Name	Description	XBRL GL Taxonomy Element	Object Class Term Qualifier	Object Class Term	Property Term Qualifier	Property Term	Datatype Qualifier	Representation term	Associated Object Class Term Qualifier	Associated Object Class	Datatype	Representation	Level	Key	Ref Field	Ref Table	Occurrence Min	Occurrence Max']
        # header = ['module','table_id','table','field_id','name','datatype','presentation','desc','level','key','refField','refTable','kind','DEN','classQualifier','class','propertyQualifier','property','datatypeQualifier','representation','associatedClassQualifier','associatedClass','occMin','occMax','XBRL-GL']
        # for cols in reader:
        #     record = {}
        #     for i in range(len(cols)):
        #         col = cols[i]
        #         record[header[i]] = col.strip()
        #     if not record['module']:
        #         continue
        #     adc_id = ''
        #     name = ''
        #     type = ''
        #     if 'ABIE'==record['kind']:
        #         adc_id = f"A{record['table_id'].zfill(3)}"
        #         name = record['class']
        #         if adc_id in adcDict:
        #             if DEBUG: print(f'{adc_id} already in adcDict.')
        #             continue
        #         record['name'] = name
        #         record['type'] = ''
        #         record['children'] = []
        #         record['adc_id'] = adc_id
        #         adcDict[adc_id] = record
        #     else:
        #         adc_id = f"A{record['table_id'].zfill(3)}-{record['field_id'].zfill(3)}"
        #         parent_id =adc_id[:4]
        #         name = record['name']
        #         if name:
        #             name = ' '.join([x in abbreviationMap and abbreviationMap[x] or x for x in name.split('_')])
        #         else:
        #             DEN = record['DEN']
        #             kind = record['kind']
        #             names = DEN.split('.')
        #             name0 = names[0].strip()
        #             name0 = name0.replace('ADC_ ','')
        #             name0 = name0.replace('_','')
        #             name1 = names[1].strip()
        #             name1 = name1.replace('_','')
        #             if len(names) > 2:
        #                 name2 = names[2].strip()
        #                 name2 = name2.replace('ADC_ ','')
        #                 name2 = name2.replace('_','')
        #                 if name2 in name1:
        #                     name = name1
        #                 else:
        #                     name = f'{name1} {name2}'
        #             else:
        #                 if 'ID'==name1:
        #                     name = f'{name0} ID' 
        #                 else:
        #                     name = name1
        #         record['name'] = name
        #         type = record['representation']
        #         if type in datatypeMap:
        #             type = datatypeMap[type]['adc']
        #         else:
        #             type = 'xbrli:stringItemType'
        #         record['type'] = type
        #         if not parent_id in adcDict:
        #             continue
        #         if not 'children' in adcDict[parent_id]:
        #             adcDict[parent_id]['children'] = []
        #         if not adc_id in adcDict[parent_id]['children']:
        #             adcDict[parent_id]['children'].append(adc_id)
        #         record['adc_id'] = adc_id
        #         adcDict[adc_id] = record
        #         if not 'parent' in adcDict[adc_id]:
        #             adcDict[adc_id]['parent'] = [parent_id]            
        #     records.append(record)

    targetRefDict = {}
    associationDict = {}
    for adc_id, record in adcDict.items():
        kind = record['kind']
        if not 'ABIE'==kind: continue
        # if not adc_id in targetTables and 'Core'!=record['module']: continue
        if DEBUG:
            print(f"=== {record['DEN']}")
        if 'children' in record:
            children = record['children']
            children0 = [x for x in children]
            for child_id in children0:
                child = getRecord(child_id)
                kind = child['kind']
                if not child:
                    continue
                if kind in ['BBIE','RFBIE']:
                    if DEBUG: print(f'=1= addChild( {[adc_id]}, {child_id} )[{kind}]{getDEN(child_id)}')
                    addChild([adc_id],child_id)
                    if 'RFBIE'==kind:
                        if not child_id in referenceDict:
                            associatedClass = child['associatedClass']
                            for adc2_id,record2 in adcDict.items():
                                if associatedClass==record2['class']:
                                    if not child_id in referenceDict:
                                        referenceDict[child_id] = {}
                                    if 'ABIE'==record2['kind']:
                                        referenceDict[child_id]['ABIE'] = adc2_id
                                    elif 'IDBIE'==record2['kind']:
                                        if 'A010'==adc2_id[:4]:
                                            if child['name']==record2['name']:
                                                referenceDict[child_id]['IDBIE'] = adc2_id
                                                break
                                        else:
                                            referenceDict[child_id]['IDBIE'] = adc2_id
                                            break
                elif 'ASBIE'==kind:
                    associatedClass = child['associatedClass']
                    for adc2_id,record2 in adcDict.items():
                        if associatedClass==record2['class']:
                            if DEBUG: print(f'=2= {child_id} targetRef {adc2_id}')
                            if 'n' == child['occMax']:
                                targetRefDict[child_id] = adc2_id
                            else:
                                associationDict[child_id] = adc2_id
                            kind2 = record2['kind']
                            if kind2 in ['ABIE','ASBIE']:
                                if DEBUG: print(f'=2=*addChildren( {[adc_id]}, {child_id} )<{kind2}>{getDEN(adc2_id)}')
                                addChildren([adc_id],child_id)
                            else:
                                if DEBUG: print(f'=3= addChild( {[adc_id]}, {child_id} )[{kind2}]{getDEN(adc2_id)}')
                                addChild([adc_id],child_id)
                                child = getRecord(child_id)
                                if 'associatedClass' in child:
                                    associatedClass = child['associatedClass']
                                    for adc2_id,record2 in adcDict.items():
                                        if associatedClass==record2['class']:
                                            if not child_id in referenceDict:
                                                referenceDict[child_id] = {}
                                            if 'ABIE'==record2['kind']:
                                                referenceDict[child_id]['ABIE'] = adc2_id
                                            elif 'IDBIE'==record2['kind']:
                                                if 'A010'==adc2_id[:4]:
                                                    if child['name']==record2['name']:
                                                        referenceDict[child_id]['IDBIE'] = adc2_id
                                                        break
                                                else:
                                                    referenceDict[child_id]['IDBIE'] = adc2_id
                                                    break
                            break
                elif DEBUG: print(f'=X= NOT ( {[adc_id]}, {child_id} )[{kind}]{getDEN(child_id)}')
        elif DEBUG: print(f'=X= NOT ( {[adc_id]}, {child_id} )[{kind}]{getDEN(child_id)}')

    sourceRefDict = {}
    for source_id,target_id in targetRefDict.items():
        if not target_id in sourceRefDict:
            den = getLC3_DEN(target_id)
            sourceRefDict[target_id] = {'den':den, 'source':[]}
        sourceRefDict[target_id]['source'].append(source_id)

    repeatables = {}
    for adc_id, record in adcDict.items():
        kind = record['kind']
        if 'ABIE'==kind:
            continue
        if 'occMax' in record and 'n' == record['occMax']:
            parent_id = record['parent'][-1]
            # if DEBUG: print(f"{adc_id} max occurence:{record['occMax']} parent:{parent_id}")
            if not parent_id in repeatables:
                den = getLC3_DEN(parent_id)
                repeatables[parent_id] = {'den':den, 'source':[]}
            repeatables[parent_id]['source'].append(adc_id)
    if DEBUG:
        print(repeatables)

    for adc_id,record in adcDict.items():
        if 'parent' in record:
            if len(record['parent']) > 0:
                for parent_id in record['parent']:
                    if not 'children' in adcDict[parent_id]:
                        adcDict[parent_id]['children'] = [adc_id]
                    elif not adc_id in adcDict[parent_id]['children']:
                        adcDict[parent_id]['children'].append(adc_id)

    roleMap = {}
    for adc_id,record in adcDict.items():
        den = getLC3_DEN(adc_id)
        if 'ABIE'==record['kind'] and not adc_id in roleMap:
            link_id = adc_id
            den = getLC3_DEN(link_id)
            role_id = f'link_{link_id}'
            URI = f'/{role_id}'
            roleMap[link_id] = {'adc_id':link_id,'link_id':link_id,'URI':URI,'role_id':role_id,'den':den}
    for adc_id,target_id in targetRefDict.items():
        source_id = adc_id[:4]
        link_id = f'{source_id}-{target_id}'
        if link_id not in roleMap:
            source_den = getLC3_DEN(source_id)
            target_den = getLC3_DEN(target_id)
            den = f'{source_den}-{target_den}'
            role_id = f'link_{link_id}'
            URI = f'/{role_id}'
            roleMap[link_id] = {'adc_id':adc_id,'link_id':link_id,'URI':URI,'role_id':role_id,'den':den}

    ###################################
    # core.xsd
    #
    html_head = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<!-- (c) 2022 XBRL Japan  inc. -->\n',
        '<schema \n',
        '    targetNamespace="http://www.xbrl.jp/audit-data-collection" \n',
        '    elementFormDefault="qualified" \n',
        '    xmlns="http://www.w3.org/2001/XMLSchema" \n',
        '    xmlns:adc="http://www.xbrl.jp/audit-data-collection" \n',
        '    xmlns:xlink="http://www.w3.org/1999/xlink" \n',
        '    xmlns:link="http://www.xbrl.org/2003/linkbase" \n',
        '    xmlns:xbrli="http://www.xbrl.org/2003/instance" \n',
        '    xmlns:xbrldt="http://xbrl.org/2005/xbrldt"> \n',
        '    <import namespace="http://www.xbrl.org/2003/instance" schemaLocation="http://www.xbrl.org/2003/xbrl-instance-2003-12-31.xsd"/>\n',
        '    <import namespace="http://xbrl.org/2005/xbrldt" schemaLocation="http://www.xbrl.org/2005/xbrldt-2005.xsd"/>\n',
        '    <import namespace="http://www.xbrl.org/dtr/type/numeric" schemaLocation="http://www.xbrl.org/dtr/type/numeric-2009-12-16.xsd"/>\n',
        '    <import namespace="http://www.xbrl.org/dtr/type/non-numeric" schemaLocation="http://www.xbrl.org/dtr/type/nonNumeric-2009-12-16.xsd"/>\n']
    lines = html_head
    html_annotation_head = [
        '    <annotation>\n',
        '        <appinfo>\n',
        '            <link:linkbaseRef xlink:type="simple" xlink:role="http://www.xbrl.org/2003/role/labelLinkbaseRef" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-lbl-en.xml"/>\n',
        '            <link:linkbaseRef xlink:type="simple" xlink:role="http://www.xbrl.org/2003/role/presentationLinkbaseRef" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-pre.xml"/>\n',
        '            <link:linkbaseRef xlink:type="simple" xlink:role="http://www.xbrl.org/2003/role/definitionLinkbaseRef" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-def.xml"/>\n',
        '            <!-- formula -->\n',
        '            <link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Mandatory-Base.xml"/> \n',
        '            <link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Mandatory-GL.xml"/> \n',
        '            <link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Mandatory-O2C.xml"/> \n',
        '            <link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Mandatory-P2P.xml"/> \n',
        '            <link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Mandatory-Core.xml"/> \n',
        '            <link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Card-Base.xml"/> \n',
        '            <link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Card-GL.xml"/> \n',
        '            <link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Card-O2C.xml"/> \n',
        '            <link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Card-P2P.xml"/> \n',
        '            <link:linkbaseRef xlink:type="simple" xlink:arcrole="http://www.w3.org/1999/xlink/properties/linkbase" xlink:href="core-for-Card-Core.xml"/> \n',
    ]
    lines += html_annotation_head
    html = [
        '            <!-- \n',
        '                role type\n',
        '            -->\n'
        f'            <link:roleType id="audit-data-collection-role" roleURI="http://www.xbrl.jp/audit-data-collection/role">\n',
        f'                <link:definition>link audit-data-collection</link:definition>\n',
        f'                <link:usedOn>link:definitionLink</link:usedOn>\n',
        f'                <link:usedOn>link:presentationLink</link:usedOn>\n',
        '            </link:roleType>\n',
    ]
    for adc_id,role in roleMap.items():
        role_id = role["role_id"]
        URI = role['URI']
        link_id = role['link_id']
        den = role["den"]
        if 4==len(adc_id):
            html.append(f'            <link:roleType id="{role_id}" roleURI="http://www.xbrl.jp/audit-data-collection/role{URI}">\n')
            html.append(f'                <link:definition>{den}</link:definition>\n')
            html.append(f'                <link:usedOn>link:definitionLink</link:usedOn>\n')
            html.append('            </link:roleType>\n')
        else:
            source_den = den[:den.index('-')]
            target_den = den[den.index('-')+1:]
            html.append(f'            <link:roleType id="{role_id}" roleURI="http://www.xbrl.jp/audit-data-collection/role{URI}">\n')
            html.append(f'                <link:definition>{source_den} to {target_den}</link:definition>\n')
            html.append(f'                <link:usedOn>link:definitionLink</link:usedOn>\n')
            html.append('            </link:roleType>\n')
    lines += html

    html = [
        '            <!--\n',
        '                description: roleType arcroleType\n',
        '            -->\n'
        '            <link:roleType id="description" roleURI="http://www.xbrl.jp/audit-data-collection/role/description">\n',
        '                <link:definition>description</link:definition>\n',
        '                <link:usedOn>link:label</link:usedOn>\n',
        '            </link:roleType>\n',
        '            <link:arcroleType id="concept-description" cyclesAllowed="undirected" arcroleURI="http://www.xbrl.jp/audit-data-collection/arcrole/concept-description">\n',
        '                <link:definition>concept to description</link:definition>\n',
        '                <link:usedOn>link:labelArc</link:usedOn>\n',
        '            </link:arcroleType >\n',
    ]
    lines += html

    html = [
        '            <!--\n',
        '                primary key: roleType arcroleType\n',
        '            -->\n'
        '            <link:roleType id="primary-key" roleURI="http://www.xbrl.jp/audit-data-collection/role/primary-key">\n',
        '                <link:definition>primary key</link:definition>\n',
        '                <link:usedOn>link:definitionLink</link:usedOn>\n',
        '            </link:roleType>\n',
        '            <link:arcroleType id="concept-primary-key" cyclesAllowed="undirected" arcroleURI="http://www.xbrl.jp/audit-data-collection/arcrole/concept-primary-key">\n',
        '                <link:definition>concept primary key</link:definition>\n',
        '                <link:usedOn>link:definitionArc</link:usedOn>\n',
        '            </link:arcroleType >\n',
    ]
    lines += html

    html = [
        '            <!--\n',
        '                reference identifier: roleType arcroleType\n',
        '            -->\n'
        '            <link:roleType id="reference-identifier" roleURI="http://www.xbrl.jp/audit-data-collection/role/reference-identifier">\n',
        '                <link:definition>reference identifier</link:definition>\n',
        '                <link:usedOn>link:definitionLink</link:usedOn>\n',
        '            </link:roleType>\n',
        '            <link:arcroleType id="concept-reference-identifier" cyclesAllowed="undirected" arcroleURI="http://www.xbrl.jp/audit-data-collection/arcrole/concept-reference-identifier">\n',
        '                <link:definition>concept reference identifier</link:definition>\n',
        '                <link:usedOn>link:definitionArc</link:usedOn>\n',
        '            </link:arcroleType >\n',
    ]
    lines += html

    html = [
        '            <!--\n',
        '                require: roleType\n',
        '            -->\n'
        '            <link:roleType id="require" roleURI="http://www.xbrl.jp/audit-data-collection/role/require">\n',
        '                <link:definition>require</link:definition>\n',
        '                <link:usedOn>link:definitionLink</link:usedOn>\n',
        '            </link:roleType>\n',
    ]
    lines += html

    html_annotation_tail = [
        '        </appinfo>\n',
        '    </annotation>\n'
    ]
    lines += html_annotation_tail

    html_type = [
        '    <!-- typed dimension referenced element -->\n',
        '    <element name="_v" id="_v">\n',
        '        <simpleType>\n',
        '            <restriction base="string"/>\n',
        '        </simpleType>\n',
        '    </element>\n',
        '    <element name="_activity" id="_activity">',
        '        <simpleType>',
        '            <restriction base="string">',
        '                <pattern value="\s*(Created|Approved|LastModified|Entered|Posted)\s*"/>',
        '            </restriction>',
        '        </simpleType>',
        '    </element>'
    ]
    lines += html_type

    html_hypercube = [
        '    <!-- Hypercube -->\n'
    ]
    # Hypercube
    for adc_id,role in roleMap.items():
        link_id = role['link_id']
        html_hypercube.append(f'    <element name="h_{link_id}" id="h_{link_id}" substitutionGroup="xbrldt:hypercubeItem" type="xbrli:stringItemType" nillable="true" abstract="true" xbrli:periodType="instant"/>\n')
    lines += html_hypercube

    html_dimension = [
        '    <!-- Dimension -->\n'
    ]
    # Dimension
    for adc_id,role in roleMap.items():
        link_id = role['link_id']
        if 4==len(link_id):
            if 'A075'==link_id:
                html_dimension.append(f'    <element name="d_{link_id}" id="d_{link_id}" substitutionGroup="xbrldt:dimensionItem" type="xbrli:stringItemType" abstract="true" xbrli:periodType="instant" xbrldt:typedDomainRef="#_activity"/>\n')
            else:
                html_dimension.append(f'    <element name="d_{link_id}" id="d_{link_id}" substitutionGroup="xbrldt:dimensionItem" type="xbrli:stringItemType" abstract="true" xbrli:periodType="instant" xbrldt:typedDomainRef="#_v"/>\n')
    lines += html_dimension

    html_itemtype = [
        '    <!-- item type -->\n'
    ]
    # complexType
    for name,type in datatypeMap.items():
        adc = type['adc']
        xbrli = type['xbrli']
        complexType = [
            f'        <complexType name="{adc}">\n',
            '            <simpleContent>\n',
            f'                <restriction base="xbrli:{xbrli}"/>\n',
            '            </simpleContent>\n',
            '        </complexType>\n',
        ]
        html_itemtype += complexType
    lines += html_itemtype

    lines.append('    <!-- element -->\n')
    
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
            type = record['type']
            if 'ABIE'==kind or adc_id in targetRefDict:
                line = f'        <element name="{adc_id}" id="{adc_id}" abstract="true" type="xbrli:stringItemType" nillable="true" substitutionGroup="xbrli:item" xbrli:periodType="instant"/>\n'
            else:
                type = get_element_datatype(adc_id,type,kind)
                line = f'        <element name="{adc_id}" id="{adc_id}" type="{type}" nillable="false" substitutionGroup="xbrli:item" xbrli:periodType="instant"/>\n'
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

    elementsDefined = set()
    primaryKeys = {}
    for record in adcDict.values():
        adc_id = record['adc_id']
        kind = record['kind']
        referenced_id = None
        defineElement(adc_id,record)
        if 'IDBIE'==kind:
            primaryKeys[adc_id[:4]] = adc_id
        if 'ASBIE'==kind:
            if adc_id in referenceDict:
                referenced_id = referenceDict[adc_id]['ABIE']
            elif adc_id in targetRefDict:
                referenced_id = targetRefDict[adc_id]
            else:
                associatedClass = record['associatedClass']
                referenced_id = None
                for adc2_id,record2 in adcDict.items():
                    if associatedClass==record2['class']:
                        referenced_id = f'{adc_id[:4]}-{adc2_id}'
                        defineElement(referenced_id,record2)
                        break
            if referenced_id:
                record2 = getRecord(referenced_id[-4:])
                if 'children' in record2:
                    children = record2['children']
                    for child_id in children:
                        child = getRecord(child_id)
                        referenced_id = f'{adc_id[:4]}-{child_id}'
                        defineElement(referenced_id,child)
        
    for link_id,role in roleMap.items():
        if 4==len(link_id):
            continue
        adc_id = link_id[5:]
        record = getRecord(adc_id)
        defineElement(link_id,record)
        lookupPrimarykey(link_id)

    for adc_id,target_id in targetRefDict.items():
        link_id = f'{source_id}{target_id}'
        if not link_id in primaryKeys:
            primary_key = lookupPrimarykey(link_id)
            primaryKeys[link_id] = primary_key
            if DEBUG:
                print(f'NOT DEFINED primary key {primary_key} in {link_id}')

    for adc_id,target_id in associationDict.items():
        link_id = f'{source_id}{target_id}'
        if not link_id in primaryKeys:
            primary_key = lookupPrimarykey(link_id)
            primaryKeys[link_id] = primary_key
            if DEBUG:
                print(f'NOT DEFINED primary key {primary_key} in {link_id}')

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
        lines.append(f'        <!-- {adc_id} {name} -->\n')
        if not adc_id in locsDefined:
            locsDefined[adc_id] = adc_id
            line = f'        <link:loc xlink:type="locator" xlink:href="{core_xsd}#{adc_id}" xlink:label="{adc_id}" xlink:title="{adc_id}"/>\n'
        else:
            line = f'            <!-- link:loc defined -->\n'
        lines.append(line)
        # name
        if not adc_id in definedLabels:
            definedLabels[adc_id] = adc_id
            line = f'        <link:label xlink:type="resource" xlink:label="label_{adc_id}" xlink:title="label_{adc_id}" id="label_{adc_id}" xml:lang="en" xlink:role="http://www.xbrl.org/2003/role/label">{name}</link:label>\n'
        else:
            line = f'            <!-- link:label http://www.xbrl.org/2003/role/label defined -->\n'
        lines.append(line)
        if not adc_id in arcsDefined:
            arcsDefined[adc_id] = adc_id
            line = f'        <link:labelArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/concept-label" xlink:from="{adc_id}" xlink:to="label_{adc_id}" xlink:title="label: {adc_id} to label_{adc_id}"/>\n'
        else:
            line = f'            <!-- link:labelArc http://www.xbrl.org/2003/arcrole/concept-label defined -->\n'
        lines.append(line)
        # Desc
        if name != Desc:
            if not adc_id in definedDescs:
                definedDescs[adc_id] = adc_id
                line = f'        <link:label xlink:type="resource" xlink:label="description_{adc_id}" xlink:title="description_{adc_id}" id="description_{adc_id}" xml:lang="en" xlink:role="http://www.xbrl.jp/audit-data-collection/role/description">{Desc}</link:label>\n'
            else:
                line = f'            <!-- link:label http://www.xbrl.jp/audit-data-collection/role/description defined -->\n'
            lines.append(line)
            if not adc_id in definedDescArcs:
                definedDescArcs[adc_id] = adc_id
                line = f'        <link:labelArc xlink:type="arc" xlink:arcrole="http://www.xbrl.jp/audit-data-collection/arcrole/concept-description" xlink:from="{adc_id}" xlink:to="description_{adc_id}" xlink:title="label: {adc_id} to label_{adc_id}"/>\n'
            else:
                line = f'            <!-- link:labelArc http://www.xbrl.jp/audit-data-collection/arcrole/concept-description defined -->\n'
            lines.append(line)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<!--  (c) 2022 XBRL Japan inc. -->\n',
        '<link:linkbase\n',
        '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n',
        '    xmlns:link="http://www.xbrl.org/2003/linkbase"\n',
        '    xmlns:xlink="http://www.w3.org/1999/xlink"\n',
        '    xsi:schemaLocation="http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd">\n',
        '    <link:roleRef roleURI="http://www.xbrl.jp/audit-data-collection/role/description" xlink:type="simple" xlink:href="core.xsd#description"/>\n',
        '    <link:arcroleRef arcroleURI="http://www.xbrl.jp/audit-data-collection/arcrole/concept-description" xlink:type="simple" xlink:href="core.xsd#concept-description"/>\n',
        '    <link:labelLink xlink:type="extended" xlink:role="http://www.xbrl.org/2003/role/link">\n'
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
        if 'ASBIE'==kind:
            if adc_id in referenceDict:
                referenced_id = referenceDict[adc_id]['ABIE']
            elif adc_id in targetRefDict:
                referenced_id = targetRefDict[adc_id]
            else:
                associatedClass = record['associatedClass']
                referenced_id = None
                for adc2_id,record2 in adcDict.items():
                    if associatedClass==record2['class']:
                        referenced_id = f'{adc_id[:4]}-{adc2_id}'
                        linkLabel(referenced_id,name,Desc)
                        break

    for adc_id,referenced_id in targetRefDict.items():
        record = getRecord(referenced_id)
        name = record['name']
        Desc = record['desc']
        linkLabel(adc_id,name,Desc)
        adc_id = f'{adc_id[:4]}-{referenced_id}'
        linkLabel(adc_id,name,Desc)

    lines.append('    </link:labelLink>\n')
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
    def linkPresentation(adc_id,children):
        global lines
        global count
        global locsDefined
        global arcsDefined
        if not adc_id: 
            return
        record = getRecord(adc_id)
        if not record:
            return
        name = record['name']
        if not adc_id in locsDefined:
            locsDefined[adc_id] = name
            lines.append(f'        <!-- {kind} {adc_id} {name} -->\n')
            lines.append(f'        <link:loc xlink:type="locator" xlink:href="{core_xsd}#{adc_id}" xlink:label="{adc_id}" xlink:title="presentation: {adc_id} {name}"/>\n')
        for child_id in children:
            child = getRecord(child_id)
            child_kind = child['kind']
            child_name = child['name']
            if 'ASBIE'==child_kind and child_id in targetRefDict:
                target_id = child_id
                if not target_id in locsDefined:
                    locsDefined[target_id] = child_name
                    lines.append(f'        <link:loc xlink:type="locator" xlink:href="{core_xsd}#{target_id}" xlink:label="{target_id}" xlink:title="presentation parent: {target_id} {child_name}"/>\n')
                arc_id = F'{adc_id} {target_id}'
                if not arc_id in arcsDefined:
                    arcsDefined[arc_id] = f'{name} to {child_name}'
                    count += 1
                    lines.append(f'        <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="{adc_id}" xlink:to="{target_id}" order="{count}" xlink:title="presentation: {adc_id} {name} to {target_id} {child_name}"/>\n')
                    if 'children' in child and len(child['children']) > 0:
                        grand_children = child['children']
                        linkPresentation(target_id,grand_children)
            else:
                if not child_id in locsDefined:
                    locsDefined[child_id] = child_name
                    lines.append(f'        <link:loc xlink:type="locator" xlink:href="{core_xsd}#{child_id}" xlink:label="{child_id}" xlink:title="presentation parent: {child_id} {child_name}"/>\n')
                arc_id = F'{adc_id} {child_id}'
                if not arc_id in arcsDefined:
                    arcsDefined[arc_id] = f'{name} to {child_name}'
                    count += 1
                    lines.append(f'        <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="{adc_id}" xlink:to="{child_id}" order="{count}" xlink:title="presentation: {adc_id} {name} to {child_id} {child_name}"/>\n')
                    if 'children' in child and len(child['children']) > 0:
                        grand_children = child['children']
                        linkPresentation(child_id,grand_children)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<!--  (c) 2022 XBRL Japan inc. -->\n',
        '<link:linkbase\n',
        '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n',
        '    xsi:schemaLocation="http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd"\n',
        '    xmlns:link="http://www.xbrl.org/2003/linkbase"\n',
        '    xmlns:xlink="http://www.w3.org/1999/xlink">\n',
        '    <link:roleRef roleURI="http://www.xbrl.jp/audit-data-collection/role" xlink:type="simple" xlink:href="core.xsd#audit-data-collection-role"/>\n',
        '    <link:presentationLink xlink:type="extended" xlink:role="http://www.xbrl.jp/audit-data-collection/role">\n',
    ]
    locsDefined = {}
    arcsDefined = {}
    for record in [x for x in records if 'ABIE'==x['kind']]:
        adc_id = record['adc_id']
        kind = record['kind']
        count = 0
        children = record['children']
        linkPresentation(adc_id,children)
       
    lines.append('    </link:presentationLink>\n')
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
        '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n',
        '    xsi:schemaLocation="http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd"\n',
        '    xmlns:link="http://www.xbrl.org/2003/linkbase"\n',
        '    xmlns:xbrldt="http://xbrl.org/2005/xbrldt"\n',
        '    xmlns:xlink="http://www.w3.org/1999/xlink">\n'
    ]
    lines.append('    <!-- roleRef -->\n')
    for role in roleMap.values():
        role_id = role["role_id"]
        link_id = role['link_id']
        URI = f"/{role_id}"
        lines.append(f'    <link:roleRef roleURI="http://www.xbrl.jp/audit-data-collection/role{URI}" xlink:type="simple" xlink:href="{core_xsd}#{role_id}"/>\n')
    html = [
        f'    <link:roleRef roleURI="http://www.xbrl.jp/audit-data-collection/role/primary-key" xlink:type="simple" xlink:href="{core_xsd}#primary-key"/>\n',
        f'    <link:roleRef roleURI="http://www.xbrl.jp/audit-data-collection/role/reference-identifier" xlink:type="simple" xlink:href="{core_xsd}#reference-identifier"/>\n',
        f'    <link:roleRef roleURI="http://www.xbrl.jp/audit-data-collection/role/require" xlink:type="simple" xlink:href="{core_xsd}#require"/>\n',
        '    <!-- arcroleRef -->\n',
        '    <link:arcroleRef arcroleURI="http://xbrl.org/int/dim/arcrole/all" xlink:type="simple" xlink:href="http://www.xbrl.org/2005/xbrldt-2005.xsd#all"/>\n',
        '    <link:arcroleRef arcroleURI="http://xbrl.org/int/dim/arcrole/domain-member" xlink:type="simple" xlink:href="http://www.xbrl.org/2005/xbrldt-2005.xsd#domain-member"/>\n',
        '    <link:arcroleRef arcroleURI="http://xbrl.org/int/dim/arcrole/hypercube-dimension" xlink:type="simple" xlink:href="http://www.xbrl.org/2005/xbrldt-2005.xsd#hypercube-dimension"/>\n',
        '    <link:arcroleRef arcroleURI="http://xbrl.org/int/dim/arcrole/dimension-domain" xlink:type="simple" xlink:href="http://www.xbrl.org/2005/xbrldt-2005.xsd#dimension-domain"/>\n',
        f'    <link:arcroleRef arcroleURI="http://www.xbrl.jp/audit-data-collection/arcrole/concept-primary-key" xlink:type="simple" xlink:href="{core_xsd}#concept-primary-key"/>\n',
        f'    <link:arcroleRef arcroleURI="http://www.xbrl.jp/audit-data-collection/arcrole/concept-reference-identifier" xlink:type="simple" xlink:href="{core_xsd}#concept-reference-identifier"/>\n',
    ]
    lines += html

    for adc_id,role in roleMap.items():
        defineHypercube(adc_id, role)

    # primary-key
    def defPK(link_id,primary_key):
        global lines
        global count
        arc_id = f'{link_id} {primary_key}'
        if not arc_id in arcsDefined:
            lines.append(f'        <!-- primary-key {primary_key} -->\n')
        if not link_id in locsDefined:
            locsDefined.add(link_id)
            lines.append(f'        <link:loc xlink:type="locator" xlink:href="{core_xsd}#{link_id}" xlink:label="{link_id}" xlink:title="{link_id}"/>\n')
        if not primary_key in locsDefined:
            locsDefined.add(primary_key)
            lines.append(f'        <link:loc xlink:type="locator" xlink:href="{core_xsd}#{primary_key}" xlink:label="{primary_key}" xlink:title="{primary_key}"/>\n')
        if not arc_id in arcsDefined:
            count = 1
            arcsDefined.add(arc_id)
            lines.append(f'        <link:definitionArc xlink:type="arc" xlink:arcrole="http://www.xbrl.jp/audit-data-collection/arcrole/concept-primary-key" xlink:from="{link_id}" xlink:to="{primary_key}" xlink:title="concept-primary-key: {link_id} to {primary_key}" order="{count}"/>\n')
    
    # reference-identifier
    def defREF(adc_id,referenced_id):
        global lines
        global count
        arc_id = f'{adc_id} {referenced_id}'
        if not arc_id in arcsDefined:
            lines.append(f'        <!-- reference-identifier {adc_id} to {referenced_id} -->\n')
        if not referenced_id in locsDefined:
            locsDefined.add(referenced_id)
            lines.append(f'        <link:loc xlink:type="locator" xlink:href="{core_xsd}#{referenced_id}" xlink:label="{referenced_id}" xlink:title="{referenced_id}"/>\n')
        if not adc_id in locsDefined:
            locsDefined.add(adc_id)
            lines.append(f'        <link:loc xlink:type="locator" xlink:href="{core_xsd}#{adc_id}" xlink:label="{adc_id}" xlink:title="{adc_id}"/>\n')
        count += 1
        if not arc_id in arcsDefined:
            arcsDefined.add(arc_id)
            lines.append(f'        <link:definitionArc xlink:type="arc" xlink:arcrole="http://www.xbrl.jp/audit-data-collection/arcrole/concept-reference-identifier" xlink:from="{adc_id}" xlink:to="{referenced_id}" xlink:title="concept-reference-identifier: {adc_id} to {referenced_id}" order="{count}"/>\n')

    # require
    def defREQ(link_id,primary_key):
        global lines
        global count
        source_id = primary_key[:-8]
        record = getRecord(link_id[-4:])
        children = record['children']
        for child_id in children:
            child = getRecord(child_id)
            if '1'==child['occMin'] and 'ASBIE'!=child['kind']:
                required_id = f'{source_id}{child_id}'
                arc_id = f'{primary_key} {required_id}'
                if not arc_id in arcsDefined:
                    lines.append(f'        <!-- requires-element {primary_key} to {required_id} -->\n')
                if not required_id in locsDefined:
                    locsDefined.add(required_id)
                    lines.append(f'        <link:loc xlink:type="locator" xlink:href="{core_xsd}#{required_id}" xlink:label="{required_id}" xlink:title="{required_id}"/>\n')
                if not primary_key in locsDefined:
                    locsDefined.add(primary_key)
                    lines.append(f'        <link:loc xlink:type="locator" xlink:href="{core_xsd}#{primary_key}" xlink:label="{primary_key}" xlink:title="{primary_key}"/>\n')
                count += 1
                if not arc_id in arcsDefined:
                    arcsDefined.add(arc_id)
                    lines.append(f'        <link:definitionArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/requires-element" xlink:from="{primary_key}" xlink:to="{required_id}" xlink:title="concept-reference-identifier: {primary_key} to {required_id}" order="{count}"/>\n')

    # primary-key
    locsDefined = set()
    arcsDefined = set()
    primaryKeys = {}
    count = 0
    lines.append(f'    <link:definitionLink xlink:type="extended" xlink:role="http://www.xbrl.jp/audit-data-collection/role/primary-key">\n')

    for record in adcDict.values():
        adc_id = record['adc_id']
        kind = record['kind']
        if 'IDBIE'==kind:
            link_id = adc_id[:4]
            primary_key = adc_id
            if not link_id in primaryKeys:
                primaryKeys[link_id] = primary_key
                defPK(link_id,primary_key)

    for link_id in roleMap.keys():
        if len(link_id) > 4:
            source_id = link_id[:4]
            adc_id = link_id[5:]
            record = getRecord(adc_id)
            if adc_id in primaryKeys:
                primary_key = f'{source_id}-{primaryKeys[adc_id]}'
                if not link_id in primaryKeys:
                    primaryKeys[link_id] = primary_key
                    defPK(link_id,primary_key)

    notDefinedPrimaryKeys = set()
    for adc_id,target_id in targetRefDict.items():
        source_id = adc_id[:4]
        if not target_id in primaryKeys:
            print(f'ADDED targetRefDict {adc_id} {target_id} in primaryKeys')
            link_id = f'{source_id}-{target_id}'
            notDefinedPrimaryKeys.add(link_id)
            continue
        primary_key = primaryKeys[target_id]
        primary_key = f'{source_id}-{primary_key}'
        link_id = primary_key[:9]
        if not link_id in primaryKeys:
            primaryKeys[link_id] = primary_key
            defPK(link_id,primary_key)

    for adc_id,target_id in associationDict.items():
        source_id = adc_id[:4]
        if not target_id in primaryKeys:
            print(f'ADDED associationDict {adc_id} {target_id} in primaryKeys')
            link_id = f'{source_id}-{target_id}'
            notDefinedPrimaryKeys.add(link_id)
            continue
        primary_key = primaryKeys[target_id]
        primary_key = f'{source_id}-{primary_key}'
        link_id = primary_key[:9]
        if not link_id in primaryKeys:
            primaryKeys[link_id] = primary_key
            defPK(link_id,primary_key)

    notDefinedPrimaryKeys = sorted(notDefinedPrimaryKeys)
    for link_id in notDefinedPrimaryKeys:
        source_id = link_id[:4]
        abie_id = link_id[-4:]
        records = [record for record in adcDict.values() if abie_id in record['adc_id']]
        primary_keys = set()
        for record in records:
            primary_key = record['adc_id']
            primary_key = f'{source_id}-{primary_key}'
            if 'IDBIE'==record['kind']:
                primary_keys.add(primary_key)
        if 1==len(primary_keys):
            primary_key = primary_keys.pop()
            primaryKeys[link_id] = primary_key
            defPK(link_id,primary_key)
        elif len(primary_keys) > 1:
            for primary_key in primary_keys:
                defPK(link_id,primary_key)
            primaryKeys[link_id] = primary_keys

    lines.append('    </link:definitionLink>\n')

    # reference-identifier
    locsDefined = set()
    arcsDefined = set()
    referenceIdentifiers = {}
    count = 0
    lines.append(f'    <link:definitionLink xlink:type="extended" xlink:role="http://www.xbrl.jp/audit-data-collection/role/reference-identifier">\n')
    for adc_id,record in adcDict.items():
        kind = record['kind']
        if 'RFBIE'==kind:
            if not adc_id in referenceDict:
                associatedClass = record['associatedClass']
                for adc2_id,record2 in adcDict.items():
                    if associatedClass==record2['class']:
                        referenced_id = adc2_id
                        if not child_id in referenceDict:
                            referenceDict[child_id] = {}
                        if 'ABIE'==record2['kind']:
                            referenceDict[child_id]['ABIE'] = adc2_id
                        elif 'IDBIE'==record2['kind']:
                            referenceDict[child_id]['IDBIE'] = adc2_id
                            break
            elif not 'IDBIE' in referenceDict[adc_id]:
                print(f'NOT DEFINED referenceDict[{adc_id}][IDBIE]')
            else:
                referenced_id = referenceDict[adc_id]['IDBIE']
            arc_id =f'{adc_id} {referenced_id}'
            if not arc_id in referenceIdentifiers:
                referenceIdentifiers[adc_id] = referenced_id
                defREF(adc_id,referenced_id)
    for link_id in roleMap.keys():
        if len(link_id) > 4:
            adc_id = link_id[5:]
            record = getRecord(adc_id)
            if adc_id in referenceIdentifiers:
                referenced_id = referenceIdentifiers[adc_id]
    lines.append('    </link:definitionLink>\n')

    # require
    locsDefined = set()
    arcsDefined = set()
    count = 0
    lines.append(f'    <link:definitionLink xlink:type="extended" xlink:role="http://www.xbrl.jp/audit-data-collection/role/require">\n')
    for link_id,primary_key in primaryKeys.items():
        adc_id = primary_key[-8:]
        record = getRecord(adc_id)
        defREQ(link_id,primary_key)

    lines.append('    </link:definitionLink>\n')
    lines.append('</link:linkbase>\n')

    adc_definition_file = file_path(f'{xbrl_base}{core_definition}.xml')
    with open(adc_definition_file, 'w', encoding='utf_8', newline='') as f:
        f.writelines(lines)
    if VERBOSE:
        print(f'-- {adc_definition_file}')

    ###################################
    # formulaLink
    #
    def cardinalityAssertion(primarykey):
        if primarykey in assertionDefined:
            return ''
        assertionDefined.add(primarykey)
        lines_assertion = [
            '        <!-- '+primarykey+' duplicate assertion -->\n',
            '        <va:valueAssertion id="Card_'+primarykey+'" test="count($duplicates_'+primarykey+')=0" aspectModel="dimensional" implicitFiltering="true" xlink:type="resource" xlink:label="Card_'+primarykey+'"/>\n',
            '        <!-- unsatisfied message -->\n',
            '        <gen:arc order="1.0" xlink:type="arc" xlink:arcrole="http://xbrl.org/arcrole/2010/assertion-unsatisfied-message" xlink:from="Card_'+primarykey+'" xlink:to="error-Card_'+primarykey+'"/>\n',
            '        <msg:message id="error-Card_'+primarykey+'" xlink:type="resource" xlink:role="http://www.xbrl.org/2010/role/message" xlink:label="error-Card_'+primarykey+'" xml:lang="en">Not satisfied error: [Card '+primarykey[:-4]+'] '+primarykey[:-4]+' shall not contain duplicate items. Fact { node-name($duplicates_'+primarykey+') } in context { $duplicates_'+primarykey+'/@contextRef }</msg:message>\n',
            '        <!-- variable -->\n',
            '        <variable:variableArc name="duplicates_'+primarykey+'" order="1.0" xlink:type="arc" xlink:arcrole="http://xbrl.org/arcrole/2008/variable-set" xlink:from="Card_'+primarykey+'" xlink:to="gen_duplicates_'+primarykey+'"/>\n',
            '        <variable:generalVariable id="gen_duplicates_'+primarykey+'" bindAsSequence="true" select="//*[self::node()/@contextRef=preceding-sibling::adc:'+primarykey+'/@contextRef and name(self::node())=preceding-sibling::*[1]/name(self::node())]" xlink:type="resource" xlink:label="gen_duplicates_'+primarykey+'"/>\n',
        ]
        return lines_assertion

    def mandatoryAssertion(key1,key2,key3,num):
        global assertionDefined
        if key1 and key2 and key3:
            mandatorykey = f'{key2}-{key3}-{num}'
            if mandatorykey in assertionDefined:
                return ''
            assertionDefined.add(mandatorykey)
            distinctContext = f'distinct-values(//*[local-name(.)=\'context\']/@id[substring(.,1,4)=\'{key1}\' and contains(substring-after(.,\'_\'),\'{key2}\') and contains(substring-after(.,\'{key2}_\'),\'{key3}\')])'
            distinctElement = f'distinct-values(//adc:{key2}-{key3}-{num}[substring(@contextRef,1,4)=\'{key1}\' and contains(substring-after(@contextRef,\'_\'),\'{key2}\') and contains(substring-after(@contextRef,\'{key2}_\'),\'{key3}\')]/@contextRef)'
        elif key1 and key2:
            mandatorykey = f'{key1}-{key2}-{num}'
            if mandatorykey in assertionDefined:
                return ''
            assertionDefined.add(mandatorykey)
            distinctContext = f'distinct-values(//*[local-name(.)=\'context\']/@id[substring(.,1,4)=\'{key1}\' and contains(substring-after(.,\'_\'),\'{key2}\') and not(contains(substring-after(.,\'{key2}_\'),\'_\'))])'
            distinctElement = f'distinct-values(//adc:{key1}-{key2}-{num}[substring(@contextRef,1,4)=\'{key1}\' and contains(substring-after(@contextRef,\'_\'),\'{key2}\') and not(contains(substring-after(.,\'{key2}_\'),\'_\'))]/@contextRef)'
        elif key1:
            mandatorykey = f'{key1}-{num}'
            if mandatorykey in assertionDefined:
                return ''
            assertionDefined.add(mandatorykey)
            distinctContext = f'distinct-values(//*[local-name(.)=\'context\']/@id[substring(.,1,4)=\'{key1}\' and not(contains(substring-after(.,\'_\'),\'_\'))])'
            distinctElement = f'distinct-values(//adc:{key1}-{num}[substring(@contextRef,1,4)=\'{key1}\' and not(contains(substring-after(@contextRef,\'_\'),\'_\'))]/@contextRef)'
        else:
            return ''
        lines_assertion = [
            '        <!-- '+mandatorykey+' mandatory assertion -->\n',
            '        <va:valueAssertion id="Mandatory_'+mandatorykey+'" test="count($context_'+mandatorykey+')=count($element_'+mandatorykey+')" aspectModel="dimensional" implicitFiltering="true" xlink:type="resource" xlink:label="Mandatory_'+mandatorykey+'"/>\n',
            '        <!-- unsatisfied message -->\n',
            '        <gen:arc order="1.0" xlink:type="arc" xlink:arcrole="http://xbrl.org/arcrole/2010/assertion-unsatisfied-message" xlink:from="Mandatory_'+mandatorykey+'" xlink:to="error-Mandatory_'+mandatorykey+'"/>\n',
            '        <msg:message id="error-Mandatory_'+mandatorykey+'" xlink:type="resource" xlink:role="http://www.xbrl.org/2010/role/message" xlink:label="error-Mandatory_'+mandatorykey+'" xml:lang="en">Not satisfied error: [Mandatory '+mandatorykey+'] '+mandatorykey+' is a mandatory items.</msg:message>\n',
            '        <!-- variable -->\n',
            '        <variable:variableArc name="context_'+mandatorykey+'" order="1" xlink:type="arc" xlink:arcrole="http://xbrl.org/arcrole/2008/variable-set" xlink:from="Mandatory_'+mandatorykey+'" xlink:to="gen_context_'+mandatorykey+'"/>\n',
            '        <variable:variableArc name="element_'+mandatorykey+'" order="1.0" xlink:type="arc" xlink:arcrole="http://xbrl.org/arcrole/2008/variable-set" xlink:from="Mandatory_'+mandatorykey+'" xlink:to="gen_element_'+mandatorykey+'"/>\n',
            '        <variable:generalVariable id="gen_context_'+mandatorykey+'" bindAsSequence="true" select="'+distinctContext+'" xlink:type="resource" xlink:label="gen_context_'+mandatorykey+'"/>\n',
            '        <variable:generalVariable id="gen_element_'+mandatorykey+'" bindAsSequence="true" select="'+distinctElement+'" xlink:type="resource" xlink:label="gen_element_'+mandatorykey+'"/>\n',
        ]
        return lines_assertion

    def writePrimaryFormula(minKey,maxKey,module):
        global assertionDefined
        global primaryKeys
        lines = [
            '<?xml version="1.0"?>\n',
            '<link:linkbase \n',
            '    xsi:schemaLocation="\n',
            '    http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd \n',
            '    http://xbrl.org/2008/generic http://www.xbrl.org/2008/generic-link.xsd \n',
            '    http://xbrl.org/2008/assertion/value http://www.xbrl.org/2008/value-assertion.xsd \n',
            '    http://xbrl.org/2008/variable http://www.xbrl.org/2008/variable.xsd \n',
            '    http://xbrl.org/2010/message http://www.xbrl.org/2010/generic-message.xsd" \n',
            '    xmlns:adc="http://www.xbrl.jp/audit-data-collection" \n',
            '    xmlns:xlink="http://www.w3.org/1999/xlink" \n',
            '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \n',
            '    xmlns:link="http://www.xbrl.org/2003/linkbase" \n',
            '    xmlns:va="http://xbrl.org/2008/assertion/value" \n',
            '    xmlns:gen="http://xbrl.org/2008/generic" \n',
            '    xmlns:variable="http://xbrl.org/2008/variable" \n',
            '    xmlns:msg="http://xbrl.org/2010/message">\n',
            '    <link:arcroleRef arcroleURI="http://xbrl.org/arcrole/2010/assertion-unsatisfied-message" xlink:type="simple" xlink:href="http://www.xbrl.org/2010/validation-message.xsd#assertion-unsatisfied-message"/>\n',
            '    <link:arcroleRef arcroleURI="http://xbrl.org/arcrole/2010/assertion-satisfied-message" xlink:type="simple" xlink:href="http://www.xbrl.org/2010/validation-message.xsd#assertion-satisfied-message"/>\n',
            '    <link:roleRef roleURI="http://www.xbrl.org/2010/role/message" xlink:type="simple" xlink:href="http://www.xbrl.org/2010/generic-message.xsd#standard-message"/>\n',
            '    <link:arcroleRef arcroleURI="http://xbrl.org/arcrole/2008/variable-set" xlink:type="simple" xlink:href="http://www.xbrl.org/2008/variable.xsd#variable-set"/>\n',
            '    <link:roleRef roleURI="http://www.xbrl.org/2008/role/link" xlink:type="simple" xlink:href="http://www.xbrl.org/2008/generic-link.xsd#standard-link-role"/>\n',
            '    <gen:link xlink:type="extended" xlink:role="http://www.xbrl.org/2008/role/link">\n'
        ]

        for link_id,primarykey in primaryKeys.items():
            key = primarykey[:4]
            if minKey <= key and key <= maxKey:
                lines_assertion = cardinalityAssertion(primarykey)
                lines += lines_assertion

        lines.append('    </gen:link>\n')
        lines.append('</link:linkbase>\n')

        core_for_file = file_path(f'{xbrl_base}{core_for_Card}-{module}.xml')
        with open(core_for_file, 'w', encoding='utf_8', newline='') as f:
            f.writelines(lines)
        if VERBOSE:
            print(f'-- {core_for_file}')

    def writeMandatoryFormula(minKey,maxKey,module):
        global assertionDefined
        lines = [
            '<?xml version="1.0"?>\n',
            '<link:linkbase \n',
            '    xsi:schemaLocation="\n',
            '    http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd \n',
            '    http://xbrl.org/2008/generic http://www.xbrl.org/2008/generic-link.xsd \n',
            '    http://xbrl.org/2008/assertion/value http://www.xbrl.org/2008/value-assertion.xsd \n',
            '    http://xbrl.org/2008/variable http://www.xbrl.org/2008/variable.xsd \n',
            '    http://xbrl.org/2010/message http://www.xbrl.org/2010/generic-message.xsd" \n',
            '    xmlns:adc="http://www.xbrl.jp/audit-data-collection" \n',
            '    xmlns:xlink="http://www.w3.org/1999/xlink" \n',
            '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \n',
            '    xmlns:link="http://www.xbrl.org/2003/linkbase" \n',
            '    xmlns:va="http://xbrl.org/2008/assertion/value" \n',
            '    xmlns:gen="http://xbrl.org/2008/generic" \n',
            '    xmlns:variable="http://xbrl.org/2008/variable" \n',
            '    xmlns:msg="http://xbrl.org/2010/message">\n',
            '    <link:arcroleRef arcroleURI="http://xbrl.org/arcrole/2010/assertion-unsatisfied-message" xlink:type="simple" xlink:href="http://www.xbrl.org/2010/validation-message.xsd#assertion-unsatisfied-message"/>\n',
            '    <link:arcroleRef arcroleURI="http://xbrl.org/arcrole/2010/assertion-satisfied-message" xlink:type="simple" xlink:href="http://www.xbrl.org/2010/validation-message.xsd#assertion-satisfied-message"/>\n',
            '    <link:roleRef roleURI="http://www.xbrl.org/2010/role/message" xlink:type="simple" xlink:href="http://www.xbrl.org/2010/generic-message.xsd#standard-message"/>\n',
            '    <link:arcroleRef arcroleURI="http://xbrl.org/arcrole/2008/variable-set" xlink:type="simple" xlink:href="http://www.xbrl.org/2008/variable.xsd#variable-set"/>\n',
            '    <link:roleRef roleURI="http://www.xbrl.org/2008/role/link" xlink:type="simple" xlink:href="http://www.xbrl.org/2008/generic-link.xsd#standard-link-role"/>\n',
            '    <gen:link xlink:type="extended" xlink:role="http://www.xbrl.org/2008/role/link">\n'
        ]

        for link_id,primarykey in primaryKeys.items():
            key1 = ''
            key2 = ''
            key3 = ''
            keyA = primarykey[:4]
            if minKey <= keyA and keyA <= maxKey:
                num = primarykey[-3:]
                if 4==len(link_id):
                    key1 = keyA
                    lines_assertion = mandatoryAssertion(key1,key2,key3,num)
                    lines += lines_assertion  
                else:
                    keyB = primarykey[5:9]
                    key1 = keyA
                    key2 = keyB
                    lines_assertion = mandatoryAssertion(key1,key2,key3,num)
                    lines += lines_assertion
                keysX = list(set([k[:4] for k,v in targetRefDict.items() if v==keyA]))
                for keyX in keysX:
                    key1 = ''
                    key2 = ''
                    key3 = ''
                    if 4==len(primarykey):
                        key1 = keyX
                        key2 = keyA
                        lines_assertion = mandatoryAssertion(key1,key2,key3,num)
                        lines += lines_assertion
                        keysY = list(set([k[:4] for k,v in targetRefDict.items() if v==keyX]))
                        for keyY in keysY:
                            key1 = keyY
                            key2 = keyX
                            key3 = keyA
                            lines_assertion = mandatoryAssertion(key1,key2,key3,num)
                            lines += lines_assertion
                    else:
                        if re.match(r'A[0-9]{3}-A[0-9]{3}',primarykey):
                            keyB = primarykey[5:9]
                        else:
                            keyB = ''
                        key1 = keyX
                        key2 = keyA
                        key3 = keyB
                        lines_assertion = mandatoryAssertion(key1,key2,key3,num)
                        lines += lines_assertion

        lines.append('    </gen:link>\n')
        lines.append('</link:linkbase>\n')

        core_for_file = file_path(f'{xbrl_base}{core_for_Mandatory}-{module}.xml')
        with open(core_for_file, 'w', encoding='utf_8', newline='') as f:
            f.writelines(lines)
        if VERBOSE:
            print(f'-- {core_for_file}')
    #
    # save and restore saved primaryKeys
    #
    # pk_file = file_path(f'{xbrl_base}{primarykey_file}')
    # with open(pk_file, 'w', encoding='utf_8', newline='') as f:
    #     f.writelines(primaryKeys.values())
    # if VERBOSE:
    #     print(f'-- {pk_file}')
    #
    # primaryKeys = []
    # primary_key_file = file_path(f'{xbrl_source}{primary_key}')
    # with open(primary_key_file, encoding='utf_8', newline='') as f:
    #     lines = f.readlines()
    #     primaryKeys = [x.strip() for x in lines]
    #     primaryKeys = [x for x in primaryKeys if x]
    minBase = 'A999'
    maxBase = 'A000'
    minGL = 'A999'
    maxGL = 'A000'
    minO2C = 'A999'
    maxO2C = 'A000'
    minP2P = 'A999'
    maxP2P = 'A000'
    minCore = 'A999'
    maxCore = 'A000'
    for adc_id,record in adcDict.items():
        module = record['module']
        kind = record['kind']
        if 'ABIE'!=kind:
            continue
        if 'Base'==module:
            if adc_id < minBase: minBase = adc_id
            if adc_id > maxBase: maxBase = adc_id
        elif 'GL'==module:
            if adc_id < minGL: minGL = adc_id
            if adc_id > maxGL: maxGL = adc_id
        elif module in ['AR','Sales']:
            if adc_id < minO2C: minO2C = adc_id
            if adc_id > maxO2C: maxO2C = adc_id
        elif module in ['AP','Purchase']:
            if adc_id < minP2P: minP2P = adc_id
            if adc_id > maxP2P: maxP2P = adc_id
        elif 'Core'==module:
            if adc_id < minCore: minCore = adc_id
            if adc_id > maxCore: maxCore = adc_id

    assertionDefined = set()
    writePrimaryFormula(minBase,maxBase,'Base')
    writePrimaryFormula(minGL,maxGL,'GL')
    writePrimaryFormula(minO2C,maxO2C,'O2C')
    writePrimaryFormula(minP2P,maxP2P,'P2P')
    writePrimaryFormula(minCore,maxCore,'Core')

    assertionDefined = set()
    writeMandatoryFormula(minBase,maxBase,'Base')
    writeMandatoryFormula(minGL,maxGL,'GL')
    writeMandatoryFormula(minO2C,maxO2C,'O2C')
    writeMandatoryFormula(minP2P,maxP2P,'P2P')
    writeMandatoryFormula(minCore,maxCore,'Core')

    print('** END **')