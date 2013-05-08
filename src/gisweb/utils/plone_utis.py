#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Libreria dedicata (anche) ad esporre metodi di Plone che si vuole rendere
accessibili
"""

def rolesOfPermission(context, permission):
    """ Exposes rolesOfPermission """
    return context.rolesOfPermission(permission)
