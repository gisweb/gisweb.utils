# - coding: utf-8 -
from suds.client import Client
from datetime import datetime, date
from base64 import b64encode
from gisweb.utils.iride.plomino_conversion import FIELDS_MAP, get_tabledata_for
from DateTime import DateTime

# this url is good if you
# ssh siti.provincia.sp.it -L 3340:10.94.128.230:80 -p 2229
URL = 'http://127.0.0.1:3340/ulissetest/iride/web_services_20/WSProtocolloDM/WSProtocolloDM.asmx?WSDL'
# This one is good at Spezia
#URL = 'http://10.94.128.230/ulissetest/iride/web_services_20/WSProtocolloDM/WSProtocolloDM.asmx?WSDL'
UTENTE = 'AMMINISTRATORE'
RUOLO = 'AMMINISTRATORE'
APPARTENENZA = 'DOCUMENTO'


def prepare_string(data, docid):
    result = ["<DatiUtenteIn>"]
    for tablename, rows in data.items():
        result.append('<table name="%s">' % tablename)
        for i, row_original in enumerate(rows):
            row = dict(row_original,
                IRIDE_DOCID=docid,
                IRIDE_PROGR=i,
                IRIDE_FONTE='GW',
                IRIDE_DATINS=get_datetime(),
            )
            result.append('<row>')
            for keyvalue in row.items():
                result.append('<field name="%s">%s</field>' % keyvalue)
            result.append('</row>')
        result.append('</table>')
    result.append("</DatiUtenteIn>")
    return '\n'.join(result)


def get_datetime():
    return datetime.now().isoformat()

def insert_documento2(doc):
    "Returns IdProtocollo"
    client = Client(URL, location=URL)
    oggetto = doc.getForm().Title().decode('ascii', errors='replace').encode('ascii', errors='replace')

    protocollo = client.factory.create('ProtocolloIn')
    protocollo.Data = date.today().isoformat()
    protocollo.Oggetto = oggetto

    mittente = client.factory.create('MittenteDestinatarioIn')

    fill_from_fisica(doc, mittente)

    protocollo.MittentiDestinatari.MittenteDestinatario.append(mittente)
    protocollo.AggiornaAnagrafiche = 'F'

    protocollo.Utente = 'AMMINISTRATORE'
    protocollo.Ruolo = 'AMMINISTRATORE'
    protocollo.Origine = 'A'
    protocollo.MittenteInterno = 'PROTO02'

    #
    metadata, data = doc.getParentDatabase().resources.get_iride_data(doc)

    # faccio in modo di avre in metadata al limite i valori di default per le voci:
    # "__TipoDocumento", "__InCaricoA", "__Classifica"
    protocollo.TipoDocumento = metadata['__TipoDocumento']
    protocollo.InCaricoA = metadata['__InCaricoA']
    protocollo.Classifica = metadata['__Classifica']

    if 'domanda_inviata.pdf' in doc:
        allegato = client.factory.create('AllegatoIn')
        allegato.Image = b64encode(doc['domanda_inviata.pdf'].data)
        allegato.TipoFile = 'pdf'
        allegato.ContentType = 'application/pdf'
        protocollo.Allegati.Allegato.append(allegato)

    protocollo_out = dict(success = 0)
    try:
        res = client.service.InserisciProtocollo(protocollo)
    except Exception as err:
        protocollo_out['errors'] = '%s' % err
    else:
        protocollo_out['success'] = 1
        protocollo_out['id'] = res.IdDocumento
        if hasattr(res, 'Errore') and unicode(res.Errore):
            protocollo_out['error'] = unicode(res.Errore)
        else:
            protocollo_out['numero'] = res.NumeroProtocollo
            protocollo_out['data'] = res.DataProtocollo

    if not data:
        return protocollo_out

    xmlstring = prepare_string(data, IdDocumento)
    resp = client.service.InserisciDatiUtente(
        Appartenenza=APPARTENENZA,
        Identificativo=res.IdDocumento,
        Utente=UTENTE,
        Ruolo=RUOLO,
        DatiUtente=xmlstring,
        CodiceAmministrazione='',
        CodiceAOO=''
    )
    return protocollo_out

