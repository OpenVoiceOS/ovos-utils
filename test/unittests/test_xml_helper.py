# Copyright 2024, OpenVoiceOS
# Licensed under the Apache License, Version 2.0

import os
import tempfile
import unittest

from ovos_utils.xml_helper import etree2dict, xml2dict, dict2xml, load_xml2dict


class TestEtree2Dict(unittest.TestCase):
    def _make_element(self, tag, text=None, attrib=None, children=None):
        from xml.etree import cElementTree as ET
        el = ET.Element(tag, attrib=attrib or {})
        if text is not None:
            el.text = text
        for child in (children or []):
            el.append(child)
        return el

    def test_simple_text_element(self):
        el = self._make_element("name", text="Alice")
        result = etree2dict(el)
        self.assertEqual(result, {"name": "Alice"})

    def test_element_with_attrib(self):
        el = self._make_element("item", attrib={"id": "1"})
        result = etree2dict(el)
        self.assertIn("item", result)
        self.assertEqual(result["item"]["id"], "1")

    def test_nested_children(self):
        from xml.etree import cElementTree as ET
        parent = ET.Element("root")
        child = ET.SubElement(parent, "child")
        child.text = "value"
        result = etree2dict(parent)
        self.assertIn("root", result)
        self.assertIn("child", result["root"])

    def test_multiple_same_tag_children(self):
        from xml.etree import cElementTree as ET
        parent = ET.Element("root")
        for i in range(3):
            c = ET.SubElement(parent, "item")
            c.text = str(i)
        result = etree2dict(parent)
        self.assertIsInstance(result["root"]["item"], list)
        self.assertEqual(len(result["root"]["item"]), 3)

    def test_element_with_text_and_attrib(self):
        el = self._make_element("node", text="hello", attrib={"x": "1"})
        result = etree2dict(el)
        self.assertEqual(result["node"]["text"], "hello")
        self.assertEqual(result["node"]["x"], "1")

    def test_empty_element(self):
        el = self._make_element("empty")
        result = etree2dict(el)
        self.assertEqual(result, {"empty": None})


class TestXml2Dict(unittest.TestCase):
    def test_basic_xml(self):
        xml = "<root><name>Alice</name></root>"
        result = xml2dict(xml)
        self.assertIn("root", result)

    def test_invalid_xml_returns_empty(self):
        result = xml2dict("not xml at all!!!")
        self.assertEqual(result, {})

    def test_xmlns_stripped(self):
        xml = '<root xmlns="http://www.w3.org/1999/xhtml"><child>text</child></root>'
        result = xml2dict(xml)
        self.assertIn("root", result)

    def test_attributes_in_xml(self):
        xml = '<item id="42">value</item>'
        result = xml2dict(xml)
        self.assertIn("item", result)

    def test_nested_xml(self):
        xml = "<root><a><b>deep</b></a></root>"
        result = xml2dict(xml)
        self.assertIn("root", result)


class TestDict2Xml(unittest.TestCase):
    def test_simple_dict(self):
        d = {"text": "hello"}
        xml = dict2xml(d)
        self.assertIn("<xml>", xml)
        self.assertIn("</xml>", xml)
        self.assertIn("hello", xml)

    def test_custom_root(self):
        d = {"text": "value"}
        xml = dict2xml(d, root="myroot")
        self.assertIn("<myroot>", xml)
        self.assertIn("</myroot>", xml)

    def test_string_attr(self):
        d = {"color": "red", "text": "hello"}
        xml = dict2xml(d)
        self.assertIn("color", xml)
        self.assertIn("red", xml)

    def test_nested_dict(self):
        d = {"child": {"text": "nested"}}
        xml = dict2xml(d)
        self.assertIn("<child>", xml)
        self.assertIn("nested", xml)

    def test_list_values(self):
        d = {"items": [{"text": "a"}, {"text": "b"}]}
        xml = dict2xml(d)
        self.assertIn("<items>", xml)


class TestLoadXml2Dict(unittest.TestCase):
    def test_load_from_file(self):
        xml_content = "<xml><name>test</name></xml>"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            tmp_path = f.name
        try:
            result = load_xml2dict(tmp_path)
            self.assertIn("name", result)
        finally:
            os.unlink(tmp_path)

    def test_load_nested_from_file(self):
        xml_content = "<xml><section><item>value</item></section></xml>"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            tmp_path = f.name
        try:
            result = load_xml2dict(tmp_path)
            self.assertIn("section", result)
        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main()
