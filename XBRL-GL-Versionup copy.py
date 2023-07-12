import xml.etree.ElementTree as ET
import argparse
from collections import defaultdict
import re
import json
import os

namespace_mappings = {
    'xbrli': 'http://www.xbrl.org/2001/instance',
    'link': 'http://www.xbrl.org/2001/XLink/xbrllinkbase',
    'ISO4217': 'http://www.xbrl.org/2003/iso4217',
    'gl-bus': 'http://www.xbrl.org/int/gl/bus/2006-10-25',
    'gl-cor': 'http://www.xbrl.org/int/gl/cor/2006-10-25',
    'gl-muc': 'http://www.xbrl.org/int/gl/muc/2006-10-25',
    'gl-usk': 'http://www.xbrl.org/taxonomy/int/gl/usk/2003-08-29/',
    'gl-plt': 'http://www.xbrl.org/int/gl/plt/2006-10-25',
    'tdb': 'www.tdb.co.jp',
    'xhtml': 'http://www.w3.org/1999/xhtml',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}

namespace1_mappings = {
    'xbrli': 'http://www.xbrl.org/2001/instance',
    'xbrll': 'http://www.xbrl.org/2003/linkbase',
    'link': 'http://www.xbrl.org/2001/XLink/xbrllinkbase',
    'xlink': 'http://www.w3.org/1999/xlink',
    'iso4217': 'http://www.xbrl.org/2003/iso4217',
    'iso639': 'http://www.xbrl.org/2005/iso639',
    'gl-gen': 'http://www.xbrl.org/taxonomy/int/gl/gen/2003-08-29/',
    'gl-cor': 'http://www.xbrl.org/taxonomy/int/gl/cor/2003-08-29/',
    'gl-bus': 'http://www.xbrl.org/taxonomy/int/gl/bus/2003-08-29/',
    'gl-muc': 'http://www.xbrl.org/taxonomy/int/gl/muc/2003-08-29/',
    'gl-usk': 'http://www.xbrl.org/taxonomy/int/gl/usk/2003-08-29/',
    'gl-taf': 'http://www.xbrl.org/taxonomy/int/gl/taf/2003-08-29/',
    'gl-plt': 'http://www.xbrl.org/taxonomy/int/gl/plt/2003-08-29/',
    'xhtml': 'http://www.w3.org/1999/xhtml',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}

namespace2_mappings = {
    'xbrli': 'http://www.xbrl.org/2001/instance',
    'xbrll': 'http://www.xbrl.org/2003/linkbase',
    'link': 'http://www.xbrl.org/2001/XLink/xbrllinkbase',
    'xlink': 'http://www.w3.org/1999/xlink',
    'iso4217': 'http://www.xbrl.org/2003/iso4217',
    'iso639': 'http://www.xbrl.org/2005/iso639',
    'gl-gen': 'http://www.xbrl.org/int/gl/gen/2015-03-25',
    'gl-cor': 'http://www.xbrl.org/int/gl/cor/2015-03-25',
    'gl-bus': 'http://www.xbrl.org/int/gl/bus/2015-03-25',
    'gl-muc': 'http://www.xbrl.org/int/gl/muc/2015-03-25',
    'gl-usk': 'http://www.xbrl.org/int/gl/usk/2015-03-25',
    'gl-taf': 'http://www.xbrl.org/int/gl/taf/2015-03-25',
    'gl-srcd': 'http://www.xbrl.org/int/gl/srcd/2015-03-25',
    'gl-ehm': 'http://www.xbrl.org/int/gl/ehm/2015-03-25',
    'gl-plt': 'http://www.xbrl.org/int/gl/plt/2015-03-25',
    'xhtml': 'http://www.w3.org/1999/xhtml',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}

