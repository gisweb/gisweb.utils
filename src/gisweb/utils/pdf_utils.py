from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, KeepInFrame
import os
import tempfile

def generate_pdf(data, layout, options={}):
    """Generate a pdf file using the strings in data,
       laying them out according to layout (data and layout share the same keys)
       layout values are like this (in millimeters units):
           ((8,38), (53,47))
       They represent the bounding box where the text should be printed.
       Overflowing text will cause the font to scale down to fit the whole text
       Options can be used to set font/colour etc
    """
    pagesize = options.get('pagesize', (210*mm, 297*mm) )
    (_, canvasFileName) = tempfile.mkstemp('page.pdf')
    mycanvas = Canvas(canvasFileName,pagesize=pagesize)
    process_fields(data, mycanvas, layout, pagesize, options)
    mycanvas.save()
    result = file(canvasFileName)
    os.unlink(canvasFileName)
    return result


def process_fields(data, canvas, fields, pagesize, options):
    for fieldname, bbox in fields.items():
        style = ParagraphStyle(name=fieldname,
            fontSize = 16,
            fontname='Arial',
            borderWidth=4,
            borderColor='black')
        p = Paragraph(data[fieldname],style)
        width = bbox[1][0] - bbox[0][0]
        height = bbox[1][1] - bbox[0][1]
        k = KeepInFrame(width*mm, height*mm, [p], mode='shrink')
        w,h = k.wrapOn(canvas, bbox[0][1]*mm, bbox[0][0]*mm )
        vpos = pagesize[1] - bbox[0][1]*mm - h
        k.drawOn(canvas, bbox[0][0]*mm, vpos)
    canvas.showPage()


if __name__ == '__main__':
    SANREMO_LAYOUT = {
        'rilasciato': ((8,38), (53,47)),
        'scadenza': ((53, 38), (105, 47)),
    }
    test_data = {
        # n_permesso = '344666',
        'rilasciato': 'RILASCIATO',
        'scadenza': 'SCADENZA',
        # categoria: 'PIPPO',
        # procura: 'NO',
    }
    pdf_file = generate_pdf(test_data, SANREMO_LAYOUT)
