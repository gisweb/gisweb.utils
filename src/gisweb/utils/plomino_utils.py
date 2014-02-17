#!/usr/bin/python
# -*- coding: utf-8 -*-

from Products.CMFPlomino.interfaces import IPlominoDatabase
from Products.CMFPlomino.PlominoDocument import PlominoDocument

import cStringIO

from Products.CMFPlomino.PlominoUtils import DateToString, StringToDate, htmlencode, asList

from DateTime import DateTime
from DateTime.interfaces import DateError

import re, os

import Missing

from json_utils import json_dumps

import sys

import lxml.etree as etree

reload(sys)
sys.setdefaultencoding("utf-8")

def StartDayofMonth(d):
    # return DateTime(d.year(), d.month(), 1)
    return StringToDate(DateToString(d,'%m-%Y'),'%m-%Y')

def LastDayofMonth(d):
    return StringToDate(DateToString(StartDayofMonth(d)+32,'%m-%Y'),'%m-%Y')-1

def lookForValidDate(year, month, day, timeargs=[0, 0, 0], start=1):
    '''
    for internal purposes.
    '''

    if month not in range(1, 13):
        raise Exception('GISWEB:UTILS ERROR: Not a valid month passed: %s' % month)

    if day not in range(1, 32):
        raise Exception('GISWEB:UTILS ERROR: Not a valid day passed: %s' % month)

    try:
        return DateTime(year, month, day, *timeargs) - start
    except DateError, error:
        # WARNING! only errors in day parameter are considered.
        day -= 1
        test = True
        while test:
            try:
                return DateTime(year, month, day, *timeargs)
            except DateError, error:
                day -= 1
            else:
                test = False

def addToDate(date, addend, units='months', start=1):
    """
    data: a zope DateTime object
    addend: int
    units: string, "months", "years" or "days" are accepted
    start: int, 0 or 1

    A DateTime may be added to a number and a number may be
    added to a DateTime and the number is supposed to represent a number of days
    to add to the date in the sum.
    You can use this function to easily add other time units such as months or years.
    Form internal convention by default is returned the first valid date before the one
    you could expect.
    """

    if not isinstance(addend, int):
        addend = int(addend)

    if units == 'days':
        return date + addend

    year = date.year()
    month = date.month()
    day = date.day()

    timeargs = [date.hour(), date.minute(), date.second(), date.timezone()]
    months = range(1, 13)
    month_id = months.index(month)

    if units == 'months':
        new_year = year + (month_id+addend)/12
        mew_month_id = (month_id+addend)%12
        new_month = months[mew_month_id]
        return lookForValidDate(new_year, new_month, day, timeargs, start=start)

    elif units == 'years':
        new_year = year + addend
        return lookForValidDate(new_year, month, day, timeargs, start=start)

    else:
        raise Exception('units %s is not yet implemented' % units)

def attachThis(plominoDocument, submittedValue, itemname, filename='', overwrite=True):
    """
    Funcion with the aim to simplify the setting of a file as an attachment of a plominoDocument
    Usage sample:
    submittedValue = plominoPrint(plominoDocument, 'stampa_autorizzazione')
    attachThis(plominoDocument, submittedValue, 'autorizzazione', filename='stampa_autorizzazione.pdf')
    #### TO DO ####
    a batter reciper proposed by Eric B. could be found here:
    https://github.com/plomino/Plomino/issues/172#issuecomment-9494835
    ###############
    """
    new_file = None

    if isinstance(submittedValue, basestring):

        try:
            os.path.isfile(submittedValue)
        except:
            with tempfile.TemporaryFile() as tmpFile:
                tmpFile.write(submittedValue)
                tmpFile.seek(0)
                (new_file, contenttype) = plominoDocument.setfile(tmpFile,
                    filename=filename or tmpFile.name, overwrite=overwrite)
        else:
            if os.path.isfile(submittedValue):
                with open(submittedValue, 'r') as ff:
                    (new_file, contenttype) = plominoDocument.setfile(ff,
                        filename=filename, overwrite=overwrite)

    if not new_file:
        (new_file, contenttype) = plominoDocument.setfile(submittedValue,
            filename=filename, overwrite=overwrite)

    if not contenttype:
        # then try a guess
        try:
            #import cStringIO
            from plone.app.blob.utils import guessMimetype
            tmpFile = StringIO()
            tmpFile.write(submittedValue)
            contenttype = guessMimetype(tmpFile, filename)
            tmpFile.close()
        except:
            pass

    current_files = plominoDocument.getItem(itemname, {}) or {}
    current_files[new_file] = contenttype or 'unknown filetype'
    plominoDocument.setItem(itemname, current_files)
    return new_file

