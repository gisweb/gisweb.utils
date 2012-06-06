#!/usr/bin/python
# -*- coding: utf-8 -*-

from Products.CMFPlomino.interfaces import IPlominoDatabase

def get_parent_plominodb(obj):
    ''' Return the current plominoDatabase. Is enough to pass the context from
        within a scipt or a plominoDocument python formula.
    '''
    current = obj
    while hasattr(current, 'aq_parent') and not IPlominoDatabase.providedBy(current):
        current = current.aq_parent
    return hasattr(current, 'aq_parent') and current

def search_around(plominoDocument, parentKey='parentDocument', *targets, **filters):
    '''
    DA TESTARE
    
    "out" è un dizionario la cui chiavi sono le stringhe contenute in targets se
    per esse è stato trovato almeno un valore tra i documenti collegati al
    plominoDocument (compreso lo stesso). Se i valori trovati per la chiave
    richiesta fossero più di uno questi vengono messi in una lista. Per ottenere
    meno valori è possibile affinare la ricerca fornendo le chiavi "filters" che
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
    filters[parentKey] = plominoDocument.id
    res = plominoIndex.dbsearch(**filters)
    for rec in res:
        pd = rec.getObject()
        
        # nel caso le chiavi in filters non fossero state indicizzate
        #+ evito i documenti che sarebbero stati scartati dalla ricerca
        #+ DA RIVEDERE E CORREGGERE
        if all([pd.getItem(k)==filters.get(k) for k in pd.getForm().getFormFields() if k in filters]):

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