def insert_documento(doc):
    "Returns IdProtocollo"
    client = Client(URL, location=URL)
    oggetto = doc.getForm().Title().decode('ascii', errors='replace').encode('ascii', errors='replace')

    protocollo = client.factory.create('ProtocolloIn')
    protocollo.Data = date.today().isoformat()
    protocollo.Oggetto = oggetto

    mittente = client.factory.create('MittenteDestinatarioIn')

    fill_from_fisica(doc, mittente)

    protocollo.MittentiDestinatari.MittenteDestinatario.append(mittente)
    protocollo.AggiornaAnagrafiche = 'F'

    protocollo.Utente = 'AMMINISTRATORE'
    protocollo.Ruolo = 'AMMINISTRATORE'
    protocollo.Origine = 'A'
    protocollo.MittenteInterno = 'PROTO02'

    try:
        metadata = get_metadata_for(doc)
        protocollo.TipoDocumento = metadata['__TipoDocumento']
        protocollo.InCaricoA = metadata['__InCaricoA']
        protocollo.Classifica = metadata['__Classifica']
    except KeyError:
        protocollo.TipoDocumento = "CONSC"
        protocollo.InCaricoA = "CONCESNEW"
        protocollo.Classifica = 'XVIII.02.03.'

    if 'domanda_inviata.pdf' in doc:
        allegato = client.factory.create('AllegatoIn')
        allegato.Image = b64encode(doc['domanda_inviata.pdf'].data)
        allegato.TipoFile = 'pdf'
        allegato.ContentType = 'application/pdf'
        protocollo.Allegati.Allegato.append(allegato)

    try:
        res = client.service.InserisciProtocollo(protocollo)
    except Exception, e:
        import sys
        #type, value, tb = sys.exc_info()
        #import pdb;pdb.post_mortem(tb)
        raise e
    IdDocumento = res.IdDocumento

    if hasattr(res, 'Errore') and unicode(res.Errore):
        # XXX FIXME: working around evil error ## TODO
        # Exception from HRESULT: 0xFFFDB5F4
        print RuntimeError(unicode(res.Errore))
        import time
        #IdDocumento = int(time.mktime(time.gmtime())) - 1358700000
        #return IdDocumento, date.today()
        raise RuntimeError(unicode(res.Errore))

    plomino_table = doc.getForm().id
    if plomino_table not in FIELDS_MAP:
        return res.NumeroProtocollo, res.DataProtocollo
    data = get_tabledata_for(doc)
    xmlstring = prepare_string(data, IdDocumento)
    resp = client.service.InserisciDatiUtente(
        Appartenenza=APPARTENENZA,
        Identificativo=IdDocumento,
        Utente=UTENTE,
        Ruolo=RUOLO,
        DatiUtente=xmlstring,
        CodiceAmministrazione='',
        CodiceAOO=''
    )
    return res.NumeroProtocollo, res.DataProtocollo


def get_metadata_for(doc):
    # cerco in resources uno script chiamato get_iride_metadata che prende
    # in ingresso il PlominoDocument e restituisce la mappatura dei campi
    # corrispondente
    db = doc.getParentDatabase()
    if 'get_iride_metadata' in db.resources.keys():
        return db.resources.get_iride_metadata(doc)
    plomino_table = doc.getForm().id
    return FIELDS_MAP[plomino_table]


def fill_from_fisica(doc, obj):
    """
    obj is an instantiated MittenteDestinatarioIn-like object
    doc is a PlominoDocument.
    This function will set values on `obj` based on those on `doc`
    """
    obj.CodiceFiscale = doc.getItem('fisica_cf')
    obj.CognomeNome = "%s %s" % (doc.getItem('fisica_cognome'), doc.getItem('fisica_nome'))
    obj.Nome = doc.getItem('fisica_nome')
    obj.Indirizzo = doc.getItem('fisica_domicilio_indirizzo')
    obj.Localita = doc.getItem('fisica_residenza_loc')
    obj.DataNascita = doc.getItem('fisica_data_nato')
    ############### I have NO IDEA about how to set those: ############################
    # CodiceComuneResidenza
    # CodiceComuneNascita
    # Nazionalita
    # DataInvio_DataProt
    # Spese_NProt
    # Mezzo
    # DataRicevimento
    # TipoSogg
    # TipoPersona
    # Recapiti


def deep_normalize(d):
    """  """
    if 'sudsobject' in str(d.__class__):
        d = deep_normalize(dict(d))
    else:
        for k,v in d.iteritems():
            if 'sudsobject' in str(v.__class__):
                #print k, v, '%s' % v.__class__
                r = deep_normalize(dict(v))
                d[k] = r
            elif isinstance(v, dict):
                r = deep_normalize(v)
                d[k] = r
            elif isinstance(v, list):
                d[k] = [deep_normalize(i) for i in v]
            elif isinstance(v, datetime):
                # per problemi di permessi sugli oggetti datetime trasformo
                # in DateTime di Zope
                d[k] = DateTime(v.isoformat())
    return d

