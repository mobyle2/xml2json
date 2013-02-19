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
<e/>                             "e": null
                                 {"#tag":"e"}
<e>text</e>                      "e": "text"
                                 {"#tag":"e", "#children":["text"]}
<e name="value" />               "e": { "@name": "value" }
                                 {"#tag":"e", "@name":"value"}
<e name="value">text</e>         "e": { "@name": "value", "#text": "text" }
                                 {"#tag":"e", "@name":"value", "#children":["text"]}
<e> <a>text</a ><b>text</b> </e> "e": { "#contents": [{"#tag":"a","#contents":"text"}, "b": "text" }
                                 {"#tag":"e", "#children": [{"#tag":"a","#children":["text"]},{"#tag":"b","#children":["text"]}]}
<e> <a>text</a> <a>text</a> </e> "e": { "a": ["text", "text"] }
                                 {"#tag":"e", "#children": [{"#tag":"a","#children":["text"]},{"#tag":"a","#children":["text"]}]}
<e> text <a>text</a> </e>        "e": { "#text": "text", "a": "text" }
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
import simplejson, optparse, sys, os

#class AccessibleDict(dict):
#
#    def getu(self, key, default=None):
#        try:
#            return dict.__getitem__(self, key)
#        except KeyError:
#            val = [value['#children'] for value in dict.__getitem__(self, "#children") if isinstance(value, dict) and value['#tag']==key]
#            if len(val)>1:
#                return val
#            elif len(val)==1:
#                val[0][0] if len(val[0])==1 else val[0]
#            else:
#                return default

def elem_to_internal(elem,strip=1):
    """
    Convert an Element into an internal dictionary (not JSON!).
    :param elem: the element to be parsed
    :type elem: Element
    :param strip: flag to indicate wether the leading/trailing whitespaces should be ignored during parsing
    :type strip: bool
    :returns: the result of the parsing as a dictionary entry in the following form: {[element tag name]:[result of the parsing of the contents]}.
    :rtype: dict
    """
    d = {}
    d['#tag']=elem.tag
    for key, value in elem.attrib.items():
        d['@'+key] = value
    d['#children']=[]
    if elem.text is not None:
        text = elem.text.strip() if strip else elem.text
        if text != '':
            d['#children'].append(text)
    # loop over subelements to merge them
    for subelem in elem:
        d['#children'].append(elem_to_internal(subelem,strip=strip))
        if subelem.tail is not None:
            text = subelem.tail.strip() if strip else subelem.tail
            if text != '':
                d['#children'].append(text)
    return d


def internal_to_elem(pfsh, factory=ET.Element):

    """Convert an internal dictionary (not JSON!) into an Element.

    Whatever Element implementation we could import will be
    used by default; if you want to use something else, pass the
    Element class as the factory parameter.
    """

    attribs = {}
    text = None
    tail = None
    sublist = []
    tag = pfsh.keys()
    if len(tag) != 1:
        raise ValueError("Illegal structure with multiple tags: %s" % tag)
    tag = tag[0]
    value = pfsh[tag]
    if isinstance(value, dict):
        for k, v in value.items():
            if k[:1] == "@":
                attribs[k[1:]] = v
            elif k == "#text":
                text = v
            elif k == "#tail":
                tail = v
            elif isinstance(v, list):
                for v2 in v:
                    sublist.append(internal_to_elem({k:v2}, factory=factory))
            else:
                sublist.append(internal_to_elem({k:v}, factory=factory))
    else:
        text = value
    e = factory(tag, attribs)
    for sub in sublist:
        e.append(sub)
    e.text = text
    e.tail = tail
    return e


def elem2json(elem, strip=1, list_elems=[]):
    """
    Convert an ElementTree or Element into a JSON string.
    :param elem: the element to be parsed
    :type elem: Element
    :param strip: flag to indicate wether the leading/trailing whitespaces should be ignored during parsing
    :type strip: bool
    :param list_elems: the list of element names for which the subelements' order should be kept. 
    :type elem: list
    :returns: the result of the parsing as a JSON string.
    :rtype: JSON
    """

    if hasattr(elem, 'getroot'):
        elem = elem.getroot()
    return simplejson.dumps(elem_to_internal(elem, strip=strip, list_elems=[]))


def json2elem(json, factory=ET.Element):

    """Convert a JSON string into an Element.

    Whatever Element implementation we could import will be used by
    default; if you want to use something else, pass the Element class
    as the factory parameter.
    """

    return internal_to_elem(simplejson.loads(json), factory)


def xml2json(xmlstring, strip=1):

    """Convert an XML string into a JSON string."""

    elem = ET.fromstring(xmlstring)
    return elem2json(elem, strip=strip)


def json2xml(json, factory=ET.Element):

    """Convert a JSON string into an XML string.

    Whatever Element implementation we could import will be used by
    default; if you want to use something else, pass the Element class
    as the factory parameter.
    """

    elem = internal_to_elem(simplejson.loads(json), factory)
    return ET.tostring(elem)


def main():
    p = optparse.OptionParser(
        description='Converts XML to JSON or the other way around',
        prog='xml2json',
        usage='%prog -t xml2json -o file.json file.xml'
    )
    p.add_option('--type', '-t', help="'xml2json' or 'json2xml'")
    p.add_option('--out', '-o', help="Write to OUT instead of stdout")
    options, arguments = p.parse_args()

    if len(arguments) == 1:
        input = open(arguments[0]).read()
    else:
        p.print_help()
        sys.exit(-1)

    if (options.type == "xml2json"):
        out = xml2json(input, strip=0)
    else:
        out = json2xml(input)

    if (options.out):
        file = open(options.out, 'w')
        file.write(out)
        file.close()
    else:
        print out

if __name__ == "__main__":
    main()
