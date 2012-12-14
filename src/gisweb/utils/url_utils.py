import urllib, urllib2
from BaseHTTPServer import BaseHTTPRequestHandler

import requests

def requests_post(url, data=None, **kwargs):
    result = requests.post(url, data, **kwargs)
    return dict(
        text = result.text,
        error = result.error,
        headers = result.headers,
        status_code = result.status_code,
        reason = result.reason
    )

#def get_request(target, data):
#    return urllib2.Request(target, data)

#def get_response(request):
#    return urllib2.urlopen(request)

def urllib_urlencode(query, doseq=0):
    return urllib.urlencode(query, doseq)

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
