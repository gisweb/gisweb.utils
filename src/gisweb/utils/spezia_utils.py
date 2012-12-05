# - coding: utf-8 -

from lxml import etree
import xmlrpclib
from datetime import datetime

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

try:
  from lxml import ElementTree
except ImportError:
  try:
    # Python 2.5
    import xml.etree.cElementTree as ElementTree
  except ImportError:
    try:
      # Python 2.5
      import xml.etree.ElementTree as ElementTree
    except ImportError:
      try:
        # normal cElementTree install
        import cElementTree as ElementTree
      except ImportError:
        try:
          # normal ElementTree install
          import elementtree.ElementTree as ElementTree
        except ImportError:
            logger.error("No ElementTree found")

# nel caso in cui questo file venga usato nelle Extensions ho riscontrato difficoltà
# nell'importazione di moduli locali per cui i file XmlDict e UnicodeDammit
# vanno accodati al presente. È sufficiente fare:
# cat path/to/XmlDict.py >> path/to/spezia_utils.py
# cat path/to/UnicodeDammit.py >> path/to/spezia_utils.py

try:
    from XmlDict import XmlDictConfig
except ImportError:
    pass

try:
    from UnicodeDammit import UnicodeDammit
except ImportError:
    pass

def guess_resp(appid=None):
    '''
    indovina il responsabile per la protocollazione in base al tipo di richiesta.
    '''

    responsabili_noti = dict(
        cantieri = 'ceccla57',
        trasporti = 'traale71',
        scavi = 'dammau54'
    )
    return responsabili_noti.get(appid) or 'dammau54'

def initBody4spezia():
    '''
    inizializzazione delle sezioni utili del file xml da passare al servizio di
    protocollazione
    '''

    segnatura_info = {'{http://www.w3.org/XML/1998/namespace}lang': 'it'}
    segnatura = etree.Element('Segnatura', encoding='ISO-8859-1', **segnatura_info)

    doc = etree.ElementTree(segnatura)

    intestazione = etree.SubElement(segnatura, 'Intestazione')

    identificatore = etree.SubElement(intestazione, 'Identificatore')

    parent = etree.SubElement(identificatore, 'CodiceAmministrazione')
    id_aoo = etree.SubElement(identificatore, 'CodiceAOO')
    idRichiesta = etree.SubElement(identificatore, 'NumeroRegistrazione')
    tiporegistrazione = etree.SubElement(identificatore, 'TipoRegistrazione')
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

    '''
    funzione per la compilazione del documento xml per la protocollazione.

    Problema riscontrato:
    * Nel caso di velore unicode è necessario un encode seguito da decode,
    altrimenti i caratteri accentati non vengono accettati dallalibreria lxml.
    * Nel caso di valore unicode con codifica ignota diversa da quella di sistema
    ho usato la classe UnicodeDammit per farmi restituire una stringa unicode
    nella codifica di sistema e quindi nota (UTF8).
    '''

    data_segnatura = data_segnatura or datetime.now().strftime('%Y-%m-%d')
    data = locals()
    kwdata = data.pop('kwdata')
    data.update(kwdata)

    bodyParts = initBody4spezia()

    for k,v in data.items():
        if k in bodyParts:

            if hasattr(v, 'strftime'):
                flag = v.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(v, str):
                flag = unicode(v).encode('utf8').decode('utf8')
            elif isinstance(v, unicode):
                fix = UnicodeDammit(v).unicode
                flag = fix.encode('utf8').decode('utf8')
            else:
                flag = str(v)

            bodyParts[k].text = flag

    xmlfile = StringIO()
    bodyParts['doc'].write(xmlfile)
    body = xmlfile.getvalue()
    xmlfile.close()

    return body

def get_id_request(adapter=None, data={}):
    '''
    restituisce l'id della richiesta come progressivo contenuto nella tabella
    "richiesta_protocollo" nello schema "istanze" del database "sitar" raggiungibile
    o mediante sqlalchemy adapter o con Z SQL method.
    In mancanza di tali informazioni l'id viene ricavato dai secondi della data
    UNIX attuale.
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
            # adapter è uno Z SQL Method e deve contenere la seguente query:
            # INSERT INTO istanze.richiesta_protocollo(tipologia,utente,tms_req,pid)
            #    VALUES('$data[tipo]','$data[username]',$t,$pid);
            # SELECT id FROM istanze.richiesta_protocollo
            #    WHERE tipologia='$data[tipo]' and utente='$data[username]' and tms_req=$t;
            pid = adapter(**data)[0]['id']

    return pid

def xml2obj(xml):
    '''
    Converte un xml in un dizionario.
    Utile per accedere ai contenuti della risposta xml del servizio di protocollazione.

    Non restituisce direttamente l'oggetto XmlDictConfig per aggirare problemi
    di permessi di Plone.
    '''

    root = ElementTree.XML(xml)
    out = dict()
    out.update(XmlDictConfig(root))

    return out


def protocolla(served_url,
    responseURL,
    adapter=None,
    **kwargs):
    """
    served_url: URL chiamante
    adapter: può essere il nome di una sessione SQLAlchemy, uno Z SQL Method o None
    responseURL: URL del servizio ws_protocollo
    kwargs: dizionario contenente le informazioni per costrure l'XML per la protocollazione

    Questa funzione interroga la funzione "accoda" del servizio di protocollazione.
    """

    now = datetime.now()
    kwargs['responseURL'] = responseURL
#    if not 'username' in kwargs:
#        kwargs['username'] = guess_resp(appid=kwargs['tipo'])

    xml_content = getXmlBody(**kwargs)

    date_req = kwargs.get('data_segnatura') or now
    data = dict(
        tipologia = kwargs['tipo'],
        utente = kwargs['username'],
        tms_req = date_req.strftime('%s'),
        pid = kwargs['pid']
    )

    date = data['tms_req']

    num = get_id_request(adapter=adapter, data=data)

    if kwargs.get('test'):
        return dict(numero=num)

    server = xmlrpclib.Server(responseURL)
    response = server.accoda(date, num, served_url, xml_content.encode('base64')).decode('base64')

    return xml2obj(response)

def get_params(doc, tipo, **kwargs):
    '''
    Ricava dal plominoDocument di una istanza scavi i paramtri utili alla
    protocollazione. I parametri in kwargs vengono settati così come sono.
    '''

    params = dict()
    for par in ('oggetto', 'indirizzo', 'comune', 'cap', 'prov', ):
        params[par] = doc.getItem(par, '')

    params['tipo'] = '%s' % tipo
    params['data_segnatura'] = doc.getItem('data_presentazione', datetime.now())
    params['pid'] = doc.getId()
    current_usr = doc.getParentDatabase().getCurrentUser()
    params['username'] = current_usr.getProperty('fullname') or current_usr.getProperty('id')

    # i valori in kwargs eventualmente sovrascrivono quelli settati sopra
    params.update(kwargs)

    return params

def protocolla_doc(doc, tipo, served_url,
    responseURL = 'http://protocollo.spezia.vmserver/ws_protocollo.php', # servizio di test,
    adapter = None,
    refresh_index = True):
    '''
    in place function
    funzione inutile... non è detto che queste operazioni possano o debbano
    essere fatte tutte.
    '''

    kwargs = get_params(doc, tipo)

    resp = protocolla(served_url,
        responseURL = responseURL,
        adapter=adapter,
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
    '''
    da script non è possibile testere valori del parametro tester diversi da None.
    '''

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
