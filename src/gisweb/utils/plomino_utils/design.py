#!/usr/bin/python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import lxml.etree as etree
import os
from xml.dom.minidom import getDOMImplementation, parseString
from Products.CMFPlomino.PlominoDesignManager import plomino_schemas, extra_schema_attributes
import xmlrpclib
from zope import component
from Products.CMFPlomino.interfaces import IXMLImportExportSubscriber
from xml.parsers.expat import ExpatError
from Products.CMFPlomino.PlominoUtils import escape_xml_illegal_chars
from Products.CMFCore.utils import getToolByName

def rename(instring, **kw):
    outstring = ''
    for k,v in kw.items():
        toremove = '%s' % k
        if toremove in instring:
            toplace = '%s' % v
            outstring = instring.replace(toremove, toplace)
    return outstring

def duplicateForm(form, xmldoc, **kw):

    xmlout = ''
    for instring in [form.id] + [i.id for i in form.getFormFields]:
        outstring = rename(instring, **kw)
        xmlout = xmldoc.replace(instring, outstring)

    return xmlout

def exportElementAsXML(obj, xmldoc=None):
    """
    """

    if not xmldoc:
        impl = getDOMImplementation()
        xmldoc = impl.createDocument(None, "plominoform", None)

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

def exportElementAsXML(db, obj, isDatabase=False):
    from xml.dom.minidom import getDOMImplementation
    import HTMLParser
    impl = getDOMImplementation()
    xmldoc = impl.createDocument(None, "plominofield", None)
    out = db.exportElementAsXML(xmldoc, obj, isDatabase=isDatabase)
    return HTMLParser.HTMLParser().unescape(out.toxml())

def importElementFromXML(xmldocument, container):
    from xml.dom.minidom import parseString
    doc = parseString(xmldocument)
    db = container.getParentDatabase()
    db.importElementFromXML(container, doc.documentElement)
    
def _update_html_content(html):
    soup = BeautifulSoup(html)
    test = len(soup.select(".plominoLabelClass"))>0
    if not test:
        for field in soup.select(".plominoFieldClass"):
            tag=soup.new_tag('span')
            tag['class']='plominoLabelClass'
            tag.string=field.string
            field.insert_before(tag)
    return str(soup)

def addLabelsField(self):
    plone_tools = getToolByName(self, 'plone_utils')
    encoding = plone_tools.getSiteEncoding()
    layout = self.getField('FormLayout')
    html_content = layout.getRaw(self).decode(encoding).replace('\n', '')
    new_html = _update_html_content(html_content)
    
    layout.set(self,new_html)

class UpdateForm(object):
    
    class base(object):
        @classmethod
        def apply_to_all(cls, root, context):
            """ Applica le modifiche alla selezione di elementi XML """
            map(lambda el: cls.modify(el, context), cls.select(root))

    class label(base):
        @staticmethod
        def select(root):
            return root.findall(".//element/FormLayout")
        @staticmethod
        def modify(el, context):
            if not 'plominoLabelClass' in el.text:
                if not context is None:
                    plone_tools = getToolByName(context, 'plone_utils')
                    encoding = plone_tools.getSiteEncoding()
                else:
                    encoding = 'utf8'
                body = BeautifulSoup(el.text)
                for field in body.select("span.plominoFieldClass"):
                    label = body.new_tag("span")
                    label["class"] = "plominoLabelClass"
                    label.string = field.string
                    field.insert_before(label)
                el.text = etree.CDATA(str(body).decode(encoding))

    class datetime(base):
        """ Cerco tutti i PlominoField di tipo DATE e sostituisco
        il valore del parametro FildType con il valore DATETIME
        """

        @staticmethod
        def select(root):
            """ Selezione di tutti gli elementi di tipo PlominoField """
            return filter(
                lambda el: el.findtext("FieldType", default='').startswith('DATE'),
                root.findall(".//element[@type='PlominoField']"))

        @staticmethod
        def modify(el, _):
            """ Sostituzione del valore """
            fieldtype = el.find('FieldType')
            fieldtype.text = "DATETIME"

            newparams = etree.Element('params')
            newparam = etree.SubElement(newparams, 'param')
            newvalue = etree.SubElement(newparam, 'value')
            newstruct = etree.SubElement(newvalue, 'struct')
            newmember = etree.SubElement(newstruct, 'member')

            memname = etree.SubElement(newmember, 'name')
            memname.text='widget'
            memvalue = etree.SubElement(newmember, 'value')
            valstring = etree.SubElement(memvalue, 'string')
            valstring.text = 'JQUERY'

            params = el.find('params')
            if params is None:
                el.append(newparams)
            else:
                members = filter(
                    lambda i: i.findtext('name')=='widget',
                    el.findall("params/param/value/struct/member"))
                if not members:
                    struct = el.find("params/param/value/struct")
                    struct.insert(0, newmember)
                else:
                    member = el.find("params/param/value/struct/member")
                    member = newmember


    class template(base):

        @staticmethod
        def select(root):
            return root.findall(".//element/FieldReadTemplate") + \
                root.findall(".//element/FieldEditTemplate")
        @staticmethod
        def modify(el, context):
            """ Rimuovo i riferimenti ai teplate rimossi """
            if not context is None and el.text and not hasattr(context, el.text):
                el.text = None

    class htmlattribute(base):
        @staticmethod
        def select(root):
            return root.findall(".//field[@name='customAttributes']")
        @staticmethod
        def modify(el, _):
            """ customAttributes -> HTMLAttributesFormula """
            el.attrib['name'] = "HTMLAttributesFormula"
            if el.text:
                newtext = el.text.replace("'", "\\'").\
                    replace('data-plugin="datepicker" ', '').\
                    replace('dynamicHidewhen', 'data-dhw="true"')
                el.text = "'%s'" % newtext
            else:
                el.text = ""

    class description(base):
        @staticmethod
        def select(root):
            return root.findall(".//element[@type='PlominoField']")
        @staticmethod
        def modify(el, _):
            """ Aggiungo la descrizione agli attributi HTML5 del campo
            e rimuovo il tag fieldDescription
            """
            descriptionObj = el.findall(".//field[@name='fieldDescription']")[0]
            description = descriptionObj.text
            if not description is None:
                attribute = el.findall(".//field[@name='HTMLAttributesFormula']")[0]
                original = attribute.text[1:-1] 
                original = (original + ' data-field-description="%s"' %(description)).strip()
                attribute.text = "'%s'" % original 
            extensionfields = el.findall(".//extensionfields")[0]
            extensionfields.remove(descriptionObj)

    @classmethod
    def update(cls, context, filepath):
        tree = etree.parse(filepath, etree.XMLParser(strip_cdata=False))
        root = tree.getroot()

        # DECOMMENTA QUI LE SOSTITUZIONI NON VOLUTE
        wizard = [
            cls.htmlattribute, # 1. customAttributes -> HTMLAttributesFormula
            cls.description,   # 2. fieldDescription -> HTMLAttributesFormula
            cls.datetime,      # 3. DATE -> DATETIME
            cls.template,      # 4. - read/edit templates
            cls.label,         # 5. + plominoLabelClass
        ]
        
        for u in wizard:
            u.apply_to_all(root, context)

        tree.write(filepath)
    
    @classmethod
    def updateall(cls, context, path):
        xmls = map(lambda xml: os.path.join(path, xml), filter(lambda fn: fn.endswith('.xml'), os.listdir(path)))
        map(lambda xml: cls.update(context, xml), xmls)

def updateAllXML(path, context=None):
    UpdateForm.updateall(context, path)
