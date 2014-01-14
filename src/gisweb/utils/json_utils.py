#import simplejson as json

import json
from decimal import Decimal
import locale

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import lxml.etree as etree

def xml_pprint(xml):
    f = StringIO(xml)
    try:
        doc = etree.parse(f)
    except:
        return xml
    else:
        return etree.tostring(doc, pretty_print = True)

try:
    locale.setlocale(locale.LC_TIME, 'it_IT.utf8')
except:
    locale.setlocale(locale.LC_TIME, '')

def handler(obj, format='ISO', prettyxml=False):
    # datetime and DateTime handling
    if hasattr(obj, 'strftime'):
        if format.upper() == 'ISO':
            try:
                return obj.ISO()
            except AttributeError:
                return obj.isoformat()
        else:
            try:
                return obj.strftime(format)
            # the datetime strftime() methods require year >= 1900 
            except ValueError:
                return handler(obj, format='ISO')
    # Decimal handling
    elif isinstance(obj, Decimal):
        return float(obj)
    # XML handling if you need pretty printing (mainly for visual debug)
    elif prettyxml and isinstance(obj, basestring):
        return xml_pprint(obj)
    # other...
    else:
        # I assume that return a string is better than raise an error
        return str(obj)


def json_dumps(obj, customformat='%d/%m/%Y %H:%M:%S', prettyxml=False, **kwargs):

    kw = dict(
        default=lambda o: handler(o, prettyxml=prettyxml, format=customformat),
        **kwargs
    )

    return json.dumps(obj, **kw)

def json_loads(string, **kwargs):
    return json.loads(string, **kwargs)
