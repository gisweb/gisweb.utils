# - coding: utf-8 -

from lxml import etree
import xmlrpclib
from datetime import datetime
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

def guess_resp(appid=None):
    responsabili_noti = dict(
        cantieri = 'ceccla57',
        trasporti = 'traale71'
    )
    return responsabili_noti.get(appid) or 'dammau54'

def initBody4spezia():

#    page = etree.Element('xml', version='1.0', encoding='ISO-8859-1')
    
    segnatura_info = {'{http://www.w3.org/XML/1998/namespace}lang': 'it'}
    segnatura = etree.Element('Segnatura', **segnatura_info)
    
    doc = etree.ElementTree(segnatura)
    
#    segnatura_info = {'{http://www.w3.org/XML/1998/namespace}lang': 'it'}
#    segnatura = etree.SubElement(page, 'Segnatura', **segnatura_info)
    
    intestazione = etree.SubElement(segnatura, 'Intestazione')

    identificatore = etree.SubElement(intestazione, 'Identificatore')

    parent = etree.SubElement(identificatore, 'CodiceAmministrazione')
    id_aoo = etree.SubElement(identificatore, 'CodiceAOO')
    idRichiesta = etree.SubElement(identificatore, 'NumeroRegistrazione')
    data_segnatura = etree.SubElement(identificatore, 'DataRegistrazione')
    
    origine = etree.SubElement(intestazione, 'Origine')

    indirizzotelematico = etree.SubElement(origine, 'IndirizzoTelematico')
    mittente = etree.SubElement(origine, 'Mittente')

    amministrazione = etree.SubElement(mittente, 'Amministrazione')
    nominativo = etree.SubElement(amministrazione, 'Denominazione')
    unitaorganizzativa = etree.SubElement(amministrazione, 'UnitaOrganizzativa')
    denominazione = etree.SubElement(unitaorganizzativa, 'Denominazione')
    indirizzopostale = etree.SubElement(unitaorganizzativa, 'IndirizzoPostale')
    indirizzo = etree.SubElement(indirizzopostale, 'Toponimo')
    civico = etree.SubElement(indirizzopostale, 'Civico')
    cap = etree.SubElement(indirizzopostale, 'CAP')
    comune = etree.SubElement(indirizzopostale, 'Comune')
    provincia = etree.SubElement(indirizzopostale, 'Provincia')
    
    aoo = etree.SubElement(mittente, 'AOO')
    denominazione = etree.SubElement(aoo, 'Denominazione')
    
    destinazione = etree.SubElement(intestazione, 'Destinazione', confermaRicezione='si')
    IndirizzoTelematico = etree.SubElement(destinazione, 'IndirizzoTelematico', tipo='uri')
    
    risposta = etree.SubElement(intestazione, 'Risposta')
    responseURL = etree.SubElement(risposta, 'IndirizzoTelematico')
    
    riservato = etree.SubElement(intestazione, 'Riservato')
    riservato.text = 'N'
    
    oggetto = etree.SubElement(intestazione, 'Oggetto')
    note = etree.SubElement(intestazione, 'Note')
    
    riferimenti = etree.SubElement(segnatura, 'Riferimenti')
    
    contestoprocedurale = etree.SubElement(riferimenti, 'ContestoProcedurale')
    
    utenteProtocollatore  = etree.SubElement(contestoprocedurale, 'CodiceAmministrazione')
    cp_aoo = etree.SubElement(contestoprocedurale, 'CodiceAOO')
    identificativo = etree.SubElement(contestoprocedurale, 'Identificativo')
    tipocontesto = etree.SubElement(contestoprocedurale, 'TipoContestoProcedurale')
    classifica0 = etree.SubElement(contestoprocedurale, 'Classifica')

    titolario = etree.SubElement(classifica0, 'Livello')
    classifica = etree.SubElement(classifica0, 'Livello')
    cl_l3 = etree.SubElement(classifica0, 'Livello')
    cl_l3.text = '0'
    
    descrizione = etree.SubElement(segnatura, 'Descrizione')
    documento = etree.SubElement(descrizione, 'Documento', tipoRiferimento='MIME')
    
    return locals()

def getXmlBody(
        data_segnatura = None,
        parent = '86',
        titolario = '6',
        classifica = '7',
        tipocontesto = 'IndicazioneClassificazione',
        utenteProtocollatore = 'dammau54',
        **kwdata):

    from json_utils import json_dumps

    data_segnatura = data_segnatura or datetime.now().strftime('%Y-%m-%d')
    data = locals()
    kwdata = data.pop('kwdata')
    data.update(kwdata)

    bodyParts = initBody4spezia()

    for k,v in data.items():
        if k in bodyParts:
            if isinstance(v, basestring):
                flag = v
            elif hasattr(v, 'strftime'):
                flag = v.strftime('%Y-%m-%d %H:%M:%S')
            else:
                flag = '%s' % v
            bodyParts[k].text = flag.encode('utf-8')
    
    xmlfile = StringIO()
    bodyParts['doc'].write(xmlfile)
    body = xmlfile.getvalue()
    xmlfile.close()

    return body