class Iride():

    HOST = 'http://127.0.0.1:3340'
    SPATH = 'ulissetest/iride/web_services_20'
    Utente = UTENTE
    Ruolo = RUOLO

    def __init__(self, SERVICE_NAME, testinfo=False, **kw):
        self.testinfo = testinfo
        for k,v in kw.items():
            setattr(self, k, v)
        self.__set_client__(SERVICE_NAME)

    def __set_client__(self, service):
        """ Returns the client asspciated to the service """
        WSProtocolloDM = 'WSProtocolloDM/WSProtocolloDM.asmx?WSDL'
        WSProcedimenti = 'WSProcedimenti/WSProcedimenti.asmx?WSDL'

        url = '/'.join((self.HOST, self.SPATH, locals()[service]))
        self.url = url
        self.client = Client(url, location=url)

    def build_xml(self, name, **kw):
        """ Generic XML helper """
        xml = self.client.factory.create(name)
        # a quanto pare iride ha qualche problema con i valori settati a None
        # come è di default per cui i valori non forniti li setto a '' (stringa vuota)
        for k,v in dict(xml).items():
            # considero SOLO gli oggetti semplici
            if v == None:
                xml[k] = kw.get(k) or ''
        return xml

    def build_obj(self, name, **kw):

        xml = self.client.factory.create(name)

        obj = dict()
        for k in dict(xml):
            obj[k] = kw.get(k) or ''
        return obj

    def build_mittente(self, **kw):
        """ XML helper for MittenteDestinatarioIn-like object creation """
        return self.build_xml('MittenteDestinatarioIn', **kw)

    def build_allegato(self, **kw):
        """ XML helper for AllegatoIn-like object creation """

        # Image parameter value is required to be base64 encoded
        # I don't know how to verify if it's already encoded so DO NOT ENCODE! I do.
        if 'Image' in kw:
            kw['Image'] = b64encode(kw['Image'].data or '')

        return self.build_xml('AllegatoIn', **kw)

    def query_service(self, service, request):
        """ Standardize the output """

        out = dict(success=0)
        if self.testinfo: t0 = datetime.now()
        try:
            if isinstance(request, dict):
                res = service(**request)
            else:
                res = service(request)
        except Exception as err:
            out['message'] = '%s' % err
            # for debug purposes in case of exception reasons are in input data
            out['request'] = deep_normalize(dict(request))
        else:
            if self.testinfo: out['time_elapsed'] = (datetime.now()-t0).seconds()
            out['success'] = 1
            out['result'] = deep_normalize(dict(res))
        return out

    def get_ProtocolloIn(self, mittenti=[], allegati=[], **kw):
        """ XML helper for ProtocolloIn-like object creation """

        defaults = dict(
            Utente = UTENTE,
            Ruolo = RUOLO,
            Origine = 'A',
            MittenteInterno = 'PROTO02',
            Data = date.today().isoformat(),
            Classifica = 'XVIII.02.03.'
        )

        request = self.build_xml('ProtocolloIn', **dict(defaults, **kw))

        for info in mittenti:
            mittente = self.build_mittente(**info)
            request.MittentiDestinatari.MittenteDestinatario.append(mittente)

        for info in allegati:
            allegato = self.build_allegato(**info)
            request.Allegati.Allegato.append(allegato)

        return request


