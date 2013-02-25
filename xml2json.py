#!/usr/bin/env python
"""
xml2json.py  Convert XML to JSON

Forked from http://github.com/hay/xml2json

The aim of this fork is to preserve the order of XML subelements.

Relies on ElementTree for the XML parsing.  This is based on
pesterfish.py but uses a different XML->JSON mapping.
The XML->JSON mapping is described at
http://www.xml.com/pub/a/2006/05/31/converting-between-xml-and-json.html

Rewritten to a command line utility by Hay Kranen < github.com/hay > with
contributions from George Hamilton (gmh04) and Dan Brown (jdanbrown)

XML                              JSON
<e/>                             {"#tag":"e"}
<e>text</e>                      {"#tag":"e", "#children":["text"]}
<e name="value" />               {"#tag":"e", "@name":"value"}
<e name="value">text</e>         
   {"#tag":"e", "@name":"value", "#children":["text"]}
<e> <a>text</a ><b>text</b> </e> 
   {"#tag":"e", "#children": [{"#tag":"a","#children":["text"]},
                              {"#tag":"b","#children":["text"]}]}
<e> <a>text</a> <a>text</a> </e> 
   {"#tag":"e", "#children": [{"#tag":"a","#children":["text"]},
                              {"#tag":"a","#children":["text"]}]}
<e> text <a>text</a> </e>        
   {"#tag":"e", "#children": ["text",{"#tag":"a","#children":["text"]}]}

This is very similar to the mapping used for Yahoo Web Services
(http://developer.yahoo.com/common/json.html#xml).

This is a mess in that it is so unpredictable -- it requires lots of testing
(e.g. to see if values are lists or strings or dictionaries).  For use
in Python this could be vastly cleaner.  Think about whether the internal
form can be more self-consistent while maintaining good external characteristics
for the JSON.

Look at the Yahoo version closely to see how it works.  Maybe can adopt
that completely if it makes more sense...

R. White, 2006 November 6
"""

import xml.etree.cElementTree as ET
import simplejson, optparse, sys

def elem_to_internal(elem, strip=1):
    """
    Convert an Element into an internal dictionary (not JSON!).
    :param elem: the element to be parsed
    :type elem: Element
    :param strip: flag to indicate wether the leading/trailing whitespaces 
                  should be ignored during parsing
    :type strip: bool
    :returns: the result of the parsing as a dictionary entry in the following
              form: {[element tag name]:[result of the parsing of the contents]}.
    :rtype: dict
    """
    my_d = {}
    my_d['#tag'] = elem.tag
    for key, value in elem.attrib.items():
        my_d['@'+key] = value
    my_d['#children'] = []
    if elem.text is not None:
        text = elem.text.strip() if strip else elem.text
        if text != '':
            my_d['#children'].append(text)
    # loop over subelements to merge them
    for subelem in elem:
        my_d['#children'].append(elem_to_internal(subelem, strip=strip))
        if subelem.tail is not None:
            text = subelem.tail.strip() if strip else subelem.tail
            if text != '':
                my_d['#children'].append(text)
    return my_d


def internal_to_elem(pfsh, factory=ET.Element):

    """
    Convert an internal dictionary (not JSON!) into an Element.
    :param pfsh: the internal dictionary structure
    :type pfsh: dict
    :param factory: element factory which should be used. Whatever 
                    Element implementation we could import will be
                    used by default; if you want to use something else,
                    pass the Element class as the factory parameter.
    :type factory: ET.Element factory
    :returns: the ElementTree DOM structure for the XML.
    :rtype: ET.Element
    """
    my_el = factory(pfsh['#tag'], {key[1:]: value\
                    for (key, value) in pfsh.items() if key[0] == '@'})
    child_el = None
    for child in pfsh['#children']:
        if isinstance(child, basestring):
            if child_el is None:
                my_el.text = child
            else:
                child_el.tail = child
        else:
            child_el = internal_to_elem(child)
            my_el.append(child_el)
    return my_el

def elem2json(elem, strip=1):
    """
    Convert an ElementTree or Element into a JSON string.
    :param elem: the element to be parsed
    :type elem: Element
    :param strip: flag to indicate wether the leading/trailing whitespaces
                  should be ignored during parsing
    :type strip: bool
    :returns: the result of the parsing as a JSON string.
    :rtype: string
    """

    if hasattr(elem, 'getroot'):
        elem = elem.getroot()
    return simplejson.dumps(elem_to_internal(elem, strip=strip))


def json2elem(json, factory=ET.Element):
    """
    Convert a JSON string into an Element.
    :param pfsh: the JSON data
    :type pfsh: string
    :param factory: element factory which should be used. Whatever 
                    Element implementation we could import will be
                    used by default; if you want to use something else,
                    pass the Element class as the factory parameter.
    :type factory: ET.Element factory
    :returns: the ElementTree DOM structure for the XML.
    :rtype: ET.Element
    """

    return internal_to_elem(simplejson.loads(json), factory)


def xml2json(xmlstring, strip=1):
    """
    Convert an XML string into a JSON string.
    :param xmlstring: the XML string to be parsed
    :type xmlstring: string
    :param strip: flag to indicate wether the leading/trailing whitespaces
                  should be ignored during parsing
    :type strip: bool
    :returns: the result of the parsing as a JSON string.
    :rtype: string
    """

    elem = ET.fromstring(xmlstring)
    return elem2json(elem, strip=strip)


def json2xml(json, factory=ET.Element):
    """
    Convert a JSON string into an XML string.
    :param json: the JSON data
    :type json: string
    :param factory: element factory which should be used. Whatever 
                    Element implementation we could import will be
                    used by default; if you want to use something else,
                    pass the Element class as the factory parameter.
    :type factory: ET.Element factory
    :returns: the XML string
    :rtype: string
    """

    elem = internal_to_elem(simplejson.loads(json), factory)
    return ET.tostring(elem)


def main():
    """
    command line access for this module
    see options description below
    """
    opt = optparse.OptionParser(
        description='Converts XML to JSON or the other way around',
        prog='xml2json',
        usage='%prog -t xml2json -o file.json file.xml'
    )
    opt.add_option('--type', '-t', help="'xml2json' or 'json2xml'")
    opt.add_option('--out', '-o', help="Write to OUT instead of stdout")
    options, arguments = opt.parse_args()

    if len(arguments) == 1:
        my_input = open(arguments[0]).read()
    else:
        opt.print_help()
        sys.exit(-1)

    if (options.type == "xml2json"):
        out = xml2json(my_input, strip=0)
    else:
        out = json2xml(my_input)

    if (options.out):
        my_file = open(options.out, 'w')
        my_file.write(out)
        my_file.close()
    else:
        print out

if __name__ == "__main__":
    main()
