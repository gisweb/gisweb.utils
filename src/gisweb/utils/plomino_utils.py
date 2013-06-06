#!/usr/bin/python
# -*- coding: utf-8 -*-

from Products.CMFPlomino.interfaces import IPlominoDatabase
from Products.CMFPlomino.PlominoDocument import PlominoDocument

from Products.CMFPlomino.PlominoUtils import DateToString, StringToDate, htmlencode

from DateTime import DateTime
from DateTime.interfaces import DateError

import re, os

import Missing

from json_utils import json_dumps

import sys
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

def toDate(str_d):
    formats=['%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%Y-%m-%d']
    for format in formats:
        try:
            return StringToDate(data, format)
        except:
            pass

def getItemOr(plominoDocument, item_name, default=None):

    try:
        value = plominoDocument.getItem(item_name)
    except AttributeError, err:
        value = default

    return value or default


#def StringToDate2():
#    """
#    StringToDate in PlominoUtils seams to fail in case of the guess in line 84 in
#    https://github.com/plomino/Plomino/blob/github-main/Products/CMFPlomino/PlominoUtils.py
#    > dt = strptime(DateTime(str_d).ISO(), '%Y-%m-%d %H:%M:%S')
#    the function exits with message:
#    ValueError: time data '2012-02-09T00:00:00' does not match format '%Y-%m-%d %H:%M:%S'
#    """

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

def getAllSubforms(frm, doc=None, applyhidewhen=False):
    """
    Get sub forms recursively. That is what getSubforms method does not do.
    """

    db = frm.getParentDatabase()
    sub_forms = []

    flag_frm = frm
    flag_subs = flag_frm.getSubforms(doc=doc, applyhidewhen=applyhidewhen)
    n = 0
    while n < len(flag_subs):
        sub_forms += flag_subs
        flag_frm_id = flag_subs[n]
        flag_frm = db.getForm(flag_frm_id)
        flag_subs = flag_frm.getSubforms()
        n += 1

    return sub_forms

def render_as_dataTable(aaData, fieldid, params={}, rawparams=""):
    '''
    useful params examples:
    oLanguage = {'sUrl': '/'.join(context.getParentDatabase().absolute_url().split('/')[:-1] + ['DataTables', 'getLanguagePat'])}
    rawparams examples:
    """aoColumns = [
        { "sTitle": "N° Aut.", "mDataProp": "numero_autorizzazione" },
        { "sTitle": "Inizio validità", "mDataProp": "data_inizio_valido" },
        { "sTitle": "Fine validità", "mDataProp": "data_fine_valido" },
        { "mDataProp": "id", "fnRender": function (aaData, value) {return '<a href="../'+ value +'">'+ "vai all'autorizzazione" +'</a>'} }
    ]"""
    Warning: rawparams code will be simply queued to other parameters, do not
    use rawparams for passing paramters already in params or in default_params such as:
    bJQueryUI, bPaginate, bLengthChange, bFilter, bSort, bInfo, bAutoWidth.
    '''
    # default Plomino dataTable parameters
    defautl_params = {
        'bJQueryUI': True,
        'bPaginate': True,
        'bLengthChange': True,
        'bFilter': True,
        'bSort': True,
        'bInfo': True,
        'bAutoWidth': False
    }

    defautl_params.update(params)
    defautl_params = json_dumps(defautl_params)

    if rawparams:
        defautl_params = defautl_params[:-1] + ', %s' + '}'
        defautl_params = defautl_params % rawparams

    aaData = json_dumps(aaData)

    html = """<script type="text/javascript" charset="utf-8">
        var aaData = %(aaData)s;
        var o_%(fieldid)s_DynamicTable;
        jq(document).ready(function() {
        o_%(fieldid)s_DynamicTable = jq('#%(fieldid)s_table').dataTable( {
            'aaData': %(aaData)s,
            %(default_params)s
            } );
        });
    </script><table id='%(fieldid)s_table' class="display"></table><div style="clear: both"></div>""" % locals()

    return html

def renderItem(field_value, field_name, form, raise_error=False, default=None):
    '''
    render the field value according to the given form
    '''
    if not field_value:
        return default
    try:
        return form.getFormField(field_name).getSettings().processInput(field_value)
    except Exception as myException:
        if not raise_error:
            return '%s' % myException
        else:
            raise myException


def renderRaw(rec, columns, items, form, render='as_list', raise_error=False, default_item_value=None):
    '''
    render a dataGrid like record
    rec = [[...], ...]
    columns: a list of item names
    form: a plominoForm
    render: could be a string like "as_list" or "as_dict" or a plominoForm
    '''

#    list_render = lambda x, y: renderItem(x, y, form, raise_error=raise_error)
#    dict_render = lambda x, y: (y, renderItem(x, y, form, raise_error=raise_error), )

    def get_element(item_name):
        field_value = rec[columns.index(item_name)]
        element = renderItem(field_value, item_name, form, raise_error=raise_error, default=default_item_value)
        return element

