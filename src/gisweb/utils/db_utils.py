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

def get_soup(sessionname):
    session = get_session(sessionname)
    engine = session.get_bind()
    return SqlSoup(engine)

def execute_sql(sessionname, statement, method='fetchall', *multiparams, **params):
    session = get_session(sessionname)
    engine = session.get_bind()
    result = engine.execute(statement, *multiparams, **params)
    return getattr(result, method)()

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

#def getDatabase(sessionname):
#    session = get_session(sessionname)
#    engine = session.get_bind()
#    return SqlSoup(engine)

def suggestFromTable(sessionname, name, columnname, others=[], schema='public', tip='', **filters):
    '''
    utile per l'implementazione di semplici servizi di auto-suggest da tabella.
    sessionname: neme della sessione
    name: nome della tabella
    columnname: nome della colonna da cui attingere
    others: altre colonne cui si è interessati al valore. Usare '' per tutte.
    schema: nome dello schema di appartenenza della tabella
    tip: "suggerimento"
    filters: filtri aggiuntivi del tipo <chiave>=<valore>
    '''

    session = get_session(sessionname)
    engine = session.get_bind()
    db = SqlSoup(engine)
    table = db.entity(name, schema=schema)

    if isinstance(others, (list, tuple)):
        # you can submit a list of column values to return, at least an empty list
        query = session.query(*[table.c[col] for col in [columnname]+list(others)])
    elif others == 'filters_only':
        # easter egg: useful?
        query = session.query(*[table.c[col] for col in [columnname]+filters.keys()])
    else:
        # otherwise all columns will be returned
        query = table

    column = table.c[columnname]
    tip = tip.rstrip()

    # ilike '%(tip)s%%'
    where = or_(column.startswith(tip),
        column.startswith(tip.capitalize()),
        column.startswith(tip.title()),
        column.startswith(tip.lower()),
        column.startswith(tip.upper()))
    # other simple filters
    where = and_(where, *[(table.c[k]==v) for k,v in filters.items() if k in table.c.keys()])

    return [row.__dict__ for row in query.filter(where).all()]