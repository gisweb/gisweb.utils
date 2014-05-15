from suds.client import Client
from suds.sax.text import Raw

BASE_URL = "http://10.11.132.2:8080/PdDProvinciaLaSpezia/PD/SPCProvinciaLaSpezia/SPCRegioneLiguria"

def ricercaSoggetti(query='',usr='',pwd=''):
	method="SPCConsultazioneSoggettiWebService/eseguiRicercaSoggetti?wsdl";
	url="%s/%s" %(BASE_URL,method)
	client = Client(url)
	xml=Raw('''
	<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:s3="http://s3.webservices.sigmater.org/">
		<soapenv:Header/>
			<soapenv:Body>
				<s3:eseguiRicercaSoggetti>
					<ricercaSoggetti>
					%s
					</ricercaSoggetti>
					<username>%s</username>
					<password>%s</password>
				</s3:eseguiRicercaSoggetti>
		</soapenv:Body>
	</soapenv:Envelope>
	''' %(query,usr,pwd) )
	ret = dict(client.service.OpenSPCoop_PD(__inject={'msg': xml}))
	if ret['return']:
		return ret['return']
	return ret 

	
def ricercaTitolaritaSoggetto(query='',usr='',pwd=''):
	method="SPCConsultazioneSoggettiWebService/eseguiRicercaTitolaritaSoggetto?wsdl";
	url="%s/%s" %(BASE_URL,method)
	client = Client(url)
	xml=Raw('''
	<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:s3="http://s3.webservices.sigmater.org/">
		<soapenv:Header/>
			<soapenv:Body>
				<s3:eseguiRicercaTitolaritaSoggetto>
					<ricercaTitolaritaSoggetto>
					%s
					</ricercaTitolaritaSoggetto>
					<username>%s</username>
					<password>%s</password>
				</s3:eseguiRicercaTitolaritaSoggetto>
		</soapenv:Body>
	</soapenv:Envelope>
	''' %(query,usr,pwd) )
	ret = dict(client.service.OpenSPCoop_PD(__inject={'msg': xml}))
	if ret['return']:
		return ret['return']
	return ret 
	
def ricercaPerIdCat(query='',usr='',pwd=''):
	method="SPCConsultazioneTerreniWebService/eseguiRicercaTerreno?wsdl";
	url="%s/%s" %(BASE_URL,method)
	client = Client(url)
	xml=Raw('''
	<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:s3="http://s3.webservices.sigmater.org/">
		<soapenv:Header/>
			<soapenv:Body>
				<s3:eseguiRicercaTerreno>
					<ricercaPerIdCat>
					%s
					</ricercaPerIdCat>
					<username>%s</username>
					<password>%s</password>
				</s3:eseguiRicercaTerreno>
		</soapenv:Body>
	</soapenv:Envelope>
	''' %(query,usr,pwd) )
	ret = dict(client.service.OpenSPCoop_PD(__inject={'msg': xml}))
	if ret['return']:
		return ret['return']
	return ret 

def dettaglioPerIdCat(query='',usr='',pwd=''):
	method="SPCConsultazioneTerreniWebService/caricaDettaglioTerreno?wsdl";
	url="%s/%s" %(BASE_URL,method)
	client = Client(url)
	xml=Raw('''
	<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:s3="http://s3.webservices.sigmater.org/">
		<soapenv:Header/>
			<soapenv:Body>
				<s3:caricaDettaglioTerreno>
					<ricercaPerIdCat>
					%s
					</ricercaPerIdCat>
					<username>%s</username>
					<password>%s</password>
				</s3:caricaDettaglioTerreno>
		</soapenv:Body>
	</soapenv:Envelope>
	''' %(query,usr,pwd) )
	ret = dict(client.service.OpenSPCoop_PD(__inject={'msg': xml}))
	if ret['return']:
		return ret['return']
	return ret 


	
def ricercaPerUIU(query='',usr='',pwd=''):
	method="SPCConsultazioneUIUWebService/eseguiRicercaUIU?wsdl";
	url="%s/%s" %(BASE_URL,method)
        client = Client(url)
        xml=Raw('''
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:s3="http://s3.webservices.sigmater.org/">
                <soapenv:Header/>
                        <soapenv:Body>
				 <s3:eseguiRicercaUIU>
                                        <ricercaPerIdCat>
                                        %s
                                        </ricercaPerIdCat>
                                        <username>%s</username>
                                        <password>%s</password>
                                </s3:eseguiRicercaUIU>
		</soapenv:Body>
        </soapenv:Envelope>
        ''' %(query,usr,pwd) )
        ret = dict(client.service.OpenSPCoop_PD(__inject={'msg': xml}))
       	if ret['return']:
                return ret['return']
        return ret


def dettaglioPerIdUIU(query='',usr='',pwd=''):
        method="SPCConsultazioneUIUWebService/caricaDettaglioUIU?wsdl";
        url="%s/%s" %(BASE_URL,method)
        client = Client(url)
        xml=Raw('''
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:s3="http://s3.webservices.sigmater.org/">
                <soapenv:Header/>
                        <soapenv:Body>
                                <s3:caricaDettaglioUIU>
                                        <ricercaPerIdCat>
                                        %s
                                        </ricercaPerIdCat>
                                        <username>%s</username>
                                        <password>%s</password>
                                </s3:caricaDettaglioUIU>
                </soapenv:Body>
        </soapenv:Envelope>
        ''' %(query,usr,pwd) )
        ret = dict(client.service.OpenSPCoop_PD(__inject={'msg': xml}))
        if ret['return']:
                return ret['return']
        return ret
 
