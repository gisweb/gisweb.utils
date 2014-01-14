# -*- coding: utf-8 -*-
"Monkey patch PlominoForm"
from Products.CMFPlomino.PlominoUtils import asUnicode, asList
from jsonutil import jsonutil as json

from dateutil.parser import parse as parse_date

try:
    from plone.app.content.batching import Batch # Plone < 4.3
    HAS_PLONE43 = False
except ImportError:
    from plone.batching import Batch # Plone >= 4.3
    HAS_PLONE43 = True

from Products.PluginIndexes.DateIndex.DateIndex import DateIndex

from Products.CMFPlomino.PlominoDocument import PlominoDocument
from Products.CMFPlomino.PlominoForm import PlominoForm
from Products.CMFPlomino.PlominoView import PlominoView

from Products.CMFPlomino.index import PlominoIndex
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.CMFPlomino.config import READ_PERMISSION

PlominoIndex.security = ClassSecurityInfo()
PlominoIndex.security.declareProtected(READ_PERMISSION, 'search_json')
PlominoIndex.security.declareProtected(READ_PERMISSION, 'search_documents')
PlominoIndex.security.declareProtected(READ_PERMISSION, 'getFullLayout')
PlominoIndex.security.declareProtected(READ_PERMISSION, 'addLocalRoles')
PlominoIndex.security.declareProtected(READ_PERMISSION, 'get_js_hidden_fields')
InitializeClass(PlominoView)
InitializeClass(PlominoForm)

# VERSION 1.18.4
def readInputs(self, doc, REQUEST, process_attachments=False, applyhidewhen=True, validation_mode=False):
        """ Read submitted values in REQUEST and store them in document
        according to fields definition.
        """
        all_fields = self.getFormFields(
                includesubforms=True,
                doc=doc,
                request=REQUEST)
        if applyhidewhen:
            displayed_fields = self.getFormFields(
                    includesubforms=True,
                    doc=doc,
                    applyhidewhen=True,
                    request=REQUEST)

        for f in all_fields:
            mode = f.getFieldMode()
            fieldName = f.id
            if mode == "EDITABLE":
                submittedValue = REQUEST.get(fieldName)
                if submittedValue is not None:
                    if submittedValue=='':
                        doc.removeItem(fieldName)
                    else:
                        v = f.processInput(
                                submittedValue,
                                doc,
                                process_attachments,
                                validation_mode=validation_mode)
                        if f.getFieldType() == 'SELECTION':
                            if f.getSettings().widget in [
                                    'MULTISELECT', 'CHECKBOX', 'PICKLIST']:
                                v = asList(v)
                        doc.setItem(fieldName, v)
                else:
                    # The field was not submitted, probably because it is
                    # not part of the form (hide-when, ...) so we just leave
                    # it unchanged. But with SELECTION, DOCLINK or BOOLEAN, we need
                    # to presume it was empty (as SELECT/checkbox/radio tags
                    # do not submit an empty value, they are just missing
                    # in the querystring)

                    # WARNING:
                    # Commenting the next four lines is the purpose of this MonkeyPatch

                    #if applyhidewhen and f in displayed_fields:
                        #fieldtype = f.getFieldType()
                        #if (fieldtype in ("SELECTION", "DOCLINK", "BOOLEAN")):
                            #doc.removeItem(fieldName)

                    pass

PlominoForm.readInputs = readInputs

def search_documents(self, start=1, limit=None, only_allowed=True,
    getObject=True, fulltext_query=None, sortindex=None, reverse=None,
    query_request={}):
    """
    Return all the documents matching the view and the custom filter criteria.
    """
    index = self.getParentDatabase().getIndex()
    if not sortindex:
        sortindex = self.getSortColumn()
        if sortindex=='':
            sortindex=None
        else:
            sortindex=self.getIndexKey(sortindex)
    if not reverse:
        reverse = self.getReverseSorting()
    query = {'PlominoViewFormula_'+self.getViewName() : True}

    total = len(index.dbsearch(query, only_allowed=only_allowed))

    query.update(query_request)

    if fulltext_query:
        query['SearchableText'] = fulltext_query
    results=index.dbsearch(
        query,
        sortindex=sortindex,
        reverse=reverse,
        only_allowed=only_allowed) # di fatto questo parametro NON viene usato dal metodo dbsearch
    if limit:
        if HAS_PLONE43:
            results = Batch(items=results, size=limit, start=int(start/limit)+1)*limit
        else:
            results = Batch(items=results, pagesize=limit, pagenumber=int(start/limit)+1)
    if getObject:
        return [r.getObject() for r in results], total
    else:
        return results, total

