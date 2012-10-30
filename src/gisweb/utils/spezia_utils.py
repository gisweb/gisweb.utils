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
    return esponsabili_noti.get(appid) or 'dammau54'

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

    data_segnatura = data_segnatura or datetime.now().strftime('%Y-%m-%d')
    data = locals()
    kwdata = data.pop('kwdata')
    data.update(kwdata)

    bodyParts = initBody4spezia()

    for k,v in data.items():
        if k in bodyParts:
            bodyParts[k].text = v
    
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
                from db_utils import get_session, SqlSoup
            except ImportError:
                from gisweb.utils import get_session, SqlSoup
            session = get_session(adapter)
            if session:
                engine = session.get_bind()
                db = SqlSoup(engine)
                table = db.entity('richiesta_protocollo', schema='istanze')
                # TO DO: trovare il modo di recuperare in maniera rigorosa l'id del 
                # record appena inserito.
                table.insert(**data)
                pid = table.filter_by(**data).one().id
                db.commit()
            else:
                raise IOError('Error! No session found with name %s'  % adapter)
        else:
            # adapter è uno Z SQL Method contenente la seguente query:
            # INSERT INTO istanze.richiesta_protocollo(tipologia,utente,tms_req,pid)
            #    VALUES('$data[tipo]','$data[username]',$t,$pid);	
            # SELECT id FROM istanze.richiesta_protocollo
            #    WHERE tipologia='$data[tipo]' and utente='$data[username]' and tms_req=$t;
            pid = adapter(**data)[0]['id']
    return pid

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
        kwargs['username'] = guess_resp(appid=kwargs['tipologia'])

    xml_content = getXmlBody(**kwargs)

    corr = dict(tipo='tipologia', username='utente', data_segnatura='tms_req')
    data = dict([(c2, kwargs[c1]) for c1,c2 in corr.items()])
    if not 'tms_req' in data:
        data['tms_req'] = now.strftime('%s')
    data['pid'] = kwargs.get('pid')
    date = datetime.datetime.strptime(data['tms_req'], '%s').strftime('%Y-%m-%d %H:%M:%S')
    
    num = get_id_request(adapter=adapter, data=data)

    server = xmlrpclib.Server(responseURL)
    # da testare il formato di date: %Y-%m-%d %H:%M:%S ???
    response = server.accoda(date, num, served_url, xml_content.encode('base64'))
    return response.decode('base64')

if __name__ == '__main__':
    served_url = "http://iol.vmserver/scavicantieri/application/test"
    #now = datetime.now().strftime('%Y-%m-%d')
    kwargs ={'username': u'pippo', 'comune': 'La Spezia',
        'oggetto': 'A247\r\nscavo per nuovo allacciamento rete idrica \r\nVia Toti ',
        'indirizzo': 'via a picco 22', 'provincia': 'SP', 'tipo': 'scavi', 'cap': '19100',
        'nominativo': 'dimattia mirko'}
    #print getXmlBody(**kwargs)
    adapter = 'sitar'

    print protocolla(served_url,
        adapter=adapter,
        responseURL = 'http://protocollo.spezia.vmserver/ws_protocollo.php', **kwargs)
    
