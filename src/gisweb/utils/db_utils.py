#!/usr/bin/python
# -*- coding: utf-8 -*-
from z3c.saconfig import named_scoped_session
from sqlalchemy import select, and_, or_, String, DateTime, create_engine
from sqlalchemy.schema import MetaData, Table, SchemaItem, Column
from sqlalchemy.ext.sqlsoup import SqlSoup
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.orm import scoped_session
import datetime

def get_something_from_db():
    session = get_session('maciste')
    # do something with session
    return "pluto"

def get_session(sessionname):
    """ Use collective.saconnect to configure connections TTW """
    factory = named_scoped_session(sessionname)
    return factory()

#def sql_test(session, tname):
#    if isinstance(session, basestring):
#        session = get_session(session)
#    
#    meta = MetaData()
#    engine = session.get_bind()
#    schema, name = tname.split('.')
#    
#    table = Table(name, meta, autoload=True, autoload_with=engine, schema=schema)
#    
#    return 1

def query_table(sessionname, name, schema='public', flt=None, test=True):
    '''
    table_infos = dict(name='<table_name>', schema='<schema_name>')
    flt = {'<column_name>': {'query': <value>, 'operator': ..., }}
    '''

    session = get_session(sessionname)
#    session = named_scoped_session(sessionname) 
    engine = session.get_bind()
    db = SqlSoup(engine)
    
    table = db.entity(name, schema=schema)
    
    if flt:
        for k,v in flt.items():
            table[k]
    
    if test:
        return table.filter(flt).all()
    else:
        return table

def suggestFromTable(sessionname, name, schema='public', columnname=None, tip='', **filters):
    session = get_session(sessionname)
    engine = session.get_bind()
    db = SqlSoup(engine)
    
    table = db.entity(name, schema=schema)
    column = table.c[columnname]
    
    ilikefilter = column.ilike(tip)
    
    return table.filter(ilikefilter).filter_by(**filters).all()
    
    
    
    

def plominoSqlSync(session, plominoDocument, **table_infos):
    """
    table_infos = dict(schema='<schema_table>')
    """
    
    if isinstance(session, basestring):
        session = named_scoped_session(session)
    
    engine = session.get_bind()
    
    db = SqlSoup(engine, session=session)
    
    table_name = plominoDocument.Form
    main_table = db.entity(table_name, **table_infos)
    
    values = dict()
    plominoItems = plominoDocument.getItems()
    for column in main_table.c:
        if column.key == u'id':
            continue
        if column.key in plominoItems and (plominoDocument.getItem(column.key, None) != None):
            values[column.key] = plominoDocument.getItem(column.key)
    
    plominoDatabase = plominoDocument.getParentDatabase()
    values[u'modified_by'] = plominoDatabase.getCurrentUser().id
    values[u'last_update'] = plominoDocument.plomino_modification_time.asdatetime()

    if plominoDocument.isNewDocument():
        values[u'plominoId'] = plominoDocument.id
        main_table.insert(**values)
    else:
        if not main_table.filter(main_table.plominoId==plominoDocument.id).update(values):
            values[u'plominoId'] = plominoDocument.id
            main_table.insert(**values)
        
    plominoForm = plominoDatabase.getForm(plominoDocument.Form)
    plominoFields = plominoForm.getFormFields(includesubforms=True, applyhidewhen=True)

    for field in plominoFields:
        if field.getFieldType() in ("DATAGRID", ) and (plominoDocument.getItem(field.id) != None):
            gridItem = plominoDocument.getItem(field.id)
            grid_table_name = field.id # oppure field.getSettings(key='associated_form') 
            try:
                grid_table = db.entity(grid_table_name, **table_infos)
            except NoSuchTableError, err:
                pass
            else:
                grid_table.filter(grid_table.parentId==plominoDocument.id).delete()

                vals = dict()
                for record in gridItem:
                    field_mapping = field.getSettings(key='field_mapping').split(',')
                    for idx,key in enumerate(field_mapping):
                        if record[idx] != None:
                            vals[key] = record[idx]
                    vals[u'parentId'] = plominoDocument.id
                    grid_table.insert(**vals)
    return                 





#type_map = dict(
#    varchar = unicode,
#    integer = int,
#    counter = int,
#    smalint = int,
#    bigint = long,
#    real = float,
#    float = float,
#    double = float,
##    date = ,
##    time = ,
##    timestamp = ,
#)

##def get_columns(session, table_name):

##    if isinstance(session, basestring):
##        session = get_session(session)

##    if '.' in table_name:
##        table_schema, table_name = '.'.split(table_name)
##        whereclause = and_("table_name = '%s'" % table_name, "schema_table = '%s'" % table_schema)
##    else:
##        whereclause = "table_name = '%s'" % table_name
##    query = select(['schema_table', 'table_name', 'udt_name'], from_obj=['information_schema.columns'], whereclause=whereclause)
##    
##    res = session.execute(query).fetchall()
##    out = dict()
##    for rec in res:
##        values = rec.values()[-1]
##        key = str('.'.join(values[:-1]))
##        out[key] = type_map.get(str(values)) or str
##    
##    return out
#    

#def get_field_types(session, table_infos):
#    '''
#    table_infos = [dict(table_schema=<schema>, table_name=<table>, column_name=<column>), ...]
#    out = dict(<schema.table.column>=func)
#    '''
#    
#    if isinstance(session, basestring):
#        session = get_session(session)
#    # tabs and schemas
#    whereclause_list = []
#    for nfo in table_infos:
#        
#        if not nfo.get('table_schema'):
#            nfo['table_schema'] = 'public'
#        
#        wcl = []
#        for key,value in nfo.items():
#            wcl += ["%s = '%s'" % (key, value, )]
#        wc = wcl[0]
#        for wce in wcl[1:]:
#            wc = and_(wc, wce)
#        whereclause_list += [wc]
#        
#    whereclause = whereclause_list[0]
#    for whereclause_el in whereclause_list[1:]:
#        whereclause = or_(whereclause, whereclause_el)
#    
#    info_fields = ['table_schema', 'table_name', 'column_name', 'udt_name']
#    info_query = select(info_fields,
#        from_obj = ['information_schema.columns'],
#        whereclause = whereclause)
#    
#    res = session.execute(info_query).fetchall()
#    
#    out = dict()
#    for rec in res:
#        schema, tabella, colonna, tipo = map(str, rec.values())
#        if schema not in out:
#            out[schema] = dict()
#        if tabella not in out[schema]:
#            out[schema][tabella] = dict()
#        out[schema][tabella][colonna] = type_map.get(tipo) or str
#    
#    return out
#    
#    
#def smart_fetch(session, columns=None, whereclause=None, from_obj=[], **kwargs):

#    if isinstance(session, basestring):
#        session = get_session(session)

#    query = select(columns=columns, whereclause=whereclause, from_obj=from_obj, **kwargs)
#    
#    result = session.execute(query).fetchall()
#    
##    types = get_field_types(session, [])
#    
#    return result


#def base_suggest(session, table_name, column_name, hint, table_schema='public'):
#    if isinstance(session, basestring):
#        session = get_session(session)  
#    whereclause = "upper(%s) LIKE '%s%%'" % (column_name, hint.upper())
#    query = select([column_name], from_obj=['.'.join([table_schema, table_name])], whereclause=whereclause)

#    out = session.execute(query).fetchall()
#    key = '.'.join([table_schema, table_name, column_name])
#    func = get_field_types(session, [dict(table_name=table_name, column_name=column_name, table_schema=table_schema)])[key]
#    
#    return [func(i.values()[0]) for i in out]