def fiatDoc(request, form, applyhidewhen=False):
    db = form.getParentDatabase()
    doc = db.createDocument()
    form.readInputs(doc, request, applyhidewhen=applyhidewhen)
    doc.runFormulaScript("form_%s_oncreate" % form.id, doc, form.onCreateDocument)
    doc.save()
    return doc.id

class batch(object):

    def __init__(self, context):
        self.db = context.getParentDatabase()
        self.errors = list()

    def set_error(self, method, message, **kwargs):
        kwargs.update({
            'method': method,
            'message': message,
            'date': DateTime()
        })
        self.errors.append(kwargs)

    def save(self, doc, form=None, creation=False, refresh_index=True, asAuthor=True, onSaveEvent=True):
        """ Refresh values according to form, and reindex the document.

        Computed fields are processed.
        """
        if not form:
            form = doc.getForm()
        else:
            doc.setItem('Form', form.getFormName())

        db = self.db
        if form:
            for f in form.getFormFields(includesubforms=True, doc=doc):
                mode = f.getFieldMode()
                fieldname = f.id
                # Computed for display fields are not stored
                if (mode in ["COMPUTED", "COMPUTEDONSAVE"] or 
                        (creation and mode=="CREATION")):
                    result = form.computeFieldValue(fieldname, doc)
                    doc.setItem(fieldname, result)

            # compute the document title
            title_formula = form.getDocumentTitle()
            if title_formula:
                # Use the formula if we have one
                try:
                    title = doc.runFormulaScript(
                            'form_%s_title' % form.id,
                            doc,
                            form.DocumentTitle)
                    if title != doc.Title():
                        doc.setTitle(title)
                except PlominoScriptException, e:
                    e.reportError('Title formula failed')
            elif creation:
                # If we have no formula and we're creating, use Form's title
                title = form.Title()
                if title != doc.Title():
                    # We may be calling save with 'creation=True' on
                    # existing documents, in which case we may already have
                    # a title.
                    doc.setTitle(title)

            # update the document id
            if creation and form.getDocumentId():
                new_id = doc.generateNewId()
                if new_id:
                    transaction.savepoint(optimistic=True)
                    db.documents.manage_renameObject(doc.id, new_id)

        # update the Plomino_Authors field with the current user name
        if asAuthor:
            # getItem('Plomino_Authors', []) might return '' or None
            authors = asList(doc.getItem('Plomino_Authors') or [])
            name = db.getCurrentMember().getUserName()
            if not name in authors:
                authors.append(name)
            doc.setItem('Plomino_Authors', authors)

        # execute the onSaveDocument code of the form
        if form and onSaveEvent:
            try:
                result = doc.runFormulaScript('form_%s_onsave' % form.id, doc, form.onSaveDocument)
                if result and hasattr(doc, 'REQUEST'):
                    doc.REQUEST.set('plominoredirecturl', result)
            except PlominoScriptException, e:
                self.set_error(self.save.__name__, e.message)

        if refresh_index:
            # update index
            db.getIndex().indexDocument(doc)
            # update portal_catalog
            if db.getIndexInPortal():
                db.portal_catalog.catalog_object(
                    doc,
                    "/".join(db.getPhysicalPath() + (doc.id,))
                )

    def saveDocument(self, doc, REQUEST=None, creation=False):
        """ Save a document using the form submitted content """
        db = self.db
        if REQUEST is None:
            REQUEST = doc.REQUEST
        form = db.getForm(REQUEST.get('Form', '')) or db.getForm(doc.getItem('Form'))

        errors = form.validateInputs(REQUEST, doc=doc)

        # execute the beforeSave code of the form
        error = None
        try:
            error = doc.runFormulaScript(
                    'form_%s_beforesave' % form.id,
                    doc,
                    form.getBeforeSaveDocument)
        except PlominoScriptException, e:
            self.set_error(self.saveDocument.__name__, e.message)

        if error:
            errors.append(error)

        if len(errors)>0:
            for e in errors:
                self.set_error(self.saveDocument.__name__, e)
        else:
            doc.setItem('Form', form.getFormName())

            # process editable fields (we read the submitted value in the request)
            form.readInputs(doc, REQUEST, process_attachments=True)

            # refresh computed values, run onSave, reindex
            self.save(doc, creation=creation)

    def createDocument(self, form, REQUEST):
        """ Create a document using the form's submitted content.

        The created document may be a TemporaryDocument, in case 
        this form was rendered as a child form. In this case, we 
        aren't adding a document to the database yet.

        If we are not a child form, delegate to the database object 
        to create the new document.
        """
        db = self.db
        if not REQUEST:
            REQUEST = db.REQUEST

        # validate submitted values
        errors = form.validateInputs(REQUEST)
        if errors:
            for err in errors:
                self.set_error(self.createDocument.__name__, err)

        # Add a document to the database
        doc = db.createDocument()
        doc.setItem('Form', form.getFormName())

        # execute the onCreateDocument code of the form
        valid = ''
        try:
            valid = doc.runFormulaScript(
                    'form_%s_oncreate' % form.id,
                    doc,
                    form.onCreateDocument)
        except PlominoScriptException, e:
            #e.reportError('Document is created, but onCreate formula failed')
            self.set_error(self.createDocument.__name__, e.message)

        if valid is None or valid == '':
            self.saveDocument(doc, REQUEST, creation=True)
            for f in form.getFormFields(includesubforms=True):
                fieldname = f.id

        return doc.id

    def refresh(self, form=None, **kwargs):
        """ re-compute fields and re-index document
        (by default onSave event is not called, and authors are not updated
        """
        default = dict(creation=False, refresh_index=True, asAuthor=False, onSaveEvent=False)
        default.update(kwargs)
        self.save(doc, form, **default)

