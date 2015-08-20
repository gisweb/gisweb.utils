from Products.CMFPlomino.PlominoUtils import json_dumps
from Products.CMFPlone.utils import safe_unicode
from gisweb.utils import Type
from DateTime import DateTime
from Products.CMFPlomino.PlominoUtils import DateToString, StringToDate, htmlencode

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


def renderSimpleItem(db, doc, itemvalue, render, field, fieldtype):
    """ How simple item values are rendered """

    if not fieldtype:
        fieldtype = field.getFieldType()

    renderedValue = None
    # if I need data representation (or metadata) for printing porposes
    if itemvalue and render and field:
        if fieldtype == 'SELECTION':
            nfo = dict([i.split('|')[::-1] for i in field.getSettings().getSelectionList(doc)])
            if isinstance(itemvalue, basestring):
                renderedValue = nfo.get(itemvalue) or itemvalue
            else:
                renderedValue = [(nfo.get(i) or i) for i in itemvalue]

        elif fieldtype not in ('TEXT', 'NUMBER', ):
            # not worth it to call the template to render text and numbers
            # it is an expensive operation
            fieldtemplate = db.getRenderingTemplate('%sFieldRead' % fieldtype) \
                or db.getRenderingTemplate('DefaultFieldRead')
            renderedValue = fieldtemplate(fieldname=name,
                fieldvalue = itemvalue,
                selection = field.getSettings().getSelectionList(doc),
                field = field,
                doc = doc
            ).strip()

    # if I need data value
    if renderedValue==None:
        if not itemvalue:
            renderedValue = ''
        elif fieldtype == 'TEXT':
            renderedValue = safe_unicode(str(itemvalue)).encode('utf-8').decode('ascii', 'ignore')
        elif fieldtype == 'NUMBER':
            if render:
                custom_format = None if not field else field.getSettings('format')
                renderedValue = str(itemvalue) if not custom_format else custom_format % itemvalue
            else:
                renderedValue = itemvalue
        elif fieldtype == 'DATETIME':
            if field:
                custom_format = field.getSettings('format') or db.getDateTimeFormat()
            else:
                custom_format = db.getDateTimeFormat()
            renderedValue = itemvalue.strftime(custom_format)
        else:
            # in order to prevent TypeError for unknown not JSON serializable objects
            try:
                json_dumps(itemvalue)
            except TypeError:
                renderedValue = u'%s' % itemvalue
            else:
                renderedValue = itemvalue
    return renderedValue


def serialItem(doc, name, fieldtype=None, nest=True, render=True, follow=True, fieldsubset=[], fieldnames=[]):
    """
    Returns a list of 2-tuples with the data contained in the document item

    doc         : the PlominoDocument;
    name        : the item name;
    nest        : whether the fields of type DATAGRID and DOCLINK has to be
                  serialized nested in a list;
    render      : if you are interested in the data value serialization
                  set it to False, otherwise you'll obtain the data renderization
                  through the item basic read template,
    follow      : follow doclink?
    """

    result = list()
    itemvalue = doc.getItem(name)
    db = doc.getParentDatabase()

    form = doc.getForm()
    if not fieldnames:
        fieldnames = [i.getId() for i in form.getFormFields(includesubforms=True, doc=None, applyhidewhen=False)]

    if name in fieldnames:
        field = form.getFormField(name)
        fieldtype = field.getFieldType()
    else:
        field = None
        # try a guess
        if isinstance(itemvalue, (int, float, )):
            fieldtype = 'NUMBER'
        elif isinstance(itemvalue, DateTime):
            fieldtype = 'DATETIME'
        # by-pass Plone error using isinstance as in other cases
        # using isinstance(itemvalue, list) I get
        # TypeError: isinstance() arg 2 must be a class, type, or tuple of classes and types
        # even if "list" is a class itself
        elif 'list' in Type(itemvalue):
            fieldtype = 'SELECTION'
        # good for everyone
        else:
            fieldtype = 'TEXT'


    assert fieldtype, 'No fieldtype is specified for "%(name)s" with value "%(itemvalue)s"' % locals()

    # arbitrary assumption
    if fieldtype == 'DATE':
        fieldtype = 'DATETIME'

    if fieldtype == 'DATAGRID' or (follow and fieldtype == 'DOCLINK'):
        #result.append((name, fieldtype))
        if nest:
            sub_result = list()

        if fieldtype == 'DATAGRID':
            grid_form = db.getForm(field.getSettings().associated_form)
            grid_field_names = field.getSettings().field_mapping.split(',')

        for innervalue in itemvalue or []:
            if fieldtype == 'DOCLINK':
                sub_doc = db.getDocument(innervalue)
                sub_element = dict(sub_doc.serialDoc(fieldsubset=fieldsubset, nest=nested, render=render, follow=False))
            else:
                sub_element = dict([(
                    k, renderSimpleItem(db, doc, v, render,
                        grid_form.getFormField(k),
                        None)
                ) for k,v in zip(grid_field_names, innervalue)])

            if nest:
                sub_result.append(sub_element)
            else:
                result += [('%s.%s' % (name, k), v) for k,v in sub_element.items()]

        if nest:
            result.append((name, sub_result))

    else:
        renderedValue = renderSimpleItem(db, doc, itemvalue, render, field, fieldtype)
        #key = prefix + fieldname
        result.append((name, renderedValue, ))
    return dict(result)
    
    
def serialDoc(doc, fieldsubset=[], nest=True, render=True, follow=False):
    """
    Take a Plomino document :doc: and extract its data in a JSON-serializable
    structure for printing porposes. Item values are renderized according to
    the field definition and by default only defined fields will be considered.

    doc          : the PlominoDocument that contains data to serialize;
    fieldsubset : subset of item to be serialized, you can just specify the
                   list if item name you need;
    nest         : whether the fields of type DATAGRID and DOCLINK has to be
                   serialized nested in a list;
    render       : if True Item values are renderized according to the field
                   definition and by default only defined fields will be considered.
    format       : json/xml;
    follow      : follow doclink?
    """

    form = doc.getForm()
    fieldnames = [i.getId() for i in form.getFormFields(includesubforms=True, doc=None, applyhidewhen=False)]

    contentKeys = fieldnames + [i for i in doc.getItems() if i not in fieldnames]
    if fieldsubset:
        contentKeys = [i for i in contentKeys if i in fieldsubset]

    result = [] if not get_id else [('id', doc.getId(), )]
    for key in contentKeys:
        result += doc.serialItem(key, nest, render=render, follow=follow, fieldsubset=fieldsubset, fieldnames=fieldnames)
    return result

        
