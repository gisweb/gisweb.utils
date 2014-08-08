#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import tempfile
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

# Plone
try:
    from plone.batching.batch import Batch
    batch = Batch.fromPagenumber
except:
    # < 4.3 compatibility
    from plone.app.content.batching import Batch
    batch = Batch


def getIndexType(plominoContext, key):
    """
    """
    indexes = plominoContext.getParentDatabase().getIndex().Indexes
    try:
        return '%s' % indexes[key]
    except KeyError:
        return None
        
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
    """ Easy PlominoDocument creation starting from PlominoForm """
    db = form.getParentDatabase()
    doc = db.createDocument()
    form.readInputs(doc, request, applyhidewhen=applyhidewhen)
    doc.runFormulaScript("form_%s_oncreate" % form.id, doc, form.onCreateDocument)
    doc.save()
    return doc.id

def fetchViewDocuments(view, start=1, limit=None, only_allowed=True, getObject=True,
    fulltext_query=None, sortindex=None, reverse=None, **query):
    """ 
    Query the PlominoView results
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

def serialItem(form, fieldname, item_value, doc=None, prefix='', nest_datagrid=True, render=True):
    """
    Returns a list of 2-tuples with the data contained in the field `fieldname` of form

    @param form                 : the PlominoForm containing the item that would be serialied;
    @param fieldname      C{str}: id of a PlominoField contained in the PlominoForm
    @param item_value           : the item value;
    @param doc                  : the PlominoDocument;
    @param nest_datagrid C{bool}: whether the fields of type DATAGRID has to be serialized nested;
    @param render        C{bool}: if you are interested in the data value serialization set it to False,
        otherwise you'll obtain the data renderization through the item basic read template.

    """
    req = []
    db = form.getParentDatabase()
    field = form.getFormField(fieldname)
    fieldtype = '' if not field else field.getFieldType()

    # custom DATE field type are considered as DATETIME stansard ones
    if fieldtype == 'DATE':
        fieldtype = 'DATETIME'

    if fieldtype == 'DOCLINK':

        if nest_datagrid:
            sub_req = []

        for link in item_value or []:
            sub_doc = db.getDocument(link)
            # I choose not to follow nested doclink, from now on follow_doclink is false
            el = dict(serialDoc(sub_doc, nest_datagrid=True, serial_as=False,
                field_list=[], render=render, follow_doclink=False))
            if nest_datagrid:
                sub_req.append(el)
            else:
                req += [('%s.%s' % (fieldname, k), v) for k,v in el.items()]

        if nest_datagrid:
            req.append((fieldname, sub_req))

    elif fieldtype == 'DATAGRID':
        grid_form = db.getForm(field.getSettings().associated_form)
        grid_field_names = field.getSettings().field_mapping.split(',')

        if nest_datagrid:
            sub_req = []

        for row in item_value or []:
            el = {}
            for idx,sub_field_name in enumerate(grid_field_names):
                sub_item_value = row[idx]

                if nest_datagrid:
                    el[sub_field_name] = sub_item_value
                else:
                    prefix = '%s.' % fieldname
                    req += serialItem(grid_form, sub_field_name,
                        sub_item_value, prefix=prefix, nest_datagrid=False)

            if nest_datagrid:
                sub_req.append(el)

        if nest_datagrid:
            req.append((fieldname, sub_req))

    else:
        # if I need data representation (or metadata) for printing porposes
        if item_value and render and fieldtype not in ('TEXT', 'NUMBER', ):
            # not worth it to call the template to render text and numbers
            # it is an expensive operation
            fieldtemplate = db.getRenderingTemplate('%sFieldRead' % fieldtype) \
                or db.getRenderingTemplate('DefaultFieldRead')
            renderedValue = fieldtemplate(fieldname=fieldname,
                fieldvalue = item_value,
                selection = field.getSettings().getSelectionList(doc),
                field = field,
                doc = doc
            ).strip()
        # if I need data value
        else:
            if not item_value:
                renderedValue = ''
            elif fieldtype == 'NUMBER':
                custom_format = field.getSettings('format')
                renderedValue = str(item_value) if not custom_format else custom_format % rendered_value
            elif fieldtype == 'DATETIME':
                custom_format = field.getSettings('format') or db.getDateTimeFormat()
                renderedValue = item_value.strftime(custom_format)
            else:
                # in order to prevent TypeError for unknown not JSON serializable objects
                try:
                    json_dumps(item_value)
                except TypeError:
                    renderedValue = '%s' % item_value
                else:
                    renderedValue = item_value
        key = prefix + fieldname
        req.append((key, renderedValue, ))
    return req


def serialDoc(doc, nest_datagrid=True, serial_as='json', field_list=[], render=True, follow_doclink=False):
    """
    Take a Plomino document :doc: and extract its data in a JSON-serializable
    structure for printing porposes.
    Item values are renderized according to the field definition and by default only
    defined fields will be considered.

    @param doc           : the PlominoDocument to serialize;
    @param nest_datagrid : see serialItem;
    @param serial_as     : json/xml;
    @param field_list    : if you need a subset of item to be serialized you can just
                           specify the list if item name you need;
    @param render        : see serialItem.
    """

    # bad_items are indistinguishable from good behaved citizen: they are unicode
    # values that just don't belong to the data (they are in fact metadata)
    # We want to skip those, and to do that we must explicitly list 'em
    bad_items = ['Plomino_Authors', 'Form']

    res = []
    form = doc.getForm()
    fieldlist = field_list or [i.id for i in form.getFormFields(includesubforms=True,
        doc=None, applyhidewhen=False) if i.getFieldType()!='DOCLINK' or follow_doclink]
    for itemname in fieldlist:
    #for field in form.getFormFields(includesubforms=True, doc=None, applyhidewhen=False):
    #for itemname in doc.getItems():
        #itemname = field.id
        if itemname not in bad_items:
            itemvalue = doc.getItem(itemname, '') or ''
            fieldname = itemname
            res += serialItem(form, fieldname, itemvalue, doc=doc, nest_datagrid=nest_datagrid, render=render)

    if serial_as == 'json':
        return json_dumps(dict(res))
    elif serial_as == 'xml':
        from dict2xml import dict2xml
        return dict2xml(dict(res))
    else:
        return res