def search_json(self, REQUEST=None):
    """ Returns a JSON representation of view filtered data
    """
    data = []
    categorized = self.getCategorized()
    start = 1
    search = None
    sort_index = None
    reverse = 1

    if REQUEST:
        start = int(REQUEST.get('iDisplayStart', 1))

        limit = REQUEST.get('iDisplayLength')
        limit = (limit and int(limit))
        # In case limit == -1 we want it to be None
        if limit < 1:
            limit = None

        search = REQUEST.get('sSearch', '').lower()
        if search:
            search = " ".join([term+'*' for term in search.split(' ')])
        sort_column = REQUEST.get('iSortCol_0')
        if sort_column:
            sort_index = self.getIndexKey(self.getColumns()[int(sort_column)-1].id)
        reverse = REQUEST.get('sSortDir_0') or 'asc'
        if reverse=='desc':
            reverse = 0
        if reverse=='asc':
            reverse = 1

    query_request = json.loads(REQUEST['query'])
    # Some fields might express a date
    # We try to convert those strings to datetime
    #indexes = self.aq_parent.aq_base.plomino_index.Indexes
    indexes = self.getParentDatabase().getIndex().Indexes
    for key, value in query_request.iteritems():
        if key in indexes:
            index = indexes[key]
            # This is lame: we should check if it quacks, not
            # if it's a duck!
            # XXX Use a more robust method to tell apart
            # date indexes from non-dates

            # I'd use a solution like this one: http://getpython3.com/diveintopython3/examples/customserializer.py
            if isinstance(index, DateIndex):
                # convert value(s) to date(s)
                if isinstance(value, basestring):
                    query_request[key] = parse_date(value)
                else:
                    if isinstance(value['query'], basestring):
                        value['query'] = parse_date(value['query'])
                    else:
                        query_request[key]['query'] = [parse_date(v) for v in value['query']]

    results, total = self.search_documents(start=1,
                                   limit=None,
                                   getObject=False,
                                   fulltext_query=search,
                                   sortindex=sort_index,
                                   reverse=reverse,
                                   query_request=query_request)

    if limit:
        if HAS_PLONE43:
            results = Batch(items=results, size=limit, start=int(start/limit)+1)*limit
        else:
            results = Batch(items=results, pagesize=limit, pagenumber=int(start/limit)+1)
    display_total = len(results)

    columnids = [col.id for col in self.getColumns() if not getattr(col, 'HiddenColumn', False)]
    for b in results:
        row = [b.getPath().split('/')[-1]]
        for colid in columnids:
            v = getattr(b, self.getIndexKey(colid), '')
            if isinstance(v, list):
                v = [asUnicode(e).encode('utf-8').replace('\r', '') for e in v]
            else:
                v = asUnicode(v).encode('utf-8').replace('\r', '')
            row.append(v or '&nbsp;')
        if categorized:
            for cat in asList(row[1]):
                entry = [c for c in row]
                entry[1] = cat
                data.append(entry)
        else:
            data.append(row)
    return json.dumps({ 'iTotalRecords': total, 'iTotalDisplayRecords': display_total, 'aaData': data })

def getFullLayout(self):
    """ expose the protected method _get_html_content """
    return self._get_html_content()

def get_js_hidden_fields(self, REQUEST, doc):
    """ expose the protected method _get_js_hidden_fields """
    return self._get_js_hidden_fields(REQUEST=REQUEST, doc=doc)

def addLocalRoles(self, group, roles):
    return self.manage_addLocalRoles(group, roles)

PlominoView.search_documents = search_documents
PlominoView.search_json = search_json
PlominoForm.getFullLayout = getFullLayout
PlominoForm.get_js_hidden_fields = get_js_hidden_fields
PlominoDocument.addLocalRoles = addLocalRoles