# -*- coding: utf-8 -*-
import urllib, urllib2
import socket
from BaseHTTPServer import BaseHTTPRequestHandler
from urllib2 import HTTPError
import base64
import requests

try:
    from Products.CMFPlomino.PlominoUtils import json_loads
except ImportError:
    from json import loads as json_loads

import logging
logger = logging.getLogger("GISWEB.UTILS.URL")

class Requests(object):

    @staticmethod
    def _post(url, data, **kw):
        return requests.post(url, data=data, **kw)

    @staticmethod
    def _get(url, params, **_):
        return requests.get(url, params=params)

    def rawcall(self, url, data=None, method='post', **kw):

        if method.lower()=='post':
            call = self._post
        elif method.lower()=='get':
            call = self._get
        else:
            # WARNING: needs to be tested!
            call = lambda url, data, **kw: requests.request(method.lower(), data=data, **kw)
        return call(url, data, **kw)

    @staticmethod
    def _reduce(response, *args):

        out = dict(errors=False)

        args = list(set(('ok', 'text', 'status_code', 'headers', )+args))
        for key in args:
            if hasattr(response, key):
                attr = getattr(response, key)
                if not callable(attr):
                    out[key] = attr
                else:
                    try:
                        value = attr()
                    except Exception as err:
                        out['errors'] = True
                        logger.warn("Expected attribute not found: %s (%s: %s)" % (key, type(err), err))
                    else:
                        # WARNING: qui devo distinguere ciò che è renderizzabile come dizionario
                        # per ora il controllo sull'attributo keys mi pare funzioni
                        if hasattr(value, 'keys') and not isinstance(value, dict):
                            try:
                                out[key] = dict(value)
                            except Exception as err:
                                out['errors'] = True
                                # WARNING: this should not happen. Why did it happen?
                                logger.warn("%s Attribute value of type %s cannot be reducted to a dictionary." % (key, type(value)))
                                logger.error("%s: %s" % (type(err), err))
                        else:
                            out[key] = value
            else:
                out['errors'] = True
                logger.warn("Expected attribute not found: %s" % key)

        return out

    def __call__(self, url, data=None, method='POST', args=None, **kw):
        """
        args {list/tuple}: list of arguments to be requested
                           (defaults are: 'ok', 'text', 'status_code', 'headers').
        """
        if args is None:
            args = []
        elif not isinstance(args, (tuple, list, )):
            # for backward compatibility
            args = [args]

        res = self.rawcall(url, data, method, **kw)
        return self._reduce(res, *args)

def requests_post(url, data=None, args=None, **kwargs):
    r = Requests()
    return r(url, data, method='POST', args=args, **kwargs)

def requests_get(url, params=None, methods_or_args=[]):
    r = Requests()
    return r(url, params, method='GET', args=methods_or_args)

def get_headers(h):
    """ DEPRECATED """
    return dict(h)

def myproxy(url):
    req = urllib2.Request(url)
    try:

        # Important or if the remote server is slow
        # all our web server threads get stuck here
        # But this is UGLY as Python does not provide per-thread
        # or per-socket timeouts thru urllib
        orignal_timeout = socket.getdefaulttimeout()
        try:
            socket.setdefaulttimeout(60)

            response = urllib2.urlopen(req)
        finally:
            # restore orignal timeoout
            socket.setdefaulttimeout(orignal_timeout)

        # XXX: How to stream respone through Zope
        # AFAIK - we cannot do it currently

        return response.read()

    except HTTPError, e:
        # Have something more useful to log output as plain urllib exception
        # using Python logging interface
        # http://docs.python.org/library/logging.html
        logger.error("Server did not return HTTP 200 when calling remote proxy URL:" + url)
        for key, value in params.items():
            logger.error(key + ": "  + value)

        # Print the server-side stack trace / error page
        logger.error(e.read())

        raise e

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
    except Exception as error:
        return dict(
            status_code = 0,
            ok = False,
            reason = "%s: %s" % (type(error), error)
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

def encode_b64(text=''):
    return base64.b64encode(text)

def decode_b64(text=''):
    return base64.b64decode(text)    
