# - coding: utf-8 -
from suds.client import Client
from datetime import datetime, date
from base64 import b64encode
from gisweb.utils.iride.plomino_conversion import FIELDS_MAP, get_tabledata_for


# this url is good if you
# ssh siti.provincia.sp.it -L 3340:10.94.128.230:80 -p 2229
#URL = 'http://127.0.0.1:3340/ulissetest/iride/web_services_20/WSProtocolloDM/WSProtocolloDM.asmx?WSDL'
# This one is good at Spezia
URL = 'http://10.94.128.230/ulissetest/iride/web_services_20/WSProtocolloDM/WSProtocolloDM.asmx?WSDL'
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


def insert_documento(doc):
    "Returns IdDocumento"
    client = Client(URL, location=URL)
    data = get_tabledata_for(doc)
    oggetto = doc.getForm().Title().decode('ascii', errors='replace')

    protocollo = client.factory.create('ProtocolloIn')
    protocollo.Data = date.today().isoformat()
    protocollo.Oggetto = oggetto

    mittente = client.factory.create('MittenteDestinatarioIn')

    fill_from_fisica(doc, mittente)

    protocollo.MittentiDestinatari.MittenteDestinatario.append(mittente)
    protocollo.AggiornaAnagrafiche = 'F'

    protocollo.Utente = 'AMMINISTRATORE'
    protocollo.Ruolo = 'AMMINISTRATORE'
    protocollo.Origine = 'GW'
    protocollo.MittenteInterno = 'PROTO02'

    metadata = get_metadata_for(doc)
    protocollo.TipoDocumento = metadata['__TipoDocumento']
    protocollo.InCaricoA = metadata['__InCaricoA']
    protocollo.Classifica = metadata['__Classifica']

    if 'domanda_inviata.pdf' in doc:
        allegato = client.factory.create('AllegatoIn')
        allegato.Image = b64encode(doc['domanda_inviata.pdf'].data)
        allegato.TipoFile = 'pdf'
        allegato.ContentType = 'application/pdf'
        protocollo.Allegati.Allegato.append(allegato)

    res = client.service.InserisciProtocollo(protocollo)
    IdDocumento = res.IdDocumento

    if hasattr(res, 'Errore') and unicode(res.Errore):
        # XXX FIXME: working around evil error ## TODO
        # Exception from HRESULT: 0xFFFDB5F4
        print RuntimeError(unicode(res.Errore))
        print protocollo
        import time
        IdDocumento = int(time.mktime(time.gmtime())) - 1358700000
        # raise RuntimeError(unicode(res.Errore))

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
    doc.setItem('numero_protocollo', str(IdDocumento))
    return res.IdDocumento


def get_metadata_for(doc):
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



if __name__ == '__main__':
    # To run this thing use
    # bin/client1 run path/to/this/thing.py
    db = app.istanze.iol_provsp
    for doc in db.plomino_documents.objectValues():
        if doc.getForm() and doc.getForm().id in FIELDS_MAP:
	    insert_documento(doc)
