#!/usr/bin/python
# -*- coding: utf-8 -*-
from AccessControl import allow_module
from Products.CMFPlomino.interfaces import IPlominoDatabase
from z3c.saconfig import named_scoped_session

from Products.CMFCore.utils import getToolByName
from zope.app.component.hooks import getSite

allow_module('gisweb.utils')

def initialize(con):
    "Being a Zope2 Product we ensure this file will be imported at startup"


################################################################ PLOMINO UTILS #

def get_parent_plominodb(obj):
    current = obj
    while hasattr(current, 'aq_parent') and not IPlominoDatabase.providedBy(current):
        current = current.aq_parent
    return hasattr(current, 'aq_parent') and current

def search_around(plominoDocument, parentKey='parentDocument', *targets, **filters):
    '''
    DA TESTARE
    
    "out" è un dizionario la cui chiavi sono le stringhe contenute in target se
    per esse è stato trovato almeno un valore tra i documenti collegati al
    plominoDocument (compreso lo stesso). Se i valori trovati per la chiave
    richiesta fossero più di uno questi vengono messi in una lista. Per ottenere
    meno valori è possibile affinare la ricerca fornendo le chiavi "filters" che
    vengono usate per le ricerche nel plominoIndex e per la selezione dei
    documenti da cui attingere i valori.
    ATTENZIONE! NON sono contemplate condizioni di confronto per le ricerche che
    siano più complesse del semplice confronto di uguaglianza. Possono però
    essere passati parametri specifici per la ricerca su ZDB quali "sort_on",
    "sort_order" e simili.
    
    può sostituire in maniera meno statica il get_info_pratica
    '''

    out = dict()
    if plominoDocument.isNewDocument(): return out

#    main_fields = [t for t in targets if t in plominoDocument.getForm().getFormFields()]
#    other_fields = [t for t in targets if t not in main_fields]
    
    items = plominoDocument.getItems()
    # cerco prima nel documento "genitore"
    for target in targets:
        if target in items:
            out[target] = plominoDocument.getItem(target)
    
    # poi cerco nei documenti figli
    plominoIndex = plominoDocument.getParentDatabase().getIndex()
    filters[parentKey] = plominoDocument.id
    res = plominoIndex.dbsearch(**filters)
    for rec in res:
        pd = rec.getObject()
        
        # nel caso le chiavi in filters non fossero state indicizzate
        #+ evito i documenti che sarebbero stati scartati dalla ricerca
        #+ DA RIVEDERE E CORREGGERE
        if all([pd.getItem(k)==filters.get(k) for k in pd.getForm().getFormFields() if k in filters]):

            items = pd.getItems()
            for target in targets:
                if target in items:
                    if target in out:
                        out[target] += [plominoDocument.getItem(target)]
                    else:
                        out[target] = [plominoDocument.getItem(target)]
            if len(out[target]) == 1:
                out[target] = out[target][0]

    return out

##################################################################### DB UTILS #

def get_something_from_db():
    session = get_session('maciste')
    # do something with session
    return "pluto"

def get_session(sessionname):
    "Use collective.saconnect to configure connections TTW"
    factory = named_scoped_session(sessionname)
    return factory()


################################################################### JSON UTILS #

import simplejson as json
def json_dumps(pyobj=''):
    return json.dumps(pyobj)

def json_loads(string, **kwargs):
    return json.loads(string, **kwargs)


################################################################### ZOPE UTILS #

def aq_base(obj):
    return obj.aq_base()


#################################################################### ACL UTILS #

def get_users_info(id_list, properties=('fullname', )):
    '''
    get an id_list as returned by the plominoDatabase method getUsersForRoles
    that maybe it's a principals id list in wich users id and groups id are not
    distinguished and return the list of specified properties from ACL.
    
    out = [{'id':..., 'fullname':...}, {...}, ...]
    
    '''
    
    context = getSite()
    
    acl_tool = getToolByName(context, 'acl_users')
    pg_tool = getToolByName(context, 'portal_groups')

    users = [acl_tool.getUserById(i) for i in id_list if acl_tool.getUserById(i)]
    groups = [pg_tool.getGroupById(i) for i in id_list if pg_tool.getGroupById(i)]
    
    members_in_groups = []
    for group in groups:
        members_in_groups += group.getGroupMembers()

    out = list()
    ids = list()
    
    for user in users+members_in_groups:
        myuser = dict()
        if hasattr(user.aq_base, 'getName'):
            user_id = user.getName()
        else:
            user_id = user.getProperty('id')
            
        if user_id not in ids:
            ids.append(user_id)
            myuser['id'] = user_id
            for prop in properties:
                myuser[prop] = user.getProperty(prop)
            out.append(myuser)
    
    return out
    
    