def batch_createDocument(context, form, REQUEST=None):
    b = batch(context)
    doc_id = b.createDocument(form, REQUEST)
    return dict(id=doc_id, errors=b.errors)

def batch_saveDocument(context, doc, REQUEST, creation=False):
    b = batch(context)
    doc_id = b.saveDocument(doc, REQUEST, creation)
    return dict(id=doc_id, errors=b.errors)

#def batch_save(context, doc, form=None, creation=False, refresh_index=True,
        #asAuthor=True, onSaveEvent=True):
    #b = batch(context)
    #b.save(doc, form=form, creation=creation, refresh_index=refresh_index,
        #asAuthor=asAuthor, onSaveEvent=onSaveEvent)
    #return b.errors

def fetchViewDocuments(view, start=1, limit=None, only_allowed=True, getObject=True,
    fulltext_query=None, sortindex=None, reverse=None, **query):
    """
    courtesy of: https://github.com/silviot/Plomino/blob/github-main/Products/CMFPlomino/PlominoView.py#L305
    """
    index = view.getParentDatabase().getIndex()
    if not sortindex:
        sortindex = view.getSortColumn()
        if sortindex=='':
            sortindex=None
        else:
            sortindex=view.getIndexKey(sortindex)
    if not reverse:
        reverse = view.getReverseSorting()
    query['PlominoViewFormula_'+view.getViewName()] = True
    if fulltext_query:
        query['SearchableText'] = fulltext_query
    results=index.dbsearch(
        query,
        sortindex=sortindex,
        reverse=reverse,
        only_allowed=only_allowed)
    if limit:
        results = batch(
                results,
                pagesize=limit,
                pagenumber=int(start/limit)+1)
    if getObject:
        return [r.getObject() for r in results]
    else:
        return results