#    ll = list()
#    ld = list()
#    for item_name in items:
#        element = get_element(item_name)
#        ll.append(element)
#        ld.append((item_name, element, ))

    dd = dict()
    for item_name in columns:
        element = get_element(item_name)
        dd[item_name] = element

    ll = [dd[i] for i in items]

    if render == 'as_list':
        return ll

    def multireplace(text, replacements):
        for i, o in replacements:
            text = text.replace(i, o)
        return text

    if hasattr(render, 'displayDocument'):
#        request = render.getParentDatabase().REQUEST
#        for k,v in dd.items():
#            request.set(k, v)
        replacements = [('\n', '', ), ('\r', '', ), ('\t', '', )]
        rendered_html = render.displayDocument(None, creation=True, request=dd).strip()
        cleaned_html = '%s' % multireplace(rendered_html, replacements)
        for focus in ("^<p>\s*</p>", "<p>\s*</p>$", ):
            cleaned_html = re.sub(focus, "", cleaned_html)
        return ll + [cleaned_html]

    if render == 'as_dict':
        return dd

    return ll


def get_gridDataFor(plominoDocument, grid_name, items=None, render='as_list', filter_function=False, form_name=None, raise_error=False, default_item_value=None):
    '''
    render = 'as_list', 'as_dict', <plominoForm>

    returns:
        - [[<item_value_1>, <item_value_2>, <item_value_3>, ...], ...] # as_list
        - [{'<item_1>': <item_value_1>, ...}, ...] # as_dict
        - [[<item_value_1>, <item_value_2>, <html>], ...]

    '''

    if plominoDocument.isNewDocument():
        return list()

    db = plominoDocument.getParentDatabase()
    if not form_name:
        form_name = plominoDocument.Form

    grid_field = db.getForm(form_name).getFormField(grid_name)
    grid_form_name = grid_field.getSettings(key='associated_form')
    grid_form = db.getForm(grid_form_name)
    grid_value = plominoDocument.getItem(grid_name, [])

    columns = grid_field.getSettings(key='field_mapping').split(',')
    all_idxs = range(len(columns))

    # if no item given all associated form fields are considered
    if not items:
        items = columns
        idxs = all_idxs
    else:
        idxs = [columns.index(field_name) for field_name in items]

    out = list() # output init
    dict_render = lambda v, n: (n, renderItem(v, n, grid_form, raise_error=raise_error), )


    if isinstance(render, basestring):
        maybeForm = db.getForm(render)
        if maybeForm:
            render = maybeForm
        elif render == 'as_form':
            render = grid_form

    for rec in grid_value:

        if filter_function:
            filter_arg = dict(map(dict_render, rec, columns))
            if not filter_function(filter_arg):
                continue

        out_raw = renderRaw(rec, columns, items, grid_form, render=render, raise_error=raise_error, default_item_value=default_item_value)
        out.append(out_raw)

    return out

def get_dataFor(plominoDocument, where, items=None, render='as_list', filter_function=None, form_name=None, raise_error=False, default_item_value=''):
    '''
    "where" must be an item name (of type dataGrid) or at least a form name used
    as sub form in form (whom name is given in form_name or corresponds to
    plominoDocument.Form)
    '''

    if plominoDocument.isNewDocument():
        return list()

    grid_name = None
    sub_form_name = None

    db = plominoDocument.getParentDatabase()
    form = db.getForm(form_name or plominoDocument.Form)

    # data in dataGrid field?
    if where in plominoDocument.getItems():
        grid_name = where
        grid_field = form.getFormField(grid_name)
        sub_form_name = grid_field.getSettings(key='associated_form')
        sub_form = db.getForm(sub_form_name)
        columns = grid_field.getSettings(key='field_mapping').split(',')
    # else data comes from fields in a sub Form
    else:
        sub_form_name = where
        sub_form = db.getForm(sub_form_name)
        columns = [f.id for f in sub_form.getFormFields(includesubforms=True)]

    if not items:
        items = columns

    if isinstance(render, basestring):
        maybeForm = db.getForm(render)
        if maybeForm:
            render = maybeForm
        elif render == 'as_form':
            render = sub_form

    if grid_name:
        data_from_grid = get_gridDataFor(plominoDocument,
            grid_name = grid_name,
            items = items,
            render = render,
            filter_function = filter_function,
            form_name = form_name,
            raise_error = raise_error,
            default_item_value = default_item_value
        )
    else:
        data_from_grid = list()

    if sub_form_name in form.getSubforms(applyhidewhen=False):
        init_rec = [plominoDocument.getItem(k) for k in columns]
        init_raw = renderRaw(init_rec, columns, items, sub_form, render=render,
            raise_error=raise_error, default_item_value=default_item_value)
        data_from_grid.insert(0, init_raw)

    return data_from_grid

