# courtesy of: https://raw.github.com/web2py/web2py/master/gluon/contrib/populate.py

from misc import *
import cPickle
import random, re
from DateTime import DateTime
from decimal import Decimal

class Learner:
    def __init__(self):
        self.db = {}

    def learn(self, text):
        replacements1 = {'[^a-zA-Z0-9\.;:\-]': ' ',
                         '\s+': ' ', ', ': ' , ', '\. ': ' . ',
                         ': ': ' : ', '; ': ' ; '}
        for key, value in replacements1.items():
            text = re.sub(key, value, text)
        items = [item.lower() for item in text.split(' ')]
        for i in range(len(items) - 1):
            item = items[i]
            nextitem = items[i + 1]
            if item not in self.db:
                self.db[item] = {}
            if nextitem not in self.db[item]:
                self.db[item][nextitem] = 1
            else:
                self.db[item][nextitem] += 1

    def save(self, filename):
        cPickle.dump(self.db, open(filename, 'wb'))

    def load(self, filename):
        self.loadd(cPickle.load(open(filename, 'rb')))

    def loadd(self, db):
        self.db = db

    def generate(self, length=10000, prefix=False):
        replacements2 = {' ,': ',', ' \.': '.\n', ' :': ':', ' ;':
                         ';', '\n\s+': '\n'}
        keys = self.db.keys()
        key = keys[random.randint(0, len(keys) - 1)]
        words = key
        words = words.capitalize()
        regex = re.compile('[a-z]+')
        for i in range(length):
            okey = key
            if not key in self.db:
                break  # should not happen
            db = self.db[key]
            s = sum(db.values())
            i = random.randint(0, s - 1)
            for key, value in db.items():
                if i < value:
                    break
                else:
                    i -= value
            if okey == '.':
                key1 = key.capitalize()
            else:
                key1 = key
            if prefix and regex.findall(key1) and \
                    random.random() < 0.01:
                key1 = '<a href="%s%s">%s</a>' % (prefix, key1, key1)
            words += ' ' + key1
        text = words
        for key, value in replacements2.items():
            text = re.sub(key, value, text)
        return text + '.\n'

def da_du_ma(n=4):
    return ''.join([['da', 'du', 'ma', 'mo', 'ce', 'co',
                     'pa', 'po', 'sa', 'so', 'ta', 'to']
                    [random.randint(0, 11)] for i in range(n)])

learner = Learner()
learner.loadd(IUP)
def rndgenerate(**kw):
    return learner.generate(**kw)

def namegenerate(type='FIRST'):
    return random.choice(globals()['%s_NAMES' % type.upper()])

def dategenerate(s=-100, e=100, format=None, type="DATE"):
    d = random.randint(s, e)
    if type == "DATETIME":
        d += random.random()
    date = DateTime() + d
    if format:
        return date.strftime(format)
    else:
        return date

def numbergenerate(type='INTEGER', digits=5, negative=True, **kw):
    l = kw.get('lower') or 10**(digits-1)
    u = kw.get('upper') or 10**digits - 1
    i = random.randint(l, u)
    if negative and l>0:
        i *= random.choice((1, -1, ))
    #i = random.randint(-10000, 10000)
    if type == 'INTEGER':
        return i
    f = random.random()
    if type == 'FLOAT':
        return i+f
    elif type == 'DECIMAL':
        return Decimal('%f' % (i+f))
    
def boolgenerate():
    return random.choice((True, False, ))

def rndselection(vals=[], n=1):
    if vals:
        if n > 1:
            return random.sample(vals, n)
        else:
            return random.choice(vals)
    else:
        return ''

def rndCodFisco(as_dict=False):
    """
    order: "Comune", "Provincia", "CAP", "CodFisco", )
    TODO: support for sample??
    """
    if as_dict:
        return dict(zip(CodFiscoHeaders, random.choice(CodFisco)))
    else:
        return random.choice(CodFisco)

def latlongenerate(tl=(45, 9), br=(44, 8)):
    minlat = br[0]
    maxlat = tl[0]
    maxlon = tl[1]
    minlon = br[1]
    return random.uniform(minlon,maxlon), random.uniform(minlat,maxlat)
    