namespace3_mappings = {
    'xbrli': 'http://www.xbrl.org/2001/instance',
    'xbrll': 'http://www.xbrl.org/2003/linkbase',
    'link': 'http://www.xbrl.org/2001/XLink/xbrllinkbase',
    'xlink': 'http://www.w3.org/1999/xlink',
    'iso4217': 'http://www.xbrl.org/2003/iso4217',
    'iso639': 'http://www.xbrl.org/2005/iso639',
    'gl-gen': 'http://www.xbrl.org/int/gl/gen/2016-12-01',
    'gl-cor': 'http://www.xbrl.org/int/gl/cor/2016-12-01',
    'gl-bus': 'http://www.xbrl.org/int/gl/bus/2016-12-01',
    'gl-muc': 'http://www.xbrl.org/int/gl/muc/2016-12-01',
    'gl-usk': 'http://www.xbrl.org/int/gl/usk/2016-12-01',
    'gl-taf': 'http://www.xbrl.org/int/gl/taf/2016-12-01',
    'gl-srcd': 'http://www.xbrl.org/int/gl/srcd/2016-12-01',
    'gl-ehm': 'http://www.xbrl.org/int/gl/ehm/2016-12-01',
    'gl-plt': 'http://www.xbrl.org/int/gl/plt/2016-12-01',
    'xhtml': 'http://www.w3.org/1999/xhtml',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}

def extract_namespaces(element):
    # Extract namespaces from an element and its children recursively
    namespaces = {}
    if '}' in element.tag:
        tag_parts = element.tag.split('}')
        if len(tag_parts) == 2:
            prefix = tag_parts[0][1:]
            namespace = tag_parts[1]
            if prefix:
                namespaces[prefix] = namespace
    for child in element:
        child_namespaces = extract_namespaces(child)
        namespaces.update(child_namespaces)
    return namespaces

def modify_xml_files_in_directory(in_directory, out_directory):
    # Get a list of XML files in the directory
    xml_files = [file for file in os.listdir(in_directory) if file.endswith('.xml')]

    # Process each XML file
    for xml_file in xml_files:
        # Construct the input and output file paths
        input_file = os.path.join(in_directory, xml_file)
        output_file = os.path.join(out_directory, xml_file)

        # Modify XML namespaces
        modify_xml_namespaces(input_file, output_file)

