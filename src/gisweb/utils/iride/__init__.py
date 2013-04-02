from AccessControl import allow_module, ModuleSecurityInfo
#from z3c.saconfig import named_scoped_session

allow_module('gisweb.utils.iride')

from gisweb.utils.plomino_utils import serialDoc
from plomino_conversion import get_tabledata_for
from concessioni_strada import insert_documento


def inserisci_protocollo(doc, tipo, oggetto, data):
    """
    doc -> PlominoDocument da protocollare
    tipo -> 'E' per 'Entrata' o 'U' per 'Uscita'
    data -> una data
    """
    res = insert_documento(doc)    
    return {'numero': res[0], 'data': str(res[1])}