################################################################## PRINT UTILS #

import cStringIO, os
import xhtml2pdf.pisa as xhtml2pdf
from xhtml2pdf.default import DEFAULT_CSS as pisa_css

import re, codecs
try:
    import chardet
#    import chardet.constants
#    chardet.constants._debug = 1
except ImportError:
    chardet = None

# This class comes from BeautifulSoup
class UnicodeDammit:
    """A class for detecting the encoding of a *ML document and
    converting it to a Unicode string. If the source encoding is
    windows-1252, can replace MS smart quotes with their HTML or XML
    equivalents."""

    # This dictionary maps commonly seen values for "charset" in HTML
    # meta tags to the corresponding Python codec names. It only covers
    # values that aren't in Python's aliases and can't be determined
    # by the heuristics in find_codec.
    CHARSET_ALIASES = { "macintosh" : "mac-roman",
                        "x-sjis" : "shift-jis" }

    def __init__(self, markup, overrideEncodings=[],
                 smartQuotesTo='xml', isHTML=False):
        self.declaredHTMLEncoding = None
        self.markup, documentEncoding, sniffedEncoding = \
                     self._detectEncoding(markup, isHTML)
        self.smartQuotesTo = smartQuotesTo
        self.triedEncodings = []
        if markup == '' or isinstance(markup, unicode):
            self.originalEncoding = None
            self.unicode = unicode(markup)
            return

        u = None
        for proposedEncoding in overrideEncodings:
            u = self._convertFrom(proposedEncoding)
            if u: break
        if not u:
            for proposedEncoding in (documentEncoding, sniffedEncoding):
                u = self._convertFrom(proposedEncoding)
                if u: break

        # If no luck and we have auto-detection library, try that:
        if not u and chardet and not isinstance(self.markup, unicode):
            u = self._convertFrom(chardet.detect(self.markup)['encoding'])

        # As a last resort, try utf-8 and windows-1252:
        if not u:
            for proposed_encoding in ("utf-8", "windows-1252"):
                u = self._convertFrom(proposed_encoding)
                if u: break

        self.unicode = u
        if not u: self.originalEncoding = None

    def _subMSChar(self, orig):
        """Changes a MS smart quote character to an XML or HTML
        entity."""
        sub = self.MS_CHARS.get(orig)
        if isinstance(sub, tuple):
            if self.smartQuotesTo == 'xml':
                sub = '&#x%s;' % sub[1]
            else:
                sub = '&%s;' % sub[0]
        return sub

    def _convertFrom(self, proposed):
        proposed = self.find_codec(proposed)
        if not proposed or proposed in self.triedEncodings:
            return None
        self.triedEncodings.append(proposed)
        markup = self.markup

        # Convert smart quotes to HTML if coming from an encoding
        # that might have them.
        if self.smartQuotesTo and proposed.lower() in("windows-1252",
                                                      "iso-8859-1",
                                                      "iso-8859-2"):
            markup = re.compile("([\x80-\x9f])").sub \
                     (lambda(x): self._subMSChar(x.group(1)),
                      markup)

        try:
            # print "Trying to convert document to %s" % proposed
            u = self._toUnicode(markup, proposed)
            self.markup = u
            self.originalEncoding = proposed
        except Exception, e:
            # print "That didn't work!"
            # print e
            return None
        #print "Correct encoding: %s" % proposed
        return self.markup

    def _toUnicode(self, data, encoding):
        '''Given a string and its encoding, decodes the string into Unicode.
        %encoding is a string recognized by encodings.aliases'''

        # strip Byte Order Mark (if present)
        if (len(data) >= 4) and (data[:2] == '\xfe\xff') \
               and (data[2:4] != '\x00\x00'):
            encoding = 'utf-16be'
            data = data[2:]
        elif (len(data) >= 4) and (data[:2] == '\xff\xfe') \
                 and (data[2:4] != '\x00\x00'):
            encoding = 'utf-16le'
            data = data[2:]
        elif data[:3] == '\xef\xbb\xbf':
            encoding = 'utf-8'
            data = data[3:]
        elif data[:4] == '\x00\x00\xfe\xff':
            encoding = 'utf-32be'
            data = data[4:]
        elif data[:4] == '\xff\xfe\x00\x00':
            encoding = 'utf-32le'
            data = data[4:]
        newdata = unicode(data, encoding)
        return newdata

    def _detectEncoding(self, xml_data, isHTML=False):
        """Given a document, tries to detect its XML encoding."""
        xml_encoding = sniffed_xml_encoding = None
        try:
            if xml_data[:4] == '\x4c\x6f\xa7\x94':
                # EBCDIC
                xml_data = self._ebcdic_to_ascii(xml_data)
            elif xml_data[:4] == '\x00\x3c\x00\x3f':
                # UTF-16BE
                sniffed_xml_encoding = 'utf-16be'
                xml_data = unicode(xml_data, 'utf-16be').encode('utf-8')
            elif (len(xml_data) >= 4) and (xml_data[:2] == '\xfe\xff') \
                     and (xml_data[2:4] != '\x00\x00'):
                # UTF-16BE with BOM
                sniffed_xml_encoding = 'utf-16be'
                xml_data = unicode(xml_data[2:], 'utf-16be').encode('utf-8')
            elif xml_data[:4] == '\x3c\x00\x3f\x00':
                # UTF-16LE
                sniffed_xml_encoding = 'utf-16le'
                xml_data = unicode(xml_data, 'utf-16le').encode('utf-8')
            elif (len(xml_data) >= 4) and (xml_data[:2] == '\xff\xfe') and \
                     (xml_data[2:4] != '\x00\x00'):
                # UTF-16LE with BOM
                sniffed_xml_encoding = 'utf-16le'
                xml_data = unicode(xml_data[2:], 'utf-16le').encode('utf-8')
            elif xml_data[:4] == '\x00\x00\x00\x3c':
                # UTF-32BE
                sniffed_xml_encoding = 'utf-32be'
                xml_data = unicode(xml_data, 'utf-32be').encode('utf-8')
            elif xml_data[:4] == '\x3c\x00\x00\x00':
                # UTF-32LE
                sniffed_xml_encoding = 'utf-32le'
                xml_data = unicode(xml_data, 'utf-32le').encode('utf-8')
            elif xml_data[:4] == '\x00\x00\xfe\xff':
                # UTF-32BE with BOM
                sniffed_xml_encoding = 'utf-32be'
                xml_data = unicode(xml_data[4:], 'utf-32be').encode('utf-8')
            elif xml_data[:4] == '\xff\xfe\x00\x00':
                # UTF-32LE with BOM
                sniffed_xml_encoding = 'utf-32le'
                xml_data = unicode(xml_data[4:], 'utf-32le').encode('utf-8')
            elif xml_data[:3] == '\xef\xbb\xbf':
                # UTF-8 with BOM
                sniffed_xml_encoding = 'utf-8'
                xml_data = unicode(xml_data[3:], 'utf-8').encode('utf-8')
            else:
                sniffed_xml_encoding = 'ascii'
                pass
        except:
            xml_encoding_match = None
        xml_encoding_match = re.compile(
            '^<\?.*encoding=[\'"](.*?)[\'"].*\?>').match(xml_data)
        if not xml_encoding_match and isHTML:
            regexp = re.compile('<\s*meta[^>]+charset=([^>]*?)[;\'">]', re.I)
            xml_encoding_match = regexp.search(xml_data)
        if xml_encoding_match is not None:
            xml_encoding = xml_encoding_match.groups()[0].lower()
            if isHTML:
                self.declaredHTMLEncoding = xml_encoding
            if sniffed_xml_encoding and \
               (xml_encoding in ('iso-10646-ucs-2', 'ucs-2', 'csunicode',
                                 'iso-10646-ucs-4', 'ucs-4', 'csucs4',
                                 'utf-16', 'utf-32', 'utf_16', 'utf_32',
                                 'utf16', 'u16')):
                xml_encoding = sniffed_xml_encoding
        return xml_data, xml_encoding, sniffed_xml_encoding


    def find_codec(self, charset):
        return self._codec(self.CHARSET_ALIASES.get(charset, charset)) \
               or (charset and self._codec(charset.replace("-", ""))) \
               or (charset and self._codec(charset.replace("-", "_"))) \
               or charset

    def _codec(self, charset):
        if not charset: return charset
        codec = None
        try:
            codecs.lookup(charset)
            codec = charset
        except (LookupError, ValueError):
            pass
        return codec

    EBCDIC_TO_ASCII_MAP = None
    def _ebcdic_to_ascii(self, s):
        c = self.__class__
        if not c.EBCDIC_TO_ASCII_MAP:
            emap = (0,1,2,3,156,9,134,127,151,141,142,11,12,13,14,15,
                    16,17,18,19,157,133,8,135,24,25,146,143,28,29,30,31,
                    128,129,130,131,132,10,23,27,136,137,138,139,140,5,6,7,
                    144,145,22,147,148,149,150,4,152,153,154,155,20,21,158,26,
                    32,160,161,162,163,164,165,166,167,168,91,46,60,40,43,33,
                    38,169,170,171,172,173,174,175,176,177,93,36,42,41,59,94,
                    45,47,178,179,180,181,182,183,184,185,124,44,37,95,62,63,
                    186,187,188,189,190,191,192,193,194,96,58,35,64,39,61,34,
                    195,97,98,99,100,101,102,103,104,105,196,197,198,199,200,
                    201,202,106,107,108,109,110,111,112,113,114,203,204,205,
                    206,207,208,209,126,115,116,117,118,119,120,121,122,210,
                    211,212,213,214,215,216,217,218,219,220,221,222,223,224,
                    225,226,227,228,229,230,231,123,65,66,67,68,69,70,71,72,
                    73,232,233,234,235,236,237,125,74,75,76,77,78,79,80,81,
                    82,238,239,240,241,242,243,92,159,83,84,85,86,87,88,89,
                    90,244,245,246,247,248,249,48,49,50,51,52,53,54,55,56,57,
                    250,251,252,253,254,255)
            import string
            c.EBCDIC_TO_ASCII_MAP = string.maketrans( \
            ''.join(map(chr, range(256))), ''.join(map(chr, emap)))
        return s.translate(c.EBCDIC_TO_ASCII_MAP)

    MS_CHARS = { '\x80' : ('euro', '20AC'),
                 '\x81' : ' ',
                 '\x82' : ('sbquo', '201A'),
                 '\x83' : ('fnof', '192'),
                 '\x84' : ('bdquo', '201E'),
                 '\x85' : ('hellip', '2026'),
                 '\x86' : ('dagger', '2020'),
                 '\x87' : ('Dagger', '2021'),
                 '\x88' : ('circ', '2C6'),
                 '\x89' : ('permil', '2030'),
                 '\x8A' : ('Scaron', '160'),
                 '\x8B' : ('lsaquo', '2039'),
                 '\x8C' : ('OElig', '152'),
                 '\x8D' : '?',
                 '\x8E' : ('#x17D', '17D'),
                 '\x8F' : '?',
                 '\x90' : '?',
                 '\x91' : ('lsquo', '2018'),
                 '\x92' : ('rsquo', '2019'),
                 '\x93' : ('ldquo', '201C'),
                 '\x94' : ('rdquo', '201D'),
                 '\x95' : ('bull', '2022'),
                 '\x96' : ('ndash', '2013'),
                 '\x97' : ('mdash', '2014'),
                 '\x98' : ('tilde', '2DC'),
                 '\x99' : ('trade', '2122'),
                 '\x9a' : ('scaron', '161'),
                 '\x9b' : ('rsaquo', '203A'),
                 '\x9c' : ('oelig', '153'),
                 '\x9d' : '?',
                 '\x9e' : ('#x17E', '17E'),
                 '\x9f' : ('Yuml', ''),}

