#!/usr/bin/python
# -*- coding: utf-8 -*-

from xml.dom.minidom import getDOMImplementation, parseString
from Products.CMFPlomino.PlominoDesignManager import plomino_schemas, extra_schema_attributes

#def exportElementAsXML(form, prefix=''):

#    db = form.getParentDatabase()

#    impl = getDOMImplementation()
#    xmlform = impl.createDocument(None, "plominoform", None)

#    xml = db.exportElementAsXML(xmlform, form, isDatabase=False)

#    return xml

def exportElementAsXML(obj, xmldoc=None):
    """
    """
    
    if not xmldoc:
        impl = getDOMImplementation()
        xmldoc = implself.createDocument(None, "plominoform", None)
    
    isDatabase=False
    if isDatabase:
        node = xmldoc.createElement('dbsettings')
        schema = sys.modules[self.__module__].schema
    else:
        node = xmldoc.createElement('element')
        node.setAttribute('id', obj.id)
        node.setAttribute('type', obj.Type())
        title = obj.title
        node.setAttribute('title', title)
        schema = plomino_schemas[obj.Type()]

    for f in schema.fields():
        fieldNode = xmldoc.createElement(f.getName())
        field_type = f.getType()
        fieldNode.setAttribute('type', field_type)
        v = f.get(obj)
        if v is not None:
            if field_type=="Products.Archetypes.Field.TextField":
                text = xmldoc.createCDATASection(f.getRaw(obj).decode('utf-8'))
            else:
                text = xmldoc.createTextNode(str(f.get(obj)))
            fieldNode.appendChild(text)
        node.appendChild(fieldNode)

    # add AT standard extra attributes
    for extra in extra_schema_attributes:
        f = obj.Schema().getField(extra)
        if f is not None:
            fieldNode = xmldoc.createElement(extra)
            field_type = f.getType()
            fieldNode.setAttribute('type', field_type)
            v = f.get(obj)
            if v is not None:
                if field_type=="Products.Archetypes.Field.TextField":
                    text = xmldoc.createCDATASection(f.getRaw(obj).decode('utf-8'))
                else:
                    text = xmldoc.createTextNode(str(f.get(obj)))
                fieldNode.appendChild(text)
            node.appendChild(fieldNode)
#        
    if obj.Type() == "PlominoField":
        adapt = obj.getSettings()
        if adapt is not None:
            items = {}
            for k in adapt.parameters.keys():
                if hasattr(adapt, k):
                    items[k] = adapt.parameters[k]
            #items = dict(adapt.parameters)
            if len(items)>0:
                # export field settings
                str_items = xmlrpclib.dumps((items,), allow_none=1)
                try: 
                    dom_items = parseString(str_items)
                except ExpatError:
                    dom_items = parseString(escape_xml_illegal_chars(str_items))
                node.appendChild(dom_items.documentElement)
    if not isDatabase:
        elementslist = obj.objectIds()
        if len(elementslist)>0:
            elements = xmldoc.createElement('elements')
            for id in elementslist:
                elementNode = exportElementAsXML(getattr(obj, id), xmldoc=xmldoc)
                elements.appendChild(elementNode)
            node.appendChild(elements)

    if isDatabase:
       acl = xmldoc.createElement('acl')
       acl.setAttribute('AnomynousAccessRight', obj.AnomynousAccessRight)
       acl.setAttribute('AuthenticatedAccessRight', obj.AuthenticatedAccessRight)
       str_UserRoles = xmlrpclib.dumps((obj.UserRoles,), allow_none=1)
       dom_UserRoles = parseString(str_UserRoles)
       dom_UserRoles.firstChild.setAttribute('id', 'UserRoles')
       acl.appendChild(dom_UserRoles.documentElement)
       str_SpecificRights = xmlrpclib.dumps((obj.getSpecificRights(),), allow_none=1)
       dom_SpecificRights = parseString(str_SpecificRights)
       dom_SpecificRights.firstChild.setAttribute('id', 'SpecificRights')
       acl.appendChild(dom_SpecificRights.documentElement)
       node.appendChild(acl)
       node.setAttribute('version', obj.plomino_version)

    subscribers = component.subscribers((obj,), IXMLImportExportSubscriber)
    for subscriber in subscribers:
        name = subscriber.__module__ + '.' + subscriber.__class__.__name__
        doc = parseString(subscriber.export_xml())
        customnode = doc.childNodes[0]
        customnode.setAttribute("ExportImportClass", name)
        wrapper = doc.createElement("CustomData")
        wrapper.appendChild(customnode)
        node.appendChild(wrapper)
    return node