def getRndFieldValue(field, plominoContext):
    """
    TODO: "DATAGRID", "DOCLINK"
    """

    REQUEST = plominoContext.REQUEST
    db = plominoContext.getParentDatabase()

    containsany = lambda string, *subs: any([r>0 for r in map(string.count, subs)])

    fieldname = field.getId()
    fieldtype = field.getFieldType()
    result = dict()
    value = None

    #if fieldtype == 'DATAGRID':
        #frmname = field.getSettings().associated_form
        #nfrm = db.getForm(frmname)
        #value = []
        #for cname in field.getSettings().getColumnLabels():
            #fld = nfrm.getFormField(cname)


        #value = []

    if containsany(fieldtype, "DATE", "DATETIME"):
        fr = field.getSettings('format') or db.getDateTimeFormat() or '%Y-%m-%d'
        value = dategenerate(s=-14000, e=90, format=None, type=fieldtype).strftime(fr)
        #req[fieldname] = value

    elif fieldtype == "NUMBER":
        value = numbergenerate(type=field.getSettings('type'))
        #req[fieldname] = value

    elif fieldtype == "BOOLEAN":
        value = boolgenerate()
        #req[fieldname] = value

    elif fieldtype == "ATTACHMENT":
        # WARNING: Option not yet implemented!
        value = None
        ##import tempfile
        ##tmpFile = tempfile.TemporaryFile()
        ##tmpFile.write('supercalifragilistichespiralidoso')
        ##tmpFile.seek(0)
        ##value = {da_du_ma()[:8]: 'plain/text'}
        ##result['file'] = tmpFile
        #raise Exception('Option not yet implemented!')
        ## allego la conversione in pdf del form vuoto
        #html_content = form.applyHideWhen(silent_error=False)
        #pdf = printToPdf(html=html_content, content=False)
        ## piccolo trucco perché non sono riuscito a mettere in request un oggetto
        ## FileUpload-like (https://github.com/silviot/Plomino/blob/github-main/Products/CMFPlomino/PlominoField.py#L192)
        #filename, contenttype = doc.setfile(pdf,
            #filename='domanda_inviata.pdf' if fieldname=='documenti_pdf' else'%s.pdf' % da_du_ma(4),
            #overwrite=False,
            #contenttype='application/pdf'
        #)
        #value = {filename: contenttype}
        ##doc.setItem(fieldname, {filename: contenttype})

    elif fieldtype == "SELECTION":
        sel = field.getSettings().getSelectionList(plominoContext)
        vals = [i.split('|')[1] for i in sel]

        if field.getMandatory() is True:
            vals = filter(lambda x: x, vals)
        if field.getSettings('widget') in ("SELECTION", "RADIO", ) or True:
            value = rndselection(vals)
        else:
            length = len(vals)
            if length > 1:
                rndlen = numbergenerate(lower=1, upper=length)
            else:
                rndlen = 1
            value = rndselection(vals, n=rndlen)

    elif containsany(fieldtype, "TEXT", "NAME"):

        if containsany(fieldname, 'cognome'):
            value = namegenerate('LAST')
        elif containsany(fieldname, 'nome') or fieldtype=="NAME":
            value = namegenerate()
        elif containsany(fieldname, 'email', 'mail', 'pec'):
            value = '%s@example.com' % da_du_ma(4)
        elif containsany(fieldname, '_cf', 'fiscale'):
            surname = namegenerate('LAST')
            name = namegenerate()
            birth = dategenerate(s=-14000, e=0)
            sex = rndselection(vals=('M', 'F', ), n=1)
            cod = rndCodFisco()[-1]
            value = cf_build(surname, name, birth.year(), birth.month(), birth.day(), sex, cod)
        elif containsany(fieldname, 'piva'):
            part = numbergenerate(digits=11)
            if part < 0:
                part *= -1
            part = str(part)
            suff = is_valid_piva(part, validate=False)
            value = part[:-1] + suff
        elif containsany(fieldname, 'comune'):
            comune, prov, cap, codfisco = rndCodFisco()
            value = comune
            REQUEST.set(fieldname.replace('comune', 'localita'), comune)
            REQUEST.set(fieldname.replace('comune', 'provincia'), prov)
            REQUEST.set(fieldname.replace('comune', 'cap'), cap)
            REQUEST.set(fieldname.replace('comune', 'cod_cat'), codfisco)

        elif containsany(fieldname, 'cap'):
            value = str(numbergenerate(digits=5, negative=False))
        elif containsany(fieldname, 'cittadinanza'):
            value = da_du_ma(4)
        elif containsany(fieldname, 'civico'):
            value = ('%s %s' % (numbergenerate(negative=False, lower=0, upper=100), da_du_ma(2)))[:5]
        elif containsany(fieldname, 'cciaa'):
            value = da_du_ma(6)
        elif containsany(fieldname, 'tel', 'cell', 'fax'):
            prefix = numbergenerate(digits=4, negative=False)
            number = numbergenerate(digits=9, negative=False)
            value = '%s/%s' % (prefix, number, )
        elif containsany(fieldname, 'geometry', 'the_geom'):
            latlon = latlongenerate(tl=(9.85, 44.10), br=(9.80, 44.15))
            value = '%.5f %.5f' % latlon[-1::-1]
            if containsany(fieldname, 'indirizzo_geometry'):
                try:
                    res1 = geocode(latlng='%.5f,%.5f' % value)
                # ConnectionError
                except Exception as err:
                    pass
                else:
                    if res1['status'] == 'OK':
                        #address = res1['results'][0]['formatted_address']
                        address = res1['results'][0]['address_components'][0]['long_name']
                        fn = fieldname.replace('_geometry', '')
                        REQUEST.set(fn, address)
                        #req[fieldname.replace('_geometry', '')] = address
        elif containsany(fieldname, 'indirizzo'):
            latlon = latlongenerate(tl=(9.85, 44.10), br=(9.80, 44.15))
            try:
                # first take: I ask google for the nearest address
                res1 = geocode(latlng='%.5f,%.5f' % latlon)
            # ConnectionError
            except Exception as err:
                value = ''
            else:
                if res1['status'] == 'OK':
                    value = res1['results'][0]['address_components'][0]['long_name']
                else:
                    value = ''
            finally:
                # if internet connection not available or response status is not OK
                # I fill it in with random text
                if value == '':
                    z = rndgenerate(length=10, prefix=False)
                    length = int(field.getSettings('size') or -1)
                    value = z[:length].replace('\n', ' ')

        elif containsany(fieldname, 'foglio', 'mappale'):
            value = numbergenerate(digits=2, negative=False)

        else:
            length = int(field.getSettings('size') or -1)
            if field.getSettings('widget') == 'TEXTAREA':
                z = rndgenerate(length=numbergenerate(type='INTEGER', negative=False, lower=10, upper=100), prefix=False)
                value = '\n'.join(z.split('\n')[:length])
            elif field.getSettings('widget') == 'TEXT':
                z = rndgenerate(length=10, prefix=False)
                value = z[:length].replace('\n', ' ')
            if len(value)>50:
                value = value[:49]
    result['itemValue'] = value
    return result