def plominoPrint(plominoDocument, form_name, default_css=None, use_command=False):
    plominoDatabase = plominoDocument.getParentDatabase()
    form = plominoDatabase.getForm(form_name)
    html_content = plominoDocument.openWithForm(form)
    
    import ipdb; ipdb.set_trace()
    
    if default_css:
        default_css = pisa_css + default_css

    rel_path = '..'
    abs_path = '%s' % plominoDatabase.absolute_url()
    html_content = html_content.replace(rel_path, abs_path)
    u_html_content = UnicodeDammit(html_content).unicode.encode('UTF-8')

    if use_command:
        SRC = '/tmp/test_in.html'
        input_file = open(SRC, 'w')
        input_file.write(html_content)
        input_file.close()
        xml = os.popen("xhtml2pdf %s -" % SRC).read()
        os.remove(SRC)
#        output_file = open('/tmp/test_out.pdf', 'w')
#        output_file.write(xml)
#        output_file.close()
    else:
        pdf = xhtml2pdf.CreatePDF(
            u_html_content,
            default_css=default_css,
            )
        xml = pdf.dest.getvalue()
    
    return xml


############################################################### CF P.IVA UTILS #

def is_valid_cf(cf):

    cf = str(cf)

    if len(cf) <> 16: return False

    alpha = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    odd_conv = {
        '0': 1, '1': 0, '2': 5, '3': 7, '4': 9, '5': 13, '6': 15, '7': 17,
        '8': 19, '9': 21,
        'A': 1, 'B': 0, 'C': 5, 'D': 7, 'E': 9, 'F': 13, 'G': 15, 'H': 17,
        'I': 19, 'J': 21, 'K': 2, 'L': 4, 'M': 18, 'N': 20, 'O': 11, 'P': 3,
        'Q': 6, 'R': 8, 'S': 12, 'T': 14, 'U': 16, 'V': 10, 'W': 22, 'X': 25,
        'Y': 24, 'Z': 23
    }
    
    even_conv = {
        '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
        '8': 8, '9': 9,
        'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6, 'H': 7, 'I': 8,
        'J': 9, 'K': 10, 'L': 11, 'M': 12, 'N': 13, 'O': 14, 'P': 15, 'Q': 16,
        'R': 17, 'S': 18, 'T': 19, 'U': 20, 'V': 21, 'W': 22, 'X': 23, 'Y': 24,
        'Z': 25
    }
    
    s = 0
    for char in cf[:-1][1::2]:
        s += even_conv[char.upper()]
    for char in cf[:-1][::2]:
        s += odd_conv[char.upper()]
        
    r = s%26
    
    r1 = alpha[r]
    
    return cf[-1].upper()==r1
    
