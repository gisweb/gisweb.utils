#!/usr/bin/python
# -*- coding: utf-8 -*-

from xml.dom.minidom import getDOMImplementation

def exportElementAsXML(form, prefix=''):

    db = plominoForm.getParentDatabase()

    impl = getDOMImplementation()
    xmlform = impl.createDocument(None, "plominoform", None)

    xml = db.exportElementAsXML(self, xmlform, form, isDatabase=False)

    return xml
