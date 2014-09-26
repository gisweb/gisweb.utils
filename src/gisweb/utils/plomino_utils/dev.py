#!/usr/bin/python
# -*- coding: utf-8 -*-

from gisweb.utils.dev_utils.dev import dategenerate, numbergenerate, boolgenerate, rndselection
from gisweb.utils.dev_utils.dev import namegenerate, da_du_ma, rndCodFisco, is_valid_piva
from gisweb.utils.dev_utils.dev import cf_build

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