def get_gridDataFor_old(plominoDocument, grid_name, items=None, smart_filter=None, as_dict=False, form_name=None, sub_form_name=None):
    '''
    DEPRECATED!!!
    formula di popolamento oggetto con dati per la mappa del tipo
    [['label', <lat>, <lon>], ...]
    '''

    data = []
    db = plominoDocument.getParentDatabase()

    if plominoDocument.isNewDocument():
        return []

    if not form_name:
        form_name = plominoDocument.Form

    if grid_name:
        grid_field = db.getForm(form_name).getFormField(grid_name)
        grid_form = db.getForm(grid_field.getSettings(key='associated_form'))

    if not items:
        if grid_name:
            items = [f.id for f in grid_form.getFormFields()]
        else:
            sub_frm = db.getForm(sub_form_name)
            items = [f.id for f in sub_frm.getFormFields()]

    if as_dict:
        init_value = dict([(item,plominoDocument.getItem(item)) for item in items])
    else:
        init_value = [plominoDocument.getItem(item) for item in items]

    if init_value not in (
        dict([(item,None) for item in items]),
        [None for item in items]
    ):
        data = [init_value]

    if not grid_name:
        return data

    grid_value = plominoDocument.getItem(grid_name)

    if not grid_value:
        return data

    ordered_fields = grid_field.getSettings(key='field_mapping').split(',')

    # if no items list is provided all the fields are considered
    #+ this case could be useful for converting the DataGrid native list of list
    #+ value into a list of dictionaries passing as_dict=True

    all_idxs = range(len(ordered_fields))

    if items:
        idxs = [ordered_fields.index(field_name) for field_name in items]
    else:
        idxs = all_idxs

    if not smart_filter:
        smart_filter = lambda rec: True

    for rec in grid_value:

        def foo(i):
            if rec[i]:
                return grid_form.getFormField(ordered_fields[i]).getSettings().processInput(rec[i])
            else:
                return rec[i]

        complete_obj = dict([(ordered_fields[i], foo(i)) for i in all_idxs])
        if smart_filter(complete_obj):

            if as_dict:
                obj = dict([(ordered_fields[i], foo(i)) for i in idxs])
            else:
                obj = [foo(i) for i in idxs]

            data.append(obj)

    return data


def get_related_info(plominoDocument, clues, default=None, debug=False):
    '''
    get item values from one plominoDocument itself and the related ones.
    clues description: {<alias>:
        {
            'field_name': <field_name>, # OPTIONAL
            'source': <lambda to get source document id> # OPTIONAL
        }
    }

    the given lambda represent the relation between documents

    clues example: {
        'nome': None,
        'data1': {'field_name': 'data_nato',
            'source': lambda pd: pd.getItem('parentDocument')
        },
        'data2': {'field_name': 'data_consegna',
            'source': lambda pd: pd.getItem('elenco_consegne')[0]
        }
    }
    return: {<alias>: <field value>}
    '''
    db = plominoDocument.getParentDatabase()

    out = dict()
    for alias,clue in clues.items():

        source = None
        field_name = None
        if isinstance(clue, dict):

            if 'source' in clue:
                source = db.getDocument(clue['source'](plominoDocument))
            if 'field_name' in clue:
                field_name = clue['field_name']

        if not source:
            source = plominoDocument # at least get item from the plominoDocument itself

        if not field_name:
            field_name = alias # at least the field name is equivalent to alias

        if debug:
            if not field_name in source.items():
                raise IOError('Document %s does not contain field %s' % (source.getId(), field_name))

        out[alias] = source.getItem(field_name, default)

    return out


#def get_parent_plominodb(obj):
#    ''' Return the current plominoDatabase. Is enough to pass the context from
#        within a scipt or a plominoDocument python formula.
#    '''
#    current = obj
#    while hasattr(current, 'aq_parent') and not IPlominoDatabase.providedBy(current):
#        current = current.aq_parent
#    return hasattr(current, 'aq_parent') and current

def search_around(plominoDocument, parentKey='parentDocument', *targets, **flts):
    '''
    DA TESTARE

    "out" è un dizionario la cui chiavi sono le stringhe contenute in targets se
    per esse è stato trovato almeno un valore tra i documenti collegati al
    plominoDocument (compreso lo stesso). Se i valori trovati per la chiave
    richiesta fossero più di uno questi vengono messi in una lista. Per ottenere
    meno valori è possibile affinare la ricerca fornendo le chiavi "flts" che
    vengono usate per le ricerche nel plominoIndex e per la selezione dei
    documenti da cui attingere i valori.
    ATTENZIONE! NON sono contemplate condizioni di confronto per le ricerche che
    siano più complesse del semplice confronto di uguaglianza. Possono però
    essere passati parametri specifici per la ricerca su ZDB quali "sort_on",
    "sort_order" e simili.

    può sostituire in maniera meno statica il get_info_pratica
    '''

    out = dict()
    if plominoDocument.isNewDocument(): return out