def getRndFieldValues(form, only_mandatory=True):
    # TODO: support for option to fill only a fields subset
    out = dict()
    for field in form.getFormFields(includesubforms=True):

        if only_mandatory and not field.getMandatory():
            continue

        fieldname = field.getId()
        fieldtype = field.getFieldType()

        # I arbitrarily mantain values already set up
        if fieldname not in form.REQUEST.keys():

            result = getRndFieldValue(field, form)
            value = result['itemValue']
            if value != None:
                form.REQUEST.set(fieldname, value)
                if fieldtype == 'ATTACHMENT':
                    sdm = form.getParentDatabase().session_data_manager
                    sd = sdm.getSessionData()
                    sd[fieldname] = result['file']


def update2FieldDescription(el):
    """ fieldDescription -> FieldDescription """
    el.attrib['name'] = "FieldDescription"

def update2HTMLAttributesFormula(el):
    """ customAttributes -> HTMLAttributesFormula """
    el.attrib['name'] = "HTMLAttributesFormula"
    if el.text:
        el.text = '"""%s"""' % el.text

def update2DATETIME(el):
    """ DATE -> DATETIME
    Cambio i campi di tipo DATE a DATETIME con uso del widget JQUERY
    """
    fieldtype = el.find('FieldType')
    fieldtype.text = "DATETIME"

    newparams = etree.Element('params')
    newparam = etree.SubElement(newparams, 'param')
    newvalue = etree.SubElement(newparam, 'value')
    newstruct = etree.SubElement(newvalue, 'struct')
    newmember = etree.SubElement(newstruct, 'member')

    memname = etree.SubElement(newmember, 'name', text='widget')
    memvalue = etree.SubElement(newmember, 'value')
    valstring = etree.SubElement(memvalue, 'string', text='JQUERY')

    params = el.find('params')
    if params is None:
        el.append(newparams)
    else:
        members = filter(
            lambda i: i.findtext('name')=='widget',
            el.findall("params/param/value/struct/member"))
        if not members:
            struct = el.find("params/param/value/struct")
            struct.append(newmember)
        else:
            member = el.find("params/param/value/struct/member")
            member = newmember

