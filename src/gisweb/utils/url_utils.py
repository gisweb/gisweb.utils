import urllib, urllib2
from BaseHTTPServer import BaseHTTPRequestHandler

import requests

from json_utils import json_loads

def requests_post(url, data=None, *args, **kwargs):
    
    args = list(set(['ok', 'text', 'status_code']+list(args)))
    
    resp = requests.post(url, data, **kwargs)
    
    out = dict()
    for k in args:
        if callable(getattr(resp, k)):
            out[k] = getattr(resp, k)()
        else:
            out[k] = getattr(resp, k)
    
    return out

def requests_get(url, params=None, methods_or_args=[]):

    resp = requests.get(url, params=params)

    args = list(set(['ok', 'text', 'status_code'] + list(methods_or_args)))
    
    out = dict()
    for k in args:
        if callable(getattr(resp, k)):
            out[k] = getattr(resp, k)()
        else:
            out[k] = getattr(resp, k)

    return out

def wsquery(url, method='GET', timeout=60, headers={}, **kw):
    """
    url: url to contact;
    method: method type (i.e. GET (default) or POST ( and maybe PUT/DELETE/HEAD/OPTIONS.
        But I've not tested));

    kw: parameters;

    Code example:
        >> import json
        >> url = "https://maps.googleapis.com/maps/api/timezone/json"
        >> res = wsquery(url, location="39.603,-119.682", timestamp="1331161200", sensor='false')
        >> print json.dumps(res, indent=4)
        {
            "ok": true,
            "links": {},
            "encoding": "UTF-8",
            "url": "https://maps.googleapis.com/maps/api/timezone/json?timestamp=1331161200&sensor=false&location=39.603%2C-119.682",
            "status_code": 200,
            "elapsed": "0:00:00.208581",
            "content": "{\n   \"dstOffset\" : 0,\n   \"rawOffset\" : -28800,\n   \"status\" : \"OK\",\n   \"timeZoneId\" : \"America/Los_Angeles\",\n   \"timeZoneName\" : \"Pacific Standard Time\"\n}\n",
            "headers": {
                "alternate-protocol": "443:quic",
                "x-xss-protection": "1; mode=block",
                "transfer-encoding": "chunked",
                "expires": "Fri, 01 Jan 1990 00:00:00 GMT",
                "server": "mafe",
                "pragma": "no-cache",
                "cache-control": "no-cache, must-revalidate",
                "date": "Wed, 09 Oct 2013 13:13:57 GMT",
                "access-control-allow-origin": "*",
                "content-type": "application/json; charset=UTF-8",
                "x-frame-options": "SAMEORIGIN"
            },
            "reason": "OK",
            "text": "{\n   \"dstOffset\" : 0,\n   \"rawOffset\" : -28800,\n   \"status\" : \"OK\",\n   \"timeZoneId\" : \"America/Los_Angeles\",\n   \"timeZoneName\" : \"Pacific Standard Time\"\n}\n"
        }
    """

    params, files = dict(), dict()
    for k,v in kw.items():
        if isinstance(v, file):
            files[k] = v
        else:
            params[k] = v
    if files and method=='GET':
        method = 'POST'

    def getvalue(o, n):
        try:
            a = getattr(o, n)
        except AttributeError as err:
            return ''
        else:
            if callable(a):
                return a()
            else:
                return a

    try:
        response = requests.request(method, url, params=params, files=files, headers=headers, timeout=timeout)
    except requests.exceptions.Timeout as error:
        return dict(
            ok = False,
            reason = '%s' % error
        )
    else:
        return dict([(k, getvalue(response, k)) for k in (
            'elapsed',
            'ok',
            'status_code',
            'reason',
            'content',
            'text',
            'links',
            'encoding',
            'url',
        )], headers = dict(response.headers))

if __name__ == '__main__':
    url = "http://sit.spezianet.it/elabora/verifica_nucleo.php"
    result = wsquery(url=url,codfisc='zzrfba64c09e463c')
    print result

def urllib_urlencode(query, doseq=0):
    return urllib.urlencode(query, doseq)

def urllib_quote_plus(string):
    return urllib.quote_plus(string)

def proxy(request, url):
    
    allowedHosts = []
    
    allowed_content_types = (
        "image/png",
        "image/jpeg",
        "text/html",
        "application/xml", "text/xml",
        "application/json",
        "application/vnd.ogc.se_xml",           # OGC Service Exception
        "application/vnd.ogc.se+xml",           # OGC Service Exception
        "application/vnd.ogc.success+xml",      # OGC Success (SLD Put)
        "application/vnd.ogc.wms_xml",          # WMS Capabilities
        "application/vnd.ogc.context+xml",      # WMC
        "application/vnd.ogc.gml",              # GML
        "application/vnd.ogc.sld+xml",          # SLD
        "application/vnd.google-earth.kml+xml", # KML
    )
    
    method = request.method
    params = request.form
    query_string = request.QUERY_STRING
    
    if "HTTP_X_FORWARDED_FOR" in request.environ:
        # Virtual host
        host = request.environ["HTTP_X_FORWARDED_FOR"]
    elif "HTTP_HOST" in request.environ:
        # Non-virtualhost
        host = request.environ["REMOTE_ADDR"]
    else:
        host = ''
    
    if not host or (allowedHosts and not host in allowedHosts):
        short, msg = BaseHTTPRequestHandler.responses[403]
        raise urllib2.HTTPError(url, 403, msg)
    
    if url.startswith("http://") or url.startswith("https://"):
        try:
            if query_string:
                url = '?'.join([url, query_string])
        
            res = urllib2.urlopen(url)
        
            # Check for allowed content types
            i = res.info()
            if i.has_key("Content-Type"):
                ct = i["Content-Type"]
                if not ct.split(";")[0] in allowed_content_types:
                    # @ToDo?: Allow any content type from allowed hosts (any port)
                    #if allowedHosts and not host in allowedHosts:
                    msg = "Content-Type not permitted"
                    raise urllib2.HTTPError(url, 403, msg)
            else:
                msg = "Content-Type not permitted"
                raise urllib2.HTTPError(url, 406, "Unknown Content")

            msg = res.read()
            res.close()
            # Required for WMS Browser to work in IE
            # response.headers["Content-Type"] = "text/xml"
            return msg
    
        except Exception as err:
            raise urllib2.HTTPError(url, 500, "Some unexpected error occurred. Error text was: %s" % err)
    
    else:
        # Bad Request
        short, msg = BaseHTTPRequestHandler.responses[400]
        raise urllib2.HTTPError(url, 400, msg)

def proxy_script():

    from gisweb.utils import proxy

    url = '' # URL to mapserver
    
    return proxy(context.REQUEST, url)


def geocode(**kw):
    if not 'sensor' in kw:
        kw['sensor'] = 'false'
    raw = requests_get(
        'http://maps.googleapis.com/maps/api/geocode/json',
        params=kw)
    res = json_loads(raw['text'])
    return res