#    main_fields = [t for t in targets if t in plominoDocument.getForm().getFormFields()]
#    other_fields = [t for t in targets if t not in main_fields]

    items = plominoDocument.getItems()
    # cerco prima nel documento "genitore"
    for target in targets:
        if target in items:
            out[target] = [plominoDocument.getItem(target)]

    # poi cerco nei documenti figli
    plominoIndex = plominoDocument.getParentDatabase().getIndex()
    flts[parentKey] = plominoDocument.id
    res = plominoIndex.dbsearch(**flts)
    for rec in res:
        pd = rec.getObject()

        # nel caso le chiavi in flts non fossero state indicizzate
        #+ evito i documenti che sarebbero stati scartati dalla ricerca
        #+ DA RIVEDERE E CORREGGERE
        if all([pd.getItem(k)==flts.get(k) for k in pd.getForm().getFormFields() if k in flts]):

            items = pd.getItems()
            for target in targets:
                if target in items:
                    if target in out:
                        out[target] += [plominoDocument.getItem(target)]
                    else:
                        out[target] = [plominoDocument.getItem(target)]
            if len(out[target]) == 1:
                out[target] = out[target][0]

    return out

def guessType(submittedValue, filename):
    
    out = dict()
    
    try:
        import cStringIO
        from plone.app.blob.utils import guessMimetype
    except ImportError, err:
        out.update(dict(
            contenttype = None,
            success = 0,
            err_msg = '%s' % err
        ))
        out['contenttype'] = None
    else:
        tmpFile = cStringIO.StringIO()
        tmpFile.write(submittedValue)
        out.update(dict(
            contenttype = guessMimetype(tmpFile, filename),
            success = 1,
        ))
        tmpFile.close()
        
    return out

def attachThis(plominoDocument, submittedValue, itemname, filename='', overwrite=True):
    '''
    Funcion with the aim to simplify the setting of a file as an attachment of a plominoDocument
    Usage sample:
    submittedValue = plominoPrint(plominoDocument, 'stampa_autorizzazione')
    attachThis(plominoDocument, submittedValue, 'autorizzazione', filename='stampa_autorizzazione.pdf')
    #### TO DO ####
    a batter reciper proposed by Eric B. could be found here:
    https://github.com/plomino/Plomino/issues/172#issuecomment-9494835
    ###############
    '''
    new_file = None
    try:
        os.path.isfile(submittedValue)
    except:
        pass
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
            import cStringIO
            from plone.app.blob.utils import guessMimetype
            tmpFile = cStringIO.StringIO()
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

################################################################################

def get_aaData2(brains, field_names, sortindex=None, reverse=None, enum=None):

    aaData = list()

    for num,rec in enumerate(brains):
        aaRec = dict([(k, rec.get(k) or rec.getObject().getItem(k, '')) for k in field_names])
        if enum:
            aaRec['_order'] = num

        if sortindex:
            aaData.append((rec[k] or rec.getObject().getItem(k, ''), aaRec, ))
        else:
            aaData.append(aaRec)

    if sortindex:
        aaData.sort()
    if reverse:
        aaData.reverse()

    if sortindex:
        return [rec[-1] for rec in aaData]
    else:
        return aaData

def get_aaData(brain, field_names, sortindex, reverse, enum, linked, field_renderes):

    aaData = []

    for num,rec in enumerate(brain):
        if enum:
            row = [num+1]
        else:
            row = []
        for k in field_names:
            value = rec[k]

            if not value:
                value = ''
            else:
                if k in field_renderes:
                    value = field_renderes[k](value)
                if linked:
                    value = '<a href="%(url)s">%(label)s</a>' % dict(url=rec.getURL(), label=json_dumps(value).replace('"', ''))
            row.append(value)

        rendered_value = '%s| ' % json_dumps(row)
        if sortindex:
            aaData.append((rec[sortindex], rendered_value, ))
        else:
            aaData.append(rendered_value)

    if sortindex:
        aaData.sort()

    if reverse:
        aaData.reverse()

    if sortindex:
        return [rec[-1] for rec in aaData]
    else:
        return aaData


from json_utils import json_dumps

