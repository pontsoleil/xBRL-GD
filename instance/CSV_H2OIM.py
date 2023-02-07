#!/usr/bin/env python3
# coding: utf-8
#
# generate Audit Data Collection OIM-CSV fron CSV file generated from XBRL-GL instance
#
# designed by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)
# written by SAMBUICHI, Nobuyuki (Sambuichi Professional Engineers Office)
#
# MIT License
#
# (c) 2022 SAMBUICHI Nobuyuki (Sambuichi Professional Engineers Office)
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

# from cgi import print_directory
import re
import json
import os
import csv

DEBUG = True
VERBOSE = True
SEP = os.sep

source = './'
gl_instanceFile  = 'xbrl-instances0_H.csv'
adc_instanceFile = 'adc-instances0_H.csv'
adc_instanceMeta = 'adc-instances0_H.json'


def file_path(pathname):
    if SEP == pathname[0:1]:
        return pathname
    else:
        pathname = pathname.replace('/',SEP)
        dir = os.path.dirname(__file__)
        new_path = os.path.join(dir, pathname)
        return new_path

if __name__ == '__main__':
    glInstances = []
    gl_instance_file = f'{source}{gl_instanceFile}'.replace('/',SEP)
    gl_instance_file = file_path(gl_instance_file)
    with open(gl_instance_file, encoding='utf_8', newline='') as f:
        reader = csv.reader(f)
        header = next(reader) 
        header[0] = header[0].replace('\ufeff','')
        header2 = next(reader)

    with open(gl_instance_file, encoding='utf_8', newline='') as f:
        reader = csv.DictReader(f, fieldnames=header)
        content = [row for row in reader]

    d_GL02 = None
    i = 0
    records = []
    for data in content:
        if i < 1:
            i += 1
            continue
        if not re.match(r'[\-0-9]+',data['d_GL02']):
            continue
        if d_GL02!=data['d_GL02']:
            ectryDetail = 0
            accountSub = 0
            d_GL02 = data['d_GL02']
        if 'cor:entryDetail' in str(data['d_GL03']):
            if not 'cor:accountSub' in str(data['d_BS01']):
                ectryDetail += 1
                accountSub = 0
            data['d_GL03'] = ectryDetail
        else:
            data['d_GL03'] = '' 
        if 'cor:accountSub' in str(data['d_BS01']):
            accountSub += 1
            data['d_BS01'] = accountSub
        else:
            data['d_BS01'] = ''
        records.append(data)

    records2 = []
    # header2 = header[:6]+header[8:10]+header[16:21]+header[22:33]+header[34:]
    header2 = ['d_GL02','d_GL03','d_BS01','GL02-001','GL02-002','GL02-005','GL02-006','GL02-007','GL03-001','GL03-002','GL03-003','GL03-004','GL03-005','GL03-006','GL03-007','BS09-001','BS09-002','BS09-003','BS09-005','BS09-006','BS09-007','CM07-001','CM08-001','CM01-001','CM01-002','BS01-001','BS01-002','BS01-004']
    if DEBUG:
        print(header2)
    for data in records:
        record = {}
        if not data['BS01-001']:
            if data['d_BS01']:
                for k,v in data.items():
                    if not k in header2:
                        continue
                    if k in ['d_GL02','d_GL03','d_BS01']:
                        record[k] = str(v)
                    elif 'BS01-001' == k:
                        record['BS01-001'] = data['Q']
                    elif 'BS01-002' == k:
                        record['BS01-002'] = data['GL02-BS01-002']
                    elif 'BS01-003' == k:
                        record['BS01-003'] = 'account sub'
                    elif 'BS01-004' == k:
                        record['BS01-004'] = data['R']
                    else:
                        record[k] = str(v)
            else:
                for k,v in data.items():
                    if not k in header2:
                        continue
                    record[k] = str(v)
            records2.append(record)
        else:
            for k,v in data.items():
                if not k in header2:
                    continue
                # if k in ['d_GL02','d_GL03','d_BS01','BS01-001','BS01-002','BS01-004']:
                #     record[k] = str(v)
                # el
                if k=='BS01-003':
                    record[k] = 'trading partner'                 
                else:
                    record[k] = str(v)
            records2.append(record)

    adc_instance_file = f'{source}{adc_instanceFile}'.replace('/',SEP)
    adc_instance_file = file_path(adc_instance_file)
    with open(adc_instance_file, 'w', encoding='utf_8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=header2)
        writer.writeheader()
        writer.writerows(records2)

    metadata = {
        "documentInfo": {
            "documentType": "https://xbrl.org/2021/xbrl-csv",
            "namespaces": {
                "adc": "http://www.xbrl.jp/audit-data-collection",
                "ns0": "http://www.example.com",
                "link": "http://www.xbrl.org/2003/linkbase",
                "iso4217": "http://www.xbrl.org/2003/iso4217",
                "xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "xbrli": "http://www.xbrl.org/2003/instance",
                "xbrldi": "http://xbrl.org/2006/xbrldi",
                "xlink": "http://www.w3.org/1999/xlink"
            },
            "taxonomy": [
                "../taxonomy/H/core.xsd"
            ]
        },
        "tableTemplates": {
            "adc": {
                "columns": {
                    "d_GL02": {},
                    "d_GL03": {},
                    "d_BS01": {}
                },
                "dimensions": {
                    "adc:d_GL02": "$d_GL02",
                    "adc:d_GL03": "$d_GL03",
                    "adc:d_BS01": "$d_BS01",
                    "period": "2023-11-01T00:00:00",
                    "entity": "ns0:Example Co."
                }
            }
        },
        "tables": {
            "adc": {
                "url": adc_instanceFile
            }
        }
    }

    print(records2[0].keys())

    for id in records2[0].keys():
        if not id in ['d_GL02','d_GL03','d_BS01']:
            metadata['tableTemplates']['adc']['columns'][id] = {"dimensions": {"concept": f"adc:{id}"}}
            if id =='A026-A089-001':
                metadata['tableTemplates']['adc']['columns'][id]['dimensions']['unit'] = 'iso4217:JPY'
                
    print(json.dumps(metadata))

    adc_instance_meta = f'{source}{adc_instanceMeta}'.replace('/',SEP)
    adc_instance_meta = file_path(adc_instance_meta)
    with open(adc_instance_meta, 'w') as f:
        json.dump(metadata, f, indent=4)

    if DEBUG:
        print(f'output file {adc_instance_file} {adc_instance_meta}')
        print('** END **')