def get_id_request(adapter=None, data={}):
    '''
    returns '<int>', '%Y-%m-%d %H:%M:%S'
    per ora ricaviamo num dai secondi della data odierna dal 1/1/1970
    poi si userà un progressivo ricavato da una tabella in database.
    '''
    now = datetime.now()
    num = now.strftime('%s')
    pid = num
    if adapter:
        if isinstance(adapter, basestring):
            # adapter è una connessione SQLAlchemy
            try:
                from db_utils import get_soup
            except ImportError:
                from gisweb.utils import get_soup

            db = get_soup(adapter)
            table = db.entity('richiesta_protocollo', schema='istanze')
            # TO DO: trovare il modo di recuperare in maniera rigorosa l'id del 
            # record appena inserito.
            table.insert(**data)
            pid = table.filter_by(**data).one().id
            db.commit()

        else:
            # adapter è uno Z SQL Method contenente la seguente query:
            # INSERT INTO istanze.richiesta_protocollo(tipologia,utente,tms_req,pid)
            #    VALUES('$data[tipo]','$data[username]',$t,$pid);	
            # SELECT id FROM istanze.richiesta_protocollo
            #    WHERE tipologia='$data[tipo]' and utente='$data[username]' and tms_req=$t;
            pid = adapter(**data)[0]['id']
    return pid

def xml2obj(xml):

    try:
        import cElementTree as ElementTree
    except ImportError:
        import ElementTree

    from XmlDict import XmlDictConfig

    root = ElementTree.XML(xml)
    return XmlDictConfig(root)


def protocolla(served_url, adapter=None,
    responseURL = 'http://protocollo.spezia.vmserver/ws_protocollo.php', # servizio di test
    **kwargs):
    """
    served_url: URL dello script chiamante
    adapter: può essere il nome di una sessione SQLAlchemy, uno Z SQL Method o None
    responseURL: URL del servizio ws_protocollo
    kwargs: dizionario contenente le informazioni per costrure l'XML per la protocollazione
    """
    now = datetime.now()
    kwargs['responseURL'] = responseURL
    if not 'username' in kwargs:
        kwargs['username'] = guess_resp(appid=kwargs['tipo'])

    xml_content = getXmlBody(**kwargs)

    date_req = kwargs.get('data_segnatura') or now
    data = dict(
        tipologia = kwargs['tipo'],
        utente = kwargs['username'],
        tms_req = date_req.strftime('%s'),
        pid = kwargs.get('pid')
    )

    date = data['tms_req']
    
    num = get_id_request(adapter=adapter, data=data)

    server = xmlrpclib.Server(responseURL)
    response = server.accoda(date, num, served_url, xml_content.encode('base64')).decode('base64')
    
    return xml2obj(response)

def get_params(doc, tipo, **kwargs):
    
    params = dict()
    for par in ('oggetto', 'indirizzo', 'comune', 'cap', 'prov', ):
        params[par] = doc.getItem(par, '')
    
    params['tipo'] = '%s' % tipo
    
    params['data_segnatura'] = doc.getItem('data_presentazione', datetime.now())
    
    params.update(kwargs)

    return params

def protocolla_doc(doc, tipo, served_url, responseURL,
    adapter=None,
    refresh_index = True
    ):
    '''
    in place function
    '''

    kwargs = get_params(doc, tipo)

    resp = protocolla(served_url, adapter=adapter,
        responseURL = responseURL,
        **kwargs)
    
    doc.setItem('protocollo', '%s' % resp['numero'])
    
    # coutesy of: https://github.com/plomino/Plomino/blob/github-main/Products/CMFPlomino/PlominoDocument.py
    # in save
    if refresh_index:
        db = doc.getParentDatabase()
        # update index
        db.getIndex().indexDocument(doc)
        # update portal_catalog
        if db.getIndexInPortal():
            db.portal_catalog.catalog_object(doc, "/".join(db.getPhysicalPath() + (self.id,)))

if __name__ == '__main__':
    served_url = "http://iol.vmserver/scavicantieri/application/test"
    #now = datetime.now().strftime('%Y-%m-%d')
    kwargs = {'username': u'pippo', 'comune': 'La Spezia',
        'oggetto': 'A247\r\nscavo per nuovo allacciamento rete idrica \r\nVia Toti ',
        'indirizzo': 'via a picco 22', 'provincia': 'SP', 'tipo': 'scavi',
        'data_segnatura': '2011-07-13 14:48:03', 'cap': '19100', 'nominativo': 'dimattia mirko'}
    #print getXmlBody(**kwargs)
    adapter = None

    print protocolla(served_url,
        adapter=adapter,
        responseURL = 'http://protocollo.spezia.vmserver/ws_protocollo.php', **kwargs)
    