def get_docLinkInfo(context, form_name, sortindex=None, reverse=0, enum=False, linked=True, slow_flt=None, field_names=[], request={}, field_renderes={}, deprecated=True):
    """
    Warning: sortindex has to be unique or none (or equivalent; i.e. 0 et sim.)
    slow_flt: "slow filter", must be a function or at least a lambda (or a list
    of functions) that takes a dictionary with the requested field_names as keys,
    test the values and returns a boolean.
    Warning: sortindex values has not to be missing.
    """
    db = context.getParentDatabase()
    idx = db.getIndex()

    if not field_names:
        form = db.getForm(form_name)
        field_names = [i.id for i in form.getFormFields(includesubforms=True) if i in idx.indexes()]
    else:
        fl = list()
        for f in field_names:
            if f in idx.indexes():
                fl.append(f)
            else:
                raise Exception('%s is not an index' % f)
        field_names = fl

    res = []
    if isinstance(request, dict):
        request = [request]

    for num in range(len(request)):
        request[num]['Form'] = form_name

    res_list = [idx.dbsearch(req, sortindex=sortindex, reverse=reverse) for req in request]
    res = sum(res_list[1:], res_list[0])
    if slow_flt != None:
        if isinstance(slow_flt, list):
            res = [rec for rec in res if all([fun(rec) for fun in slow_flt])]
#            new_res = list()
#            for rec in res:
#                if all([fun(rec) for fun in slow_flt]):
#                    new_res.append(rec)
#            res = new_res
        else:
            res = [rec for rec in res if slow_flt(rec)]

#    if len(request) > 1:
#        sortindex = None
    if deprecated:
        return get_aaData(res, field_names, sortindex, reverse, enum, linked, field_renderes)
    else:
        return get_aaData2(res, field_names, sortindex, reverse, enum, field_renderes)




################################################################################

def getPath(doc, virtual=False):

    if virtual:
        pd_path_list = doc.REQUEST.physicalPathToVirtualPath(doc.doc_path())
    else:
        pd_path_list = doc.doc_path()

    return '/'.join(pd_path_list)


class plominoKin(object):

    def __init__(self, context, **kwargs):
        self.parentKey = kwargs.get('parentKey') or 'parentDocument'
        self.parentLinkKey = kwargs.get('parentLinkKey') or 'linkToParent'
        self.childrenList_name = kwargs.get('childrenList_name') or 'elenco_%s'

        self.db = context.getParentDatabase()

        if kwargs.get('pid'):
            self.doc = self.db.getDocument(pid)
        elif isinstance(context, PlominoDocument):
            self.doc = context
        else:
            self.doc = None

#        if not self.doc:
#            raise Exception('GISWEB.UTILS ERROR: No plominoDocument found!!')

        self.idx = self.db.getIndex()
#        for fieldname in (self.parentKey, 'CASCADE', ):
#            if fieldname not in self.idx.indexes():
#                self.idx.createFieldIndex(fieldname, 'TEXT', refresh=True)

    def searchAndFetch(self, fields={}, mainRequest={}, sideRequests={}, json=False):
        """
        dbsearch(self, request, sortindex, reverse=0)
        mainRequest = dict(Form = <form_name>, **kwargs)
        sideRequests = dict(
            <form_name> = dict(**kwargs)
        )
        fields = dict(
            <form_name> = [(<field_name>, <unique_name>, ), (<field_name>, ), ...]
            ...
        )
        """
        import itertools
        if not 'Form' in mainRequest:
            raise IOError('GISWEB.UTILS ERROR: A kay for the parent form is required!')

        mainResults = self.idx.dbsearch(mainRequest)
        # sideResults = dict(<parentId> = dict(<form_name> = [{**kwargs}, ...], ...))
        sideResults = dict()
        for form_name, sideRequest in sideRequests.items():
            if 'Form' not in sideRequest:
                sideRequest['Form'] = form_name
            sideRequest[self.parentKey] = {'query': [i.id for i in mainResults], 'operator': 'or'}

            sideResult = self.idx.dbsearch(sideRequest, sortindex=self.parentKey)

            for sideRecord in sideResult:
                tmp_dict = dict()
                for i in fields.get(form_name, []):
                    try:
                        value = sideRecord[i[0]]
                    except:
                        value = sideRecord.getObject().getItem(i[0], '')
                    tmp_dict[i[-1]] = value

                if sideRecord[self.parentKey] not in sideResults:
                    sideResults[sideRecord[self.parentKey]] = {form_name: [tmp_dict]}
                else:
                    if form_name not in sideResults[sideRecord[self.parentKey]]:
                        sideResults[sideRecord[self.parentKey]][form_name] = [tmp_dict]
                    else:
                        sideResults[sideRecord[self.parentKey]][form_name].append(tmp_dict)

        for rec in mainResults:
            mainForm = rec.getObject().Form
            tmp_dict = dict([(i[-1], rec.get(i[0]) or rec.getObject().getItem(i[0], '')) for i in fields.get(mainForm, [])])
            if rec.id not in sideResults:
                sideResults[rec.id] = {mainForm: [tmp_dict]}
            else:
                if mainForm not in sideResults[rec.id]:
                    sideResults[rec.id][mainForm] = [tmp_dict]
                else:
                    sideResults[rec.id][mainForm].append(tmp_dict)


        # sideResults2 = dict(<plominoId> = [[{**kwargs}, ...], ...], ...)
        sideResults2 = dict()
        for key,value in sideResults.items():
            sideResults2[key] = [x for x in itertools.product(*sideResults[key].values())]

        sideResults3 = dict()
        for key,prod in sideResults2.items():
            for lista in prod:
                it = [i.items() for i in lista]
                s = sum(it[1:], it[0])
                v = dict([(key,v) for k,v in s])
                if not key in sideResults3:
                    sideResults3[key] = [v]
                else:
                    sideResults3[key].append(v)

            it = []
            for tt in prod:
                mit = [i.items() for i in tt]
                somma = sum(mit[1:], mit[0])
                it.append(dict([(k,v) for k,v in somma]))

            sideResults3[key] = it

        aaData = []
        for mainId,v in sideResults3.items():

            mainDict = dict()
            if mainRequest['Form'] in fields:
                mainDoc = self.db.getDocument(mainId)
                for x in fields[mainRequest['Form']]:
                    mainDict[x[-1]] = mainDoc.getItem(x[0], '')

            for i in v:
                it = i.items() + mainDict.items()
                aaRecord = dict()
                for key,value in it:
