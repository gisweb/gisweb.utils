from AccessControl import allow_module, ModuleSecurityInfo
#from z3c.saconfig import named_scoped_session

allow_module('gisweb.utils.iride')

#from gisweb.utils.plomino_utils import serialDoc
from plomino_conversion import get_tabledata_for
from concessioni_strada import insert_documento, insert_documento2, prepare_string
from concessioni_strada import IrideProtocollo, IrideProcedimento

def inserisci_protocollo_old(doc, tipo, oggetto, data):
    """
    doc -> PlominoDocument da protocollare
    tipo -> 'E' per 'Entrata' o 'U' per 'Uscita'
    data -> una data
    """
    if 'get_iride_data' in doc.getParentDatabase().resources.keys():
        return insert_documento2(doc)
    res = insert_documento(doc)    
    return {'numero': res[0], 'data': str(res[1])}


#                                                                              NEW

def leggi_documento(docid, **kw):
    """
    Returns the data of a document starting from their iride identifier (IdDocumento).

    Args:
        docid (int): the document identifier.
    """
    conn = IrideProtocollo(**kw)
    return conn.LeggiDocumento(docid)

def lista_procedimenti(testinfo=False, **kw):
    """
    Extraction of the proceedings of a subject.

    Acceped keyword args:
        CodiceFiscale (str): personal fiscal code;
        SessionID (int):
        DataInizio (DateTime):
        DataFine (DateTime):
        Stato (str):
    """
    conn = IrideProcedimento(testinfo=testinfo)
    return conn.ListaProcedimenti(**kw)

def leggi_procedimento(IDProcedimento, testinfo=False, **kw):
    """
    Extracts detail data of proceedings

    Args:
        IDProcedimento (int): proceeding Iride idetifier
    """
    conn = IrideProcedimento(testinfo=testinfo)
    return conn.DettaglioProcedimento(IDProcedimento, **kw)

def test_ListaProcedimenti(testinfo=True, **kw):
    """ Test: ricavo e visualizzo il formato del template xml ListaProcedimenti """
    conn = IrideProcedimento(testinfo=testinfo)
    return conn.build_xml('ListaProcedimenti', **kw)

def inserisci_protocollo(doc, testinfo=False):
    """
    doc (PlominoDocument): the document to be registered;
    testinfo (bool): whether debug info has to be added to the result.
    """

    conn = IrideProtocollo(testinfo=testinfo)

    layer = doc.getParentDatabase().resources.irideLayer
    dati_protocollo = layer('ProtocolloIn', doc)
    dati_mittente = layer('MittenteDestinatarioIn', doc)
    dati_allegato = layer('AllegatoIn', doc)
    
    res_protocollo = conn.InserisciProtocollo(
        mittenti=[dati_mittente],
        allegati=[dati_allegato],
        **dati_protocollo
    )
    res_utente = None
    if res_protocollo['success']:
        if not res_protocollo['result'].get('Errore'):
            docid = res_protocollo['result']['IdDocumento']
            dati_utente = layer('DatiUtenteIn', doc)
            res_utente = conn.InserisciDatiUtente(docid, dati_utente)
            doc.setItem('irideIdDocumento', docid)
    
    return (res_protocollo, res_utente, )

def inserisci_documento(doc, testinfo=False):
    conn = IrideProtocollo(testinfo=testinfo)

    layer = doc.getParentDatabase().resources.irideLayer
    dati = layer('ProtocolloIn', doc)
    dati_mittente = layer('MittenteDestinatarioIn', doc)
    dati_allegato = layer('AllegatoIn', doc)

    return conn.InserisciDocumentoEAnagrafiche(mittenti=[dati_mittente], allegati=[dati_allegato], **dati)

def inserisci_procedimento(doc, testinfo=False):
    """ """

    conn = IrideProcedimento(testinfo=testinfo)

    layer = doc.getParentDatabase().resources.irideLayer
    dati_procedimento = layer('ProtocolloIn', doc)
    dati_mittente = layer('MittenteDestinatarioIn', doc)
    dati_allegato = layer('AllegatoIn', doc)

    return conn.AttivaProcedimento(mittenti=[dati_mittente], allegati=[dati_allegato], **dati_procedimento)
    
def procedimento_pratica(cf, docid, testinfo=False):
    """
    Shortcut per ricavare le informazioni del procedimento direttamente a partire
    da una pratica.
    """

    conn = IrideProcedimento(testinfo=True)
    
    # 1. si ricava la lista dei procedimenti in capo al mittente attraverso il CF
    res_procedimenti = conn.ListaProcedimenti(CodiceFiscale=cf)

    if res_procedimenti['success']:
        if not res_procedimenti['result'].get('Errore'):
            # 2. si filtra i procedimenti trovati in base al parametro IdDocumento
            flt_res = [rec['TestataProcedimento'] for rec in res_procedimenti['result']['Procedimenti']['Procedimento'] if rec['EstremiDocumento']['IdDocumento']==docid]
            if not flt_res:
                    flt_res = [{}]
            if testinfo:
                flt_res[0]['time_elapsed'] = res_procedimenti['time_elapsed']
            return flt_res[0]
        else:
            return res_procedimenti
    else:
        return res_procedimenti
    











    