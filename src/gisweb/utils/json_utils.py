import simplejson as json

def json_dumps(pyobj=''):
    return json.dumps(pyobj)

def json_loads(string, **kwargs):
    return json.loads(string, **kwargs)