#                    if isinstance(value, Missing.Value): # to be tested
                    vtype = '%s' % type(value) # could be better to use isinstance for the test
                    if vtype == "<type 'Missing.Value'>":
                        value = None
                    aaRecord[key] = value
#                aaRecord = dict([(key,value) for key,value in it])
                if aaRecord:
                    aaData.append(aaRecord)

        if json:
            return json_dumps(aaData)
        else:
            return aaData


    def setParenthood(self, parent_id, child_id='', CASCADE=True, setDocLink=False):
        '''
        Set parent reference in child document
        '''
        if not child_id:
            child = self.doc
        else:
            child = self.db.getDocument(child_id)
        child.setItem(self.parentKey, parent_id)
        child.setItem('CASCADE', CASCADE)
        if setDocLink:
            parent = self.db.getDocument(parent_id)
            child.setItem(self.parentLinkKey, [getPath(parent)])

    def getParentDoc(self):
        return self.db.getDocument(self.doc.getItem(self.parentKey))

    def ondelete_parent(self):
        parent = self.doc
        idx = self.db.getIndex()
        request = {self.parentKey: parent.id}
        res = idx.dbsearch(request)
        toRemove = []
        for rec in res:
            if rec.CASCADE:
                toRemove += [rec.id]
            else:
                rec.getObject().removeItem(self.parentKey)
        self.db.deleteDocuments(ids=toRemove, massive=False)

    def setChildhood(self, parent_id, child_id, backToParent='anchor'):
        '''
        Set child reference on parent document
        '''
        parent = self.db.getDocument(parent_id)
        child = self.db.getDocument(child_id)
        childrenList_name = self.childrenList_name % child.Form
        if not childrenList_name in parent.getItems():
            parent.setItem(childrenList_name, [])
            childrenList = []
        else:
            childrenList = parent.getItem(childrenList_name, []) or []

        url = getPath(child)
        parent.setItem(childrenList_name, childrenList+[url])

        if backToParent:
            backUrl = parent.absolute_url()
            if backToParent == 'anchor':
                backUrl = '%s#%s' % (backUrl, childrenList_name)
            child.setItem('plominoredirecturl', backUrl)

    def oncreate_child(self, parent_id='', backToParent='anchor', **kwargs):
        child = self.doc

        # if no parent_id passed
        # first take from the child itself
        if not parent_id:
            parent_id = child.getItem(self.parentKey)

        # second take from the request
        if not parent_id:
            parent_id = child.REQUEST.get(self.parentKey)

        # no way
        if not parent_id:
            raise IOError('GISWEB.UTILS ERROR: Parent id not found!')

        for fieldname in (self.parentKey, 'CASCADE', ):
            if fieldname not in self.idx.indexes():
                self.idx.createFieldIndex(fieldname, 'TEXT', refresh=True)

        self.setParenthood(parent_id, child.id, **kwargs)
        self.setChildhood(parent_id, child.id, backToParent)

    def onsave_child(self):
        child = self.doc
        if not child.isNewDocument():
            if child.getItem('plominoredirecturl'):
                child.removeItem('plominoredirecturl')

    def ondelete_child(self, anchor=True):
        child = self.doc
        parent = self.db.getDocument(child.getItem(self.parentKey))
        childrenList_name = self.childrenList_name % child.Form
        childrenList = parent.getItem(childrenList_name, []) or []
        url = getPath(child)
        childrenList.remove(url)
        parent.setItem(childrenList_name, childrenList)

        backUrl = parent.absolute_url()
        if anchor:
            backUrl = '%s#%s' % (backUrl, childrenList_name)
        child.REQUEST.set('returnurl', backUrl)

    def get_children_list(self, form_name, etichetta):
        '''
        es: etichetta = '%(qualifica)s modello: %(modello)s con targa: %(targa)s'
        '''
        parent = self.doc
        lista = list()
        res = self.idx.dbsearch({'Form': form_name, self.parentKey: parent.id})

#        form = self.db.getForm(form_name)
#        fieldlist = form.objectValues(spec='PlominoField')
#        for rec in res:
#            dizionario = dict()
#            for k in [tt for tt in self.idx.indexes() if rec.has_key(tt)]:
#                if k in fieldlist:
#                    obj = rec.getObject()
#                    dizionario[k] = obj.getRenderedItem(k)
##                    dizionario[k] = getFieldRender(form, None, False, creation=False, request={k: rec[k]})
#                else:
#                    dizionario[k] = rec[k]

        for rec in res:
            obj = rec.getObject()
            dizionario = dict()
            for k in obj.getItems():
                try:
                    dizionario[k] = obj.getRenderedItem(k).strip()
                except AttributeError:
                    dizionario[k] = obj.getItem(k)

            etichetta1 = etichetta % dizionario
            lista.append('%s|%s' % (etichetta1, getPath(obj)))
        return lista

    def create_child(self, form_name, request={}, applyhidewhen=True, **kwargs):
        """
        Use it to create a child document from scripts
        """
        parent = self.doc
        form = self.db.getForm(form_name)
        doc = self.db.createDocument()
        doc.setItem('Form', form_name)
        form.readInputs(doc, request, applyhidewhen=applyhidewhen)
        self.setParenthood(parent.id, doc.id, **kwargs)
        self.setChildhood(parent.id, doc.id)
        doc.save()
        return doc.getId()

def ondelete_parent(doc):
    plominoKin(doc).ondelete_parent()

def oncreate_child(doc, **kwargs):
    plominoKin(doc).oncreate_child(**kwargs)

def create_child(context, **kwargs):
    plominoKin(context).create_child(**kwargs)

def onsave_child(doc):
    plominoKin(doc).onsave_child()

def ondelete_child(doc, **kwargs):
    plominoKin(doc).ondelete_child(**kwargs)

def get_children_list(doc, form_name, etichetta):
    return plominoKin(doc).get_children_list(form_name, etichetta)

def get_parent(doc):
    return plominoKin(doc).getParentDoc()

def fetchDocs(context, **kwargs):
    return plominoKin(context).searchAndFetch(**kwargs)

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

    def save(self, doc, form=None, creation=False, refresh_index=True, asAuthor=True, onSaveEvent=True, mantainOriginalForm=True):
        """refresh values according form, and reindex the document
        """
        method = 'save'

        # we process computed fields (refresh the value)
        if form is None:
            form = doc.getForm()
        elif not mantainOriginalForm:
            # questa sostituzione può essere evitata...
            doc.setItem('Form', form.getFormName())

        db=self.db # SONO QUI
        if form:
            for f in form.getFormFields(includesubforms=True, doc=doc, applyhidewhen=False):
                mode = f.getFieldMode()
                fieldname = f.id
                if mode in ["COMPUTED", "COMPUTEDONSAVE"] or (mode=="CREATION" and creation):
                    result = form.computeFieldValue(fieldname, doc)
                    doc.setItem(fieldname, result)
                else:
                    # computed for display field are not stored
                    pass

            # compute the document title
            title_formula = form.getDocumentTitle()
            if title_formula:
                # Use the formula if we have one
                try:
                    title = doc.runFormulaScript("form_"+form.id+"_title", doc, form.DocumentTitle)
                except PlominoScriptException, e:
                    message = 'Title formula failed: %s' % e
                    self.set_error(method, message)
                else:
                    if title != doc.Title():
                        doc.setTitle(title)
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
            authors = doc.getItem('Plomino_Authors', []) or []
            name = db.getCurrentUser().getUserName()

            if name not in authors:
                authors.append(name)

            doc.setItem('Plomino_Authors', authors)

        # execute the onSaveDocument code of the form
        if form and onSaveEvent:
            try:
                result = doc.runFormulaScript("form_"+form.id+"_onsave", doc, form.onSaveDocument)
#                if result and hasattr(doc, 'REQUEST'):
#                    doc.REQUEST.set('plominoredirecturl', result)
            except PlominoScriptException, e:
                message = 'Document has been saved but onSave event failed: %s' % e
                self.set_error(method, message)