def modify_xml_namespaces(xml_file, output_file):
    # parse XML document
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Convert XML to dictionary
    xml_dict = etree_to_dict(root)

    # Modify namespace definitions and element names
    xml_dict['{'+namespace_mappings['xbrli']+'}xbrl'] = xml_dict.pop('{'+namespace_mappings['xbrli']+'}group')
    xml_dict['{'+namespace_mappings['xbrli']+'}xbrl']['@xmlns:xbrli']   = namespace2_mappings['xbrli']
    xml_dict['{'+namespace_mappings['xbrli']+'}xbrl']['@xmlns:xbrll']   = namespace2_mappings['xbrll']
    xml_dict['{'+namespace_mappings['xbrli']+'}xbrl']['@xmlns:xlink']   = namespace2_mappings['xlink']
    xml_dict['{'+namespace_mappings['xbrli']+'}xbrl']['@xmlns:iso4217'] = namespace2_mappings['iso4217']
    xml_dict['{'+namespace_mappings['xbrli']+'}xbrl']['@xmlns:iso639']  = namespace2_mappings['iso639']
    xml_dict['{'+namespace_mappings['xbrli']+'}xbrl']['@xmlns:gl-cor']  = namespace2_mappings['gl-cor']
    xml_dict['{'+namespace_mappings['xbrli']+'}xbrl']['@xmlns:gl-muc']  = namespace2_mappings['gl-muc']
    xml_dict['{'+namespace_mappings['xbrli']+'}xbrl']['@xmlns:gl-bus']  = namespace2_mappings['gl-bus']
    xml_dict['{'+namespace_mappings['xbrli']+'}xbrl']['@xmlns:gl-usk']  = namespace2_mappings['gl-usk']
    xml_dict['{'+namespace_mappings['xbrli']+'}xbrl']['@xmlns:gl-taf']  = namespace2_mappings['gl-taf']
    xml_dict['{'+namespace_mappings['xbrli']+'}xbrl']['@xmlns:gl-srcd'] = namespace2_mappings['gl-srcd']
    xml_dict['{'+namespace_mappings['xbrli']+'}xbrl']['@xmlns:gl-ehm']  = namespace2_mappings['gl-ehm']
    xml_dict['{'+namespace_mappings['xbrli']+'}xbrl']['@xmlns:gl-plt']  = namespace2_mappings['gl-plt']

    txtJson = json.dumps(xml_dict)
    txtJson = re.sub('{'+namespace1_mappings['xbrli']+'}',  'xbrli:',  txtJson)
    txtJson = re.sub('{'+namespace1_mappings['gl-cor']+'}', 'gl-cor:', txtJson)
    txtJson = re.sub('{'+namespace1_mappings['gl-muc']+'}', 'gl-muc:', txtJson)
    txtJson = re.sub('{'+namespace1_mappings['gl-bus']+'}', 'gl-bus:', txtJson)
    txtJson = re.sub('{'+namespace1_mappings['gl-usk']+'}', 'gl-usk:', txtJson)
    txtJson = re.sub('{'+namespace1_mappings['gl-taf']+'}', 'gl-taf:', txtJson)
    txtJson = re.sub('{'+namespace1_mappings['gl-plt']+'}', 'gl-plt:', txtJson)
    txtJson = re.sub('gl-cor:xbrlElement', 'gl-cor:summaryReportingElement', txtJson)
    txtJson = re.sub('gl-cor:xbrlTaxonomy', 'gl-cor:summaryReportingTaxonomyIDRef', txtJson)

    dicJson = json.loads(txtJson)

    txtJson = re.sub('xbrli:',  '{'+namespace2_mappings['xbrli']+'}', txtJson)
    txtJson = re.sub('gl-cor:', '{'+namespace2_mappings['gl-cor']+'}', txtJson)
    txtJson = re.sub('gl-muc:', '{'+namespace2_mappings['gl-muc']+'}', txtJson)
    txtJson = re.sub('gl-bus:', '{'+namespace2_mappings['gl-bus']+'}', txtJson)
    txtJson = re.sub('gl-usk:', '{'+namespace2_mappings['gl-usk']+'}', txtJson)
    txtJson = re.sub('gl-taf:', '{'+namespace2_mappings['gl-taf']+'}', txtJson)
    txtJson = re.sub('gl-srcd:','{'+namespace2_mappings['gl-srcd']+'}',txtJson)
    txtJson = re.sub('gl-plt:', '{'+namespace2_mappings['gl-plt']+'}', txtJson)

    xml_dict2 = json.loads(txtJson)

    # # parse XML document
    # tree = ET.parse(xml_file)
    # root = tree.getroot()

    # Get the existing namespaces in the XML document
    namespaces = extract_namespaces(root)

    # Create the modified root element with the correct namespaces
    modified_root = ET.Element('{'+namespace3_mappings['xbrli']+'}xbrl',
                               attrib={
                                   'xmlns:xbrli': namespace2_mappings['xbrli'],
                                   'xmlns:xbrll': namespace2_mappings['xbrll'],
                                   'xmlns:link': namespace2_mappings['link'],
                                   'xmlns:xlink': namespace2_mappings['xlink'],
                                   'xmlns:iso4217': namespace2_mappings['iso4217'],
                                   'xmlns:iso639': namespace2_mappings['iso639'],
                                   'xmlns:gl-cor': namespace3_mappings['gl-cor'],
                                   'xmlns:gl-muc': namespace3_mappings['gl-muc'],
                                   'xmlns:gl-bus': namespace3_mappings['gl-bus'],
                                   'xmlns:gl-plt': namespace3_mappings['gl-plt'],
                                   'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                                   'xsi:schemaLocation': 'http://www.xbrl.org/int/gl/plt/2015-03-25 ../plt/case-c-b-m-u-t-s/gl-plt-2015-03-25.xsd'
                               })

    # Convert the modified dictionary back to XML
    # modified_xml = dict_to_etree(xml_dict2, modified_root)
    # modified_tree = ET.ElementTree(modified_xml)
    
    # Convert the modified dictionary back to XML
    # root = ET.XML('''
    # <xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance"
    #     xmlns:xbrll="http://www.xbrl.org/2003/linkbase" 
    #     xmlns:xlink="http://www.w3.org/1999/xlink"
    #     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    #     xmlns:gl-cor="http://www.xbrl.org/int/gl/cor/2006-10-25"
    #     xmlns:gl-muc="http://www.xbrl.org/int/gl/muc/2006-10-25"
    #     xmlns:gl-bus="http://www.xbrl.org/int/gl/bus/2006-10-25"
    #     xmlns:gl-plt="http://www.xbrl.org/int/gl/plt/2006-10-25"
    #     xmlns:iso4217="http://www.xbrl.org/2003/iso4217" 
    #     xmlns:iso639="http://www.xbrl.org/2005/iso639"
    #     xsi:schemaLocation="http://www.xbrl.org/int/gl/plt/2006-10-25 ../plt/case-c-b-m-u-t/gl-plt-2006-10-25.xsd" />
    # ''')
    modified_xml = dict_to_etree(xml_dict2,root)
    modified_tree = ET.ElementTree(modified_xml)

    # Save the modified XML to a file
    # modified_xml.write(output_file, encoding='utf-8', xml_declaration=True)
    with open(output_file, 'wb') as file:
        modified_tree.write(output_file, encoding='utf-8', xml_declaration=True)

