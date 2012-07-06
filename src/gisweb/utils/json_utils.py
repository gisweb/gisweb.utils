import simplejson as json
import locale
locale.setlocale(locale.LC_TIME, 'it_IT.utf8')

def handler(obj):
    if hasattr(obj, 'strftime'):
        if obj.strftime('%H:%M:%S') == '00:00:00':
            srepr = '%a %d %b %Y'
        else:
            srepr = '%a %d %b %Y, %H:%M'
        return obj.strftime(srepr)
    else:
        return None

def json_dumps(pyobj=''):
    return json.dumps(pyobj, default=handler)

def json_loads(string, **kwargs):
    return json.loads(string, **kwargs)