#                if hasattr(doc, 'REQUEST'):
#                    e.reportError('Document has been saved but onSave event failed.')
#                    doc_path = doc.REQUEST.physicalPathToURL(doc.doc_path())
#                    doc.REQUEST.RESPONSE.redirect(doc_path)

        if refresh_index:
            # update index
            db.getIndex().indexDocument(doc)
            # update portal_catalog
            if db.getIndexInPortal():
                db.portal_catalog.catalog_object(doc, "/".join(db.getPhysicalPath() + (doc.id,)))

    def saveDocument(self, doc, REQUEST, creation=False):
        """save a document using the form submitted content
        """
        method = 'saveDocument'

        db = self.db
        form_name = REQUEST.get('Form') or doc.getItem('Form')

        form = db.getForm(form_name)

        errors=form.validateInputs(REQUEST, doc=doc)
        if len(errors)>0:
            for err in errors:
                self.set_error(method, err)
        else:
            doc.setItem('Form', form.getFormName())

            # process editable fields (we read the submitted value in the request)
            form.readInputs(doc, REQUEST, process_attachments=True)

            # refresh computed values, run onSave, reindex
            self.save(form, creation)

    def refresh(self, form=None, **kwargs):
        """ re-compute fields and re-index document
        (by default onSave event is not called, and authors are not updated
        """
        default = dict(creation=False, refresh_index=True, asAuthor=False, onSaveEvent=False)
        default.update(kwargs)
        self.save(doc, form, **default)

def batch_saveDocument(context, doc, REQUEST, creation=False):
    b = batch(context)
    b.saveDocument(doc, REQUEST, creation)
    return b.errors

def batch_save(context, doc, form=None, creation=False, refresh_index=True,
    asAuthor=True, onSaveEvent=True, mantainOriginalForm=True):
    pass


def serialItem(form, fieldname, item_value, doc=None, prefix='', nest_datagrid=True):
    """
    Returns a list of 2-tuples with the data contained in the field `fieldname` of form
    """
    req = []
    db = form.getParentDatabase()
    field = form.getFormField(fieldname)
    fieldtype = '' if not field else field.getFieldType()

    # custom DATE field type are considered as DATETIME stansard ones
    if fieldtype == 'DATE':
        fieldtype = 'DATETIME'

    if fieldtype == 'DATAGRID':
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
        if fieldtype not in ('TEXT', 'NUMBER', ):
            fieldtemplate = db.getRenderingTemplate('%sFieldRead' % fieldtype) \
                or db.getRenderingTemplate('DefaultFieldRead')
            renderedValue = fieldtemplate(fieldname=fieldname,
                fieldvalue = item_value,
                selection = field.getSettings().getSelectionList(doc),
                field = field,
                doc = doc
            ).strip()
        else:
            # trying to increase speed
            renderedValue = '%s' % item_value
        key = prefix + fieldname
        req.append((key, renderedValue, ))

    return req


def serialDoc(doc, nest_datagrid=True, serial_as='json', field_list=[]):
    """
    Take a Plomino document :doc: and extract its data in a JSON-serializable
    structure for printing porposes.
    Item values are renderized according to the field definition and only
    defined fields will be considered.
    """

    # bad_items are indistinguishable from good behaved citizen: they are unicode values
    # that just don't belong to the data (they are in fact metadata)
    # We want to skip those, and to do that we must explicitly list 'em
    bad_items = ['Plomino_Authors', 'Form']

    res = []
    form = doc.getForm()
    fieldlist = field_list or [i.id in form.getFormFields(includesubforms=True, doc=None, applyhidewhen=False)]
    for itemname in fieldlist:
    #for field in form.getFormFields(includesubforms=True, doc=None, applyhidewhen=False):
    #for itemname in doc.getItems():
        #itemname = field.id
        if itemname not in bad_items:
            itemvalue = doc.getItem(itemname, '') or ''
            fieldname = itemname
            res += serialItem(form, fieldname, itemvalue, doc=doc, nest_datagrid=nest_datagrid)

    if serial_as == 'json':
        return json_dumps(dict(res))
    elif serial_as == 'xml':
        from dict2xml import dict2xml
        return dict2xml(dict(res))
    else:
        return res

def idx_createFieldIndex(plominoIndex, fieldname, fieldtype='TEXT', **args):
    """
    Espongo il metodo protetto createFieldIndex
    
    definizione:
    createFieldIndex(self, fieldname, fieldtype, refresh=True, indextype='DEFAULT')
    """
    
    if not hasattr(plominoIndex, 'createFieldIndex'):
        plominoIndex = plominoIndex.getParentDatabase().getIndex()
    
    if not fieldname in plominoIndex.indexes():
        plominoIndex.createFieldIndex(fieldname, fieldtype, **args)

def getIndexType(plominoContext, key):
    """
    """
    indexes = plominoContext.getParentDatabase().getIndex().Indexes
    return '%s' % indexes[key]
    




    