def is_valid_piva(piva):
    
    piva = str(piva)
    if len(piva) <> 11: return False
    
    s = 0
    for char in piva[:-1][::2]:
        s += int(char)
    for char in piva[:-1][1::2]:
        x = 2*int(char)
        if x>9: x = x-9
        s += x
    
    r = s%10
    
    c = str(10-r)[-1]
    
    return piva[-1]==c
    

################################################################### MAIL UTILS #

#def test_mail(to, mail_text=''):
#    import smtplib

#server = 'smtp.gmail.com'
#user = 'manuele.pesenti'
#password = 'p0TA31le'

#recipients = ['user@mail.com', 'other@mail.com']
#sender = 'manuele.pesenti@mail.com'
#message = 'Hello World'

#session = smtplib.SMTP(server, '587')
## if your SMTP server doesn't need authentications,
## you don't need the following line:
#session.login(user, password)
#session.sendmail(sender, recipients, message)
#    #    host = getToolByName(context, 'MailHost')
#    #    sender = context.getProperty('email_from_address')
#    #    try:
#    #        host.send(html_message, mto=[to], mfrom=sender, 
#    #        subject=title, encode=None, 
#    #        immediate=False, charset='utf8', msg_type=None)
#    #    except Exception, error:
#    #        return str(error)
#    #    else:
#    #        return ''