def update2TitleAsLabel(el, value=True):

    newelement = etree.Element('TitleAsLabel', type='Products.Archetypes.Field.BooleanField')
    newelement.text = 'True'
    TitleAsLabel = el.find('TitleAsLabel')

    if TitleAsLabel is None :
        el.append(newelement)
    else:
        TitleAsLabel.text = 'True'


def update2FieldTemplate(context, el):
    """ Rimuovo i riferimenti ai teplate rimossi """
    if el.text and not hasattr(context, el.text):
        el.text = None

def updateXML(context, filepath):
    tree = etree.parse(filepath, etree.XMLParser(strip_cdata=False))
    root = tree.getroot()

    descriptions = root.findall(".//field[@name='fieldDescription']")
    map(update2FieldDescription, descriptions)

    attributes = root.findall(".//field[@name='customAttributes']")
    map(update2HTMLAttributesFormula, attributes)

    dateelements = filter(
        lambda el: el.findtext("FieldType", default='').startswith('DATE'),
        root.findall(".//element[@type='PlominoField']"))
    map(update2DATETIME, dateelements)

    fieldtemplates = root.findall(".//element/FieldReadTemplate") + \
        root.findall(".//element/FieldEditTemplate")
    map(lambda ft: update2FieldTemplate(context, ft), fieldtemplates)

    plominofields = root.findall(".//element[@type='PlominoField']")
    map(update2TitleAsLabel, plominofields)

    tree.write(filepath)

def updateAllXML(context, path):
    xmls = map(lambda xml: os.path.join(path, xml), filter(lambda fn: fn.endswith('.xml'), os.listdir(path)))
    map(lambda xml: updateXML(context, xml), xmls)