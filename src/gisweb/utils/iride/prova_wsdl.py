#!/usr/bin/env python
# - coding: utf-8 -
from suds.client import Client
import logging
from base64 import b64encode
###### Avoid problems with encodings and p db/ip db
import sys

import codecs
from lxml import etree
sys.stdout = codecs.getwriter('utf8')(sys.stdout)


logging.basicConfig(level=logging.INFO)
logging.getLogger('suds.transport').setLevel(logging.DEBUG)

# this url is good if you
# ssh siti.provincia.sp.it -L 3340:10.94.128.230:80 -p 2229
url = "http://127.0.0.1:3340/ulissetest/iride/web_services/WSProtocolloDM/WSProtocolloDM.asmx?WSDL"
client_protocollo = Client(url, location=url)
url_tabelle = "http://127.0.0.1:3340/ulissetest/iride/web_services/WS_Tabelle/WS_Tabelle.asmx?WSDL"
client_tabelle = Client(url_tabelle, location=url_tabelle)
url_bacheca = "http://127.0.0.1:3340/ulissetest/iride/web_services/WSBacheca/WSBacheca.asmx?WSDL"
client_bacheca = Client(url_bacheca, location=url_bacheca)

# classifiche = client_tabelle.service.wm_classifiche(filtro='*')
strutture = etree.fromstring(client_tabelle.service.wm_struttura(filtro='*').encode('utf-8'))


### Prova InserisciDocumento
doc = client_protocollo.factory.create('ProtocolloIn')
doc.Data = "01/01/2012"
#doc.Classifica = 'a'
#logging.getLogger('suds.transport').setLevel(logging.DEBUG)
#logging.basicConfig(level=logging.DEBUG)
result = client_tabelle.service.wm_tipiDocumento(filtro='*')
res = etree.fromstring(result.encode('utf-8'))
codici_documento = res.xpath('//codice/text()')
# doc.TipoDocumento = codici_documento[3]
doc.TipoDocumento = 'COMP'
doc.Data = '19/11/2012'
doc.Oggetto = 'Un oggetto'
doc.Origine = 'A'
doc.MittenteInterno = 'PROTO02'

mittente = client_protocollo.factory.create('MittenteDestinatarioIn')
mittente.CodiceFiscale = 'BRNNMR54L53I444S'
mittente.CognomeNome = 'Rossi'
mittente.Nome = 'Mario'
doc.MittentiDestinatari.MittenteDestinatario.append(mittente)
doc.AggiornaAnagrafiche = 'F'
doc.Utente = 'AMMINISTRATORE'
doc.Ruolo = 'AMMINISTRATORE'
doc.InCaricoA = 'COMPSTRA'

doc.Classifica = 'XVIII.02.03.'

# allegato = client_protocollo.factory.create('AllegatoIn')
# allegato.Image = b64encode(open('/tmp/pdf_prova.pdf').read())
# allegato.TipoFile = 'pdf'
# allegato.ContentType = 'application/pdf'
# doc.Allegati.Allegato.append(allegato)

res = client_protocollo.service.InserisciDocumento(doc)

#import ipdb; ipdb.set_trace()
for method in client_tabelle.wsdl.services[0].ports[0].methods.values():
    print '%s(%s)' % (method.name, ', '.join('%s: %s' % (part.type, part.name) for part in method.soap.input.body.parts))
# restituisce un oggetto ProtocolloOut vuoto con attributi Messaggio ed Errore
# "Impossibile aprire il database richiesto nell'account di accesso 'iridetest'. L'accesso avrà esito negativo."

### Prova InserisciDocumentoDaDM
# doc = client_protocollo.factory.create('DocumentumIn')
# res = client_protocollo.service.InserisciDocumentoDaDM(doc)
## Non dà errore

### Prova LeggiProtocollo
res = client_protocollo.service.LeggiProtocollo(AnnoProtocollo=2012, NumeroProtocollo=1)
# restituisce un documento vuoto con attributi Messaggio ed Errore
# "Impossibile aprire il database richiesto nell'account di accesso 'iridetest'. L'accesso avrà esito negativo."

# logging.getLogger('suds.transport').setLevel(logging.DEBUG)
# logging.basicConfig(level=logging.DEBUG)
# res = client_protocollo.service.Login(Utente="iridetest", Password='iridetest')

# client_protocollo.service.RicercaAmministrazione()