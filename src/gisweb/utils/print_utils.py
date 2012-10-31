#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import xhtml2pdf.pisa as xhtml2pdf
from xhtml2pdf.default import DEFAULT_CSS as pisa_css

from UnicodeDammit import UnicodeDammit

def plominoPrint(plominoDocument, form_name=None, default_css=None, use_command=False):
    '''This function is for printing data from plominoDocuments rendered with the
        specified form. In the case no form is supplied the one specified in the
        "Form" propertiy is used.
    '''
    plominoDatabase = plominoDocument.getParentDatabase()
    if not form_name:
        form_name = plominoDocument.Form
    form = plominoDatabase.getForm(form_name)
    html_content = plominoDocument.openWithForm(form)
#    html_content = '''
#<html>
#<head>#
	#<link rel="stylesheet" href="/++theme++pippo/bootstrap/css/bootstrap.min.css">
	#<link rel="stylesheet" href="/++theme++pippo/bootstrap/css/bootstrap-responsive.min.css">
#</head>
#<body>
#%s
#</body>
#</html>''' %html_content
    if default_css:
        default_css = pisa_css + default_css

    rel_path = '..'
    abs_path = '%s' % plominoDatabase.absolute_url()
    html_content = html_content.replace(rel_path, abs_path)
    u_html_content = UnicodeDammit(html_content)
    encoding = u_html_content.originalEncoding

    # option deprecated. Used just to test different dehaviours between the two
    #+ approaches
    if use_command:
        SRC = '/tmp/test_in.html'
        input_file = open(SRC, 'w')
        input_file.write(html_content)
        input_file.close()
        xml = os.popen("xhtml2pdf --encoding %s %s -" % (encoding, SRC)).read()
#        os.remove(SRC)
#        output_file = open('/tmp/test_out.pdf', 'w')
#        output_file.write(xml)
#        output_file.close()
    else:
        pdf = xhtml2pdf.CreatePDF(
            html_content,
            default_css=default_css,
            encoding = encoding
            )
        xml = pdf.dest.getvalue()
    
    return xml

def printToPdf(html='',default_css=None):
#    if default_css:
#        default_css = pisa_css + default_css
    u_html = UnicodeDammit(html)
    encoding = u_html.originalEncoding
    pdf = xhtml2pdf.CreatePDF(
        html,
#        default_css=pisa_css,
#        encoding = encoding
    )
    xml = pdf.dest.getvalue()
    return xml

