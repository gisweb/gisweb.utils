from xdocreport import report

try:
    from cStringIO import StringIO
except ImportError, err:
    from StringIO import StringIO

#report(template, data, template_engine, document_type, output_type=None)

def make_report(template_content, data,
    template_engine='Velocity',
    document_type='odt',
    output_type=None):
    '''
    content is what is returned from mytemplate.data
    data is a json string containing the item values of a plominoDocument
    '''
    
    template = StringIO(template_content)
    
    return report(template, data, template_engine, document_type, output_type=output_type)
