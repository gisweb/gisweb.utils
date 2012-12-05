import requests
import json
from collections import namedtuple


def report(template, data, template_engine, document_type, output_type=None):
    url = 'http://127.0.0.1:8080/jaxrs/report'
    metadata = get_metadata(data)
    data = {
        'dataType': 'JSON',
        'data': json.dumps(data),
        'templateEngineKind': template_engine,
        'metadata': metadata,
        'outFileName': 'foo',
        'download': 'true',
    }
    if output_type:
        assert(output_type.upper() in ('PDF', 'XHTML'))
        data['outFormat'] = output_type.upper()
    filename = 'foo.%s' % document_type
    files = {'templateDocument': (filename, template)}
    result = requests.post(url, data, files=files)
    if result.status_code / 100 != 2:
        raise RuntimeError()
    return result.content


def get_metadata(data):
    result = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
              '<fields templateEngineKind="Freemarker">']
    for fieldinfo in get_info(data):
        fieldtag = ('<field name="%s" list="%s" imageName="" syntaxKind="">' %
                    (fieldinfo.name, fieldinfo.list))
        result += [fieldtag, '</field>']
    result.append('</fields>')
    return '\n'.join(result)


def get_info(data, path=[], islist='false'):
    "data is a dictionary. Return info about all keys named as paths"
    for key, value in data.items():
        currentpath = path + [key]
        if isinstance(value, dict):
            for info in get_info(value, currentpath, islist='false'):
                yield info
        elif isinstance(value, list) and isinstance(value[0], dict):
            for info in get_info(value[0], currentpath, islist='true'):
                yield info
        else:
            yield FieldInfo(name='.'.join(currentpath), list=islist)


FieldInfo = namedtuple('FieldInfo', ['name', 'list'])