class IrideProtocollo(Iride):
    """ A class for manage connection to WSProtocolloDM service """

    #SERVICE_NAME = 'WSProtocolloDM'

    def __init__(self, **kw):
        Iride.__init__(self, 'WSProtocolloDM', **kw)
        
    def LeggiDocumento(self, IdDocumento, **kw):
        """
        Restituisce i dati di un documento eventualmente protocollato a
        partire da IdDocumento.

        IdDocumento: identificativo del documento (str)
        """

        defaults = dict(
            Utente = UTENTE,
            Ruolo = RUOLO,
        )
        
        request = self.build_xml('LeggiDocumento',
            IdDocumento = IdDocumento,
            **dict(defaults, **kw)
        )

        return self.query_service(self.client.service.LeggiDocumento, request)

    def InserisciProtocollo(self, mittenti=[], allegati=[], **kw):
        """
        Inserisce un documento protocollato e le anagrafiche (max 100)
        ed eventualmente esegue l'avvio dell'iter.
        
        mittenti e allegati: liste di dizionari delle informazioni per la
            costruzione di oggetti xml MittenteDestinatarioIn-like e AllegatoIn-like
            attraverso i rispettivi metodi build_mittente e buil_allegato.
        """

        defaults = dict(
            Utente = UTENTE,
            Ruolo = RUOLO,
            Origine = 'A',
            MittenteInterno = 'PROTO02',
            Data = date.today().isoformat(),
            Classifica = 'XVIII.02.03.'
        )

        request = self.build_xml('ProtocolloIn', **dict(defaults, **kw))

        for info in mittenti:
            mittente = self.build_mittente(**info)
            request.MittentiDestinatari.MittenteDestinatario.append(mittente)

        for info in allegati:
            allegato = self.build_allegato(**info)
            request.Allegati.Allegato.append(allegato)

        return self.query_service(self.client.service.InserisciProtocollo, request)
        
    def InserisciDatiUtente(self, Identificativo, DatiUtente, **kw):
        """
        Inserisce i dati utente associati a un documento, un soggetto o un'attivita'

        Identificativo: identificativo del documento (str);
        DatiUtente: dizionario delle informazioni per costruire un oggetto xml
                    contenente oggetti di DatiUtenteIn-like usando la funzione
                    prepare_string;
        """

        defaults = dict(
            Utente = UTENTE,
            Ruolo = RUOLO,
            Appartenenza = APPARTENENZA,
            CodiceAmministrazione = '',
            CodiceAOO = ''
        )

        request = self.build_obj('InserisciDatiUtente',
            Identificativo = Identificativo,
            DatiUtente = prepare_string(DatiUtente, Identificativo),
            **dict(defaults, **kw)
        )
        
        return self.query_service(self.client.service.InserisciDatiUtente, request)

    def InserisciDocumentoEAnagrafiche(self, mittenti=[], allegati=[], **kw):
        """
        TODO
        Inserisce un documento non protocollato e le anagrafiche (max 100) ed
        eventualmente esegue l'avvio dell'iter
        """

        request = self.get_ProtocolloIn(mittenti=mittenti, allegati=allegati, **kw)

        return self.query_service(self.client.service.InserisciDocumento, request)

class IrideProcedimento(Iride):

    def __init__(self, **kw):
        Iride.__init__(self, 'WSProcedimenti', **kw)

    def DettaglioProcedimento(self, IDProcedimento, **kw):
        """ Estrazione dei dati di dettaglio di un procedimento """

        defaults = dict(
            #Utente = UTENTE, Ruolo = RUOLO
        )
        request = self.build_xml('DettaglioProcedimento',
            **dict(defaults, IDProcedimento=IDProcedimento, **kw))
        return self.query_service(self.client.service.DettaglioProcedimento, request)


    def ListaProcedimenti(self, **kw):
        """
        Estrazione dei procedimenti / Extraction of the proceedings of a subject.

        Argomenti possibili:
        CodiceFiscale   (str): codice fiscale dell'utente;
        SessionID       (str): -- NON UTILIZZATO --- ;
        DataInizio (DateTime): Se valorizzata, estrae i procedimenti con data di
                               protocollo a partire dalla data indicata (gg/mm/aaaa);
        DataFine   (DateTime): Se valorizzata, estrae i procedimenti con data di
                               protocollo  fino alla data indicata (gg/mm/aaaa);
        Stato           (str): Valori possibili:
                               "In corso": estrae i procedimenti attivi,
                               "Terminati": estrare i procedimenti terminati,
                               "Tutti": estrae sia i procedimenti attivi sia quelli terminati.
        """
        
        request = self.build_xml('ListaProcedimenti', **kw)
        res = self.query_service(self.client.service.ListaProcedimenti, request)
        if self.testinfo and 'result' in res:
            res['length'] = len(res['result']['Procedimenti']) and \
                len(res['result']['Procedimenti']['Procedimento'])

        return res


    def AttivaProcedimento(self, NumeroPratica, mittenti=[], allegati=[], **kw):
        """ Attivazione di un procedimento """
    
        request = self.get_ProtocolloIn(
            mittenti = mittenti,
            allegati = allegati,
            NumeroPratica = NumeroPratica,
            **kw)
        return self.query_service(self.client.service.AttivaProcedimento, request)


if __name__ == '__main__':
    # To run this thing use
    # bin/client1 run path/to/this/thing.py
    db = app.istanze.iol_provsp
    for doc in db.plomino_documents.objectValues():
        if doc.getForm() and doc.getForm().id in FIELDS_MAP:
	    insert_documento(doc)
