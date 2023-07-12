import xml.etree.ElementTree as ET
import sys
import csv

def walk_tree(node, path):
    for child in node:
        prefix = child.tag.split('}')[0].strip('{')
        local_name = child.tag.split('}')[-1]
        
        prefix_keys = [k for k, v in ns_map.items() if v == prefix]
        if prefix_keys:
            prefix_key = prefix_keys[0]
            child_path = f"{path}/{prefix_key}:{local_name}"
            xpaths.append((child_path, child.text))
            walk_tree(child, child_path)
        else:
            print(f"Warning: Namespace prefix not found for {prefix}. Skipping this element.")

def generate_xpaths_from_file(file):
    tree = ET.parse(file)
    root = tree.getroot()
    walk_tree(root, '')
    return xpaths

def save_to_csv(xpaths, output_file):
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['XPath', 'Value'])
        for xpath, value in xpaths:
            writer.writerow([xpath, value])

if __name__ == "__main__":    
    xml_file = 'XMLinstances/0001-20090405-255-14-1-489.xml'  # Replace with the path to your XML file
    # xml_file = 'gl-test.xml'
    output_file = 'output.csv'
    
    ns_map = {
        'ISO4217': "http://www.xbrl.org/2003/iso4217",
        'gl-bus': "http://www.xbrl.org/taxonomy/int/gl/bus/2003-08-29/",
        'gl-cor': "http://www.xbrl.org/taxonomy/int/gl/cor/2003-08-29/",
        'gl-muc': "http://www.xbrl.org/taxonomy/int/gl/muc/2003-08-29/",
        'gl-plt': "http://www.xbrgl.com/gl-plt/",
        'gl-usk': "http://www.xbrl.org/taxonomy/int/gl/usk/2003-08-29/",
        'link': "http://www.xbrl.org/2001/XLink/xbrllinkbase",
        'tdb': "www.tdb.co.jp",
        'xbrli': "http://www.xbrl.org/2001/instance",
        'xhtml': "http://www.w3.org/1999/xhtml",
        'xsi': "http://www.w3.org/2001/XMLSchema-instance",
        # ... the rest of the namespaces
    }
    
    xpaths = []
    xpath_values = generate_xpaths_from_file(xml_file)
    save_to_csv(xpath_values, output_file)
    print(f"XPath values saved to {output_file}")