def etree_to_dict(t):
    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        d = {t.tag: {k: v[0] if len(v) == 1 else v
                     for k, v in dd.items()}}
    if t.attrib:
        d[t.tag].update(('@' + k, v)
                        for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
                d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d

def dict_to_etree(d, root):
    def _to_etree(d, root):
        if not d:
            pass
        elif isinstance(d, str):
            root.text = d
        elif isinstance(d, dict):
            for k, v in d.items():
                assert isinstance(k, str)
                if k.startswith('#'):
                    try:
                        assert k == '#text' and isinstance(v, str)
                        root.text = v
                    except (Exception, ValueError, TypeError) as e:
                        print(e, v)
                elif k.startswith('@'):
                    if isinstance(v, str):  # 2021-06-05
                        root.set(k[1:], v)
                    else:
                        pass
                elif isinstance(v, list):
                    for e in v:
                        _to_etree(e, ET.SubElement(root, k))
                else:
                    _to_etree(v, ET.SubElement(root, k))
        else:
            assert d == 'invalid type', (type(d), d)

    assert isinstance(d, dict) and len(d) == 1
    tag, body = next(iter(d.items()))
    _to_etree(body, root)
    return root

def main():
    parser = argparse.ArgumentParser(description='Version up XBRL-GL from XBRL Spec 2.0a to 2.1')
    parser.add_argument('-i', dest='input_file', help='Input XML file')
    parser.add_argument('-o', dest='output_file', help='Output XML file')
    parser.add_argument('-d', dest='input_directory', help='Input directory containing XML files')
    parser.add_argument('-x', dest='output_directory', help='Output directory containing XML files')

    args = parser.parse_args()

    in_file = args.input_file
    out_file = args.output_file
    if in_file and out_file:
        in_file = in_file.strip()
        out_file = out_file.strip()
        modify_xml_namespaces(in_file, out_file)
        print(f"Modified XML file has been generated. {in_file} -> {out_file}")
    else:
        in_directory = args.input_directory
        out_directory = args.output_directory
        if not in_directory or not out_directory:
            parser.print_help()
            return
        in_directory = in_directory.strip()
        out_directory = out_directory.strip()

        modify_xml_files_in_directory(in_directory, out_directory)
        print(f"Modified XML file in '{in_directory}' has been generated in '{out_directory}'.")

if __name__ == '__main__':
    main()