############################################################# PERMISSION UTILS #

#def has_permission(cases, permission_store={}, form_name='', element_name='', permission_name=''):
#    '''
#    
#    DA TESTARE
#    
#    form_name: <plominoForm name>
#    element_name: <plominoAction name> or <plominoHidewhen name>
#    permission_name: <could be any string "read" "write" are the most used>

#    cases = [dict(ruolo='', status='')]

#    permission_store = {
#        'form_name|element_name|permission_name': dict(
#            ruolo = lambda x: x in (..., ) # <- permission definition
#            status = lambda y: y not in (..., ) # <- permission definition
#        )
#    }
#    '''

#    permission_key = '|'.join((form_name, element_name, permission_name, ))

#    all_possible_keys = ['|'.join([a, b])
#        for a in (form_name, '')
#        for b in (element_name, '')]

#    #possible_keys = [k for k in all_possible_keys if k in permission_store]

#    possible_keys = [k for k in permission_store if k.split('|')[:2] in [v.split('|') for v in all_possible_keys]]

#    if not possible_keys: return True 

#    for k in possible_keys:
#        if k.split('|')[2] in ('', 'any', permission_name, ):
#            permission = permission_store.get(k)
#            if not permission: return True # No permissions setted up about your case. You pass the guard!
#            for case in cases:
#                ruolo = case.get('ruolo') or ''
#                status = case.get('status') or ''
#                if permission(ruolo, status): return True # If just one condition specified is satified you pass the guard.

#    return False

