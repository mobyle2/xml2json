XML2JSON
========

Python script converts XML to JSON or the other way around

Usage
-----
Make this executable

    $ chmod +x xml2json

Then invoke it from the command line like this

    $ xml2json -t xml2json -o file.json file.xml

Or the other way around

    $ xml2json -t json2xml -o file.xml file.json

Without the `-o` parameter `xml2json` writes to stdout

    $ xml2json -t json2xml file.json

More info
---------
Relies on ElementTree for the XML parsing.  This is based on
pesterfish.py but uses a different XML->JSON mapping.
The XML -> JSON mapping is described [here](http://www.xml.com/pub/a/2006/05/31/converting-between-xml-and-json.html)

* Rewritten to a command line utility by [Hay Kranen](http://www.haykranen.nl) with contributions from George Hamilton (gmh04) and Dan Brown (jdanbrown)
* Fork it on [Github](http://github.com/hay/xml2json)

<pre>
XML                              JSON
&lt;e/&gt;                             "e": null
&lt;e&gt;text&lt;/e&gt;                      "e": "text"
&lt;e name="value" /&gt;               "e": { "@name": "value" }
&lt;e name="value"&gt;text&lt;/e&gt;         "e": { "@name": "value", "#text": "text" }
&lt;e&gt; &lt;a&gt;text&lt;/a &gt;&lt;b&gt;text&lt;/b&gt; &lt;/e&gt; "e": { "a": "text", "b": "text" }
&lt;e&gt; &lt;a&gt;text&lt;/a&gt; &lt;a&gt;text&lt;/a&gt; &lt;/e&gt; "e": { "a": ["text", "text"] }
&lt;e&gt; text &lt;a&gt;text&lt;/a&gt; &lt;/e&gt;        "e": { "#text": "text", "a": "text" }
</pre>

This is very similar to the mapping used for [Yahoo Web Services](http://developer.yahoo.com/common/json.html#xml)

This is a mess in that it is so unpredictable -- it requires lots of testing (e.g. to see if values are lists or strings or dictionaries).  For use in Python this could be vastly cleaner.  Think about whether the internal form can be more self-consistent while maintaining good external characteristics for the JSON.

Look at the Yahoo version closely to see how it works.  Maybe can adopt that completely if it makes more sense...

R. White, 2006 November 6