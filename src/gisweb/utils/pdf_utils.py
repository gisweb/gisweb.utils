# - coding: utf-8 -
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, KeepInFrame
from reportlab.lib.enums import TA_CENTER
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
            fontSize = 14,
            fontname='Arial',
            alignment=TA_CENTER,
            # borderWidth=4,
            # borderColor='black'
        )
        p = Paragraph(data.get(fieldname) or '',style)
        width = bbox_br[0] - bbox_tl[0]
        height = bbox_br[1] - bbox_tl[1]
        k = KeepInFrame(width*mm, height*mm, [p], mode='shrink')
        w,h = k.wrapOn(canvas, bbox_tl[1]*mm, bbox_tl[0]*mm )
        vpos = pagesize[1] - bbox_tl[1]*mm - h
        # Adjust vpos: we want vertical alignment
        vpos -= (height*mm - h)/2.0
        k.drawOn(canvas, bbox_tl[0]*mm, vpos)
    canvas.showPage()

def show_in_evince(filecontents, bgpdf='/tmp/abbonamento.pdf'):
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
    # Row 1, top; Row 1, bottom
    R1T, R1B = 41, 49
    R2T, R2B = 63, 71  # Row 2
    R3T, R3B = 79, 87  # Ok, you can figure it out all by yourself
    R4T, R4B = 98, 106
    R5T, R5B = 116, 124
    # Firma is not dynamic, thus I don't consider it a row at all
    R6T, R6B = 177, 185

    RR = 201  # right margin (many fields aling on this margin)

    SANREMO_LAYOUT = {
        'n_permesso_top': ((153, 20), (RR, 27)),

        'rilasciato': ((23, R1T), (57, R1B)),
        'scadenza': ((70, R1T), (105, R1B)),
        'categoria': ((127, R1T), (153, R1B)),
        'procura': ((164, R1T), (RR, R1B)),

        'cognome': ((25, R2T), (73, R2B)),
        'nome': ((86, R2T), (137, R2B)),
        'nato_a': ((147, R2T), (168, R2B)),
        'nato_il': ((173, R2T), (RR, R2B)),

        'numero_ff': ((22, R3T), (44, R3B)),
        'indirizzo': ((56, R3T), (165, R3B)),
        'civico': ((175, R3T), (RR, R3B)),

        'targa': ((18, R4T), (57, R4B)),
        'marca': ((66, R4T), (105, R4B)),
        'modello': ((117, R4T), (153, R4B)),
        'colore': ((162, R4T), (RR, R4B)),

        'verificato': ((22, R5T), (56, R5B)),
        'pagato': ((68, R5T), (104, R5B)),
        'autocertificazione': ((127, R5T), (152, R5B)),
        'data_ritiro': ((166, R5T), (RR, R5B)),

        'zona': ((15, R6T), (99, R6B)),
        'data_rilascio': ((115, R6T), (RR, R6B)),

        'n_permesso_middle': ((156, 166), (204, 173)),

        'n_permesso_bottom': ((45, 244), (73, 251)),
        'data_rilascio_bottom': ((12, 254), (39, 258)),
        'scadenza_bottom': ((49, 254), (73, 258)),
        'targa_bottom': ((24, 261), (74, 270)),
    }
    test_data = {
        'n_permesso_top': '344666',
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
        'indirizzo': 'Testo di esempio',
        'civico': 'Testo di esempio',

        'targa': 'Testo di esempio',
        'marca': 'Testo di esempio',
        'modello': 'Testo di esempio',
        'colore': 'Testo di esempio',

        'verificato': 'Testo di esempio',
        'pagato': 'Testo di esempio',
        'autocertificazione': 'Testo di esempio',
        'data_ritiro': 'Testo di esempio',

        'n_permesso_middle': '344666',

        'zona': 'Testo di esempio',
        'data_rilascio': 'Testo di esempio',

        'n_permesso_bottom': '344666',
        'data_rilascio_bottom': 'Testo di esempio',
        'scadenza_bottom': 'Testo di esempio',
        'targa_bottom': 'Testo di esempio',
    }
    pdf_file = generate_pdf(test_data, SANREMO_LAYOUT)
    show_in_evince(pdf_file)
