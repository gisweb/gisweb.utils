import simplejson as json
import locale
try:
    locale.setlocale(locale.LC_TIME, 'it_IT.utf8')
except:
    locale.setlocale(locale.LC_TIME, '')

def handler(obj):
    if hasattr(obj, 'strftime'):
        if obj.strftime('%H:%M:%S') == '00:00:00':
            srepr = '%d/%m/%Y'
#            srepr = '%a %d %b %Y'
        else:
            srepr = '%d/%m/%Y %H:%M'
        return obj.strftime(srepr)
    else:
        return None

def json_dumps(pyobj=''):
    return json.dumps(pyobj, default=handler)

def json_loads(string, **kwargs):
    return json.loads(string, **kwargs)
