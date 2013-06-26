#import simplejson as json

import json

import locale

try:
    locale.setlocale(locale.LC_TIME, 'it_IT.utf8')
except:
    locale.setlocale(locale.LC_TIME, '')


def handler(obj, format='ISO'):

    if hasattr(obj, 'strftime'):
        if format == 'ISO':
            return obj.ISO()
        else:
            return obj.strftime(format)
    else:
        return obj
    
#def handler(obj):
    #if hasattr(obj, 'strftime'):
        #if obj.strftime('%H:%M:%S') == '00:00:00':
            #srepr = '%d/%m/%Y'
##            srepr = '%a %d %b %Y'
        #else:
            #srepr = '%d/%m/%Y %H:%M:%S'
        #return obj.strftime(srepr)
    #else:
        #return None

def json_dumps(obj, dateformat='%d/%m/%Y %H:%M:%S', **kwargs):

    kw = dict(
        default=lambda o: handler(o, format=dateformat),
        **kwargs
    )
    
    return json.dumps(obj, **kw)

def json_loads(string, **kwargs):
    return json.loads(string, **kwargs)
