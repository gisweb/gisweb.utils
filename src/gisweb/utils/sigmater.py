from suds.client import Client
from suds.sax.text import Raw
serviceUrl = "http://10.11.132.2:8080/PdDProvinciaLaSpezia/PD/SPCProvinciaLaSpezia/SPCRegioneLiguria"

def ricercaTitolaritaSoggetto(body='',usr='',pwd=''):
	method="SPCConsultazioneSoggettiWebService/eseguiRicercaSoggetti?wsdl";
	url="%s/%s" %(serviceUrl,method)
	client = Client(url)
	xml=Raw('''
	<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:s3="http://s3.webservices.sigmater.org/">
		<soapenv:Header/>
			<soapenv:Body>
				<s3:eseguiRicercaTitolaritaSoggetto>
					%s
					<username>%s</username>
					<password>%s</password>
				</s3:eseguiRicercaTitolaritaSoggetto>
		</soapenv:Body>
	</soapenv:Envelope>
	''' %(body,usr,pwd) )
	return client.service.OpenSPCoop_PD(__inject={'msg': xml})
	