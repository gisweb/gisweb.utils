# - coding: utf-8 -
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
       Example Options dict:
           #XXX unimplemented so far
    """
    pagesize = options.get('pagesize', (210*mm, 297*mm) )
    (_, canvasFileName) = tempfile.mkstemp('page.pdf')
    mycanvas = Canvas(canvasFileName,pagesize=pagesize)
    process_fields(data, mycanvas, layout, pagesize, options)
    mycanvas.save()
    with open(canvasFileName) as fh:
        result = fh.read()
    os.unlink(canvasFileName)
    return result


def process_fields(data, canvas, fields, pagesize, options):
    # tl = top left; br = bottom right
    for fieldname, (bbox_tl, bbox_br) in fields.items():
        style = ParagraphStyle(name=fieldname,
            fontSize = 12,
            fontname='Arial',
            # borderWidth=4,
            # borderColor='black'
        )
        p = Paragraph(data[fieldname],style)
        width = bbox_br[0] - bbox_tl[0]
        height = bbox_br[1] - bbox_tl[1]
        k = KeepInFrame(width*mm, height*mm, [p], mode='shrink')
        w,h = k.wrapOn(canvas, bbox_tl[1]*mm, bbox_tl[0]*mm )
        vpos = pagesize[1] - bbox_tl[1]*mm - h
        k.drawOn(canvas, bbox_tl[0]*mm, vpos)
    canvas.showPage()

def show_in_evince(filecontents):
    bgpdf = '/tmp/abbonamento.pdf'
    (_, outfile) = tempfile.mkstemp('page.pdf')
    (_, mypdf) = tempfile.mkstemp('page.pdf')
    with open(mypdf, 'w') as fh:
        fh.write(filecontents)
    command = "pdftk  %(mypdf)s background %(bgpdf)s output %(outfile)s"
    os.popen(command % locals())
    os.popen("evince %(outfile)s" % locals())
    os.unlink(mypdf)
    os.unlink(outfile)

if __name__ == '__main__':
    SANREMO_LAYOUT = {
        'n_permesso_top': ((153, 20), (200, 27)),
        'rilasciato': ((28,38), (53,47)),
        'scadenza': ((74, 38), (105, 47)),
        'categoria': ((132, 38), (158, 47)),
        'procura': ((170, 38), (205, 47)),
        'cognome': ((25, 61), (73, 70)),
        'nome': ((86, 61), (137, 70)),
        'nato_a': ((152, 61), (173, 70)),
        'nato_il': ((178, 61), (205, 70)),
        'numero_ff': ((28, 76), (49, 85)),
        # 'indirizzo': ()
        # 'civico'
        # 'targa'
        # 'marca'
        # 'modello'
        # 'colore'
        # 'verificato'
        # 'pagato'
        # 'autocertificazione'
        # 'data_ritiro'
        # 'zona'
        # 'data_rilascio'
        # 'n_permesso_bottom'
        # 'data_rilascio_bottom'
        # 'scadenza_bottom'
        # 'targa_bottom'
    }
    test_data = {
        'n_permesso_top' : '344666',
        'rilasciato': 'RILASCIATO',
        'scadenza': ('SCADENZA della pratica in un remoto '
                     'futuro che prima o poi arriverà sorprendendo tutti '
                     'coloro che avevano dimenticato che, un giorno lontano, '
                     'perfino questa pratica sarebbe scaduta'),
        'categoria': 'PIPPO',
        'procura': 'NO',
        'cognome': "Serbelloni Mazzanti Viendalmare",
        'nome': "Contessa",
        'nato_a': 'Principato degli Ulivi',
        'nato_il': '1/7/1916',
        'numero_ff': 'NONso',
        # 'indirizzo':
        # 'civico'
        # 'targa'
        # 'marca'
        # 'modello'
        # 'colore'
        # 'verificato'
        # 'pagato'
        # 'autocertificazione'
        # 'data_ritiro'
        # 'zona'
        # 'data_rilascio'
        # 'n_permesso_bottom'
        # 'data_rilascio_bottom'
        # 'scadenza_bottom'
        # 'targa_bottom'
    }
    pdf_file = generate_pdf(test_data, SANREMO_LAYOUT)
    show_in_evince(pdf_file)
