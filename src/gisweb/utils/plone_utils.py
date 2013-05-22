#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Libreria dedicata (anche) ad esporre metodi di Plone che si vuole rendere
accessibili
"""

from Products.CMFCore.utils import getToolByName

def rolesOfPermission(obj, permission):
    """ Exposes rolesOfPermission """
    return obj.rolesOfPermission(permission)

def sendMail(context, Object, msg, To, From='', as_script=False):
    """
    Facility for sending emails using Plone MailHost
    
    msg: dtml is requested
    
    """
    
    success = 0
    
    messages = []
    mail_host = getToolByName(context, 'MailHost')
    try:
        mail_host.send(msg, To, From or mail_host.getProperty('email_from_address'), Object)
    except Exception as err:
        err_msg = '%s: %s' % (type(err), err)
        err = (unicode(err_msg, errors='replace'), 'error')
        wrn_msg = 'ATTENZIONE! Non è stato possibile inviare la mail con oggetto: %s' % Object
        wrn = (unicode(wrn_msg, errors='replace'), 'warning')
        messages.append(err)
        messages.append(wrn)
    else:
        success = 1
        ok_msg = 'La mail con oggetto "%s" è stata inviata correttamente' % Object
        ok = (unicode(ok_msg, errors='replace'), 'info')
        messages.append(ok)
    
    if not as_script:
        plone_tools = getToolByName(context.getParentDatabase().aq_inner, 'plone_utils')
        for imsg in messages:    
            plone_tools.addPortalMessage(*imsg, request=context.REQUEST)
        return success
    else:
        return dict(success=success, messages=messages)
