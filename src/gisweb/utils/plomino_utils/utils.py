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

