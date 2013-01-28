#!/usr/bin/python
# -*- coding: utf-8 -*-

import codicefiscale as cf
import datetime

def cf_build(surname, name, year, month, day, sex, municipality):
    """``build(surname, name, year, month, day, sex, municipality) -> string``

    Computes the fiscal code for the given person data.

    eg: build('Rocca', 'Emanuele', 1983, 11, 18, 'M', 'D969') 
        -> RCCMNL83S18D969H
    """
    birthday = datetime.datetime(year, month, day)

    return cf.build(surname, name, birthday, sex, municipality)

def is_valid_cf(cf):
    ''' Verify the validity of an (italian) fiscal code 
    courtesy of: http://www.icosaedro.it/cf-pi/index.html
    '''

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
    ''' Vefify the validity of "partita IVA"  
    courtesy of: http://www.icosaedro.it/cf-pi/index.html
    '''
    
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
    
