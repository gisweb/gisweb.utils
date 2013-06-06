#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Libreria dedicata (anche) ad esporre metodi di Plone che si vuole rendere
accessibili
"""

from Products.CMFCore.utils import getToolByName

#try:
#    from plone.app.content.batching import Batch as ploneBatch # Plone < 4.3
#    HAS_PLONE43 = False
#except ImportError:
#    from plone.batching import Batch as ploneBatch # Plone >= 4.3
#    HAS_PLONE43 = True

def rolesOfPermission(obj, permission):
    """ Exposes rolesOfPermission """
    return obj.rolesOfPermission(permission)

def sendMail(context, Object, msg, To, From='', as_script=False):
    """
    Facility for sending emails using Plone MailHost
    
    * context: the context (ex. portal) from which get the MailHost
    * msg: dtml type is requested
    * To: the recipient list
    * From: the sender address
    * as_script: if true error message will not be notified through PortalMessage
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

#def Batch(**kwargs):
#    """
#    così non si può usare per problemi di permessi sugli oggetti in output
#    """
#    for keys in (('pagesize', 'size', ), ('pagenumber', 'start', ), ):
#        if not HAS_PLONE43:
#            keys = list(reversed(keys))
#        ok, nk = keys
#        if ok in kwargs:
#            kwargs[nk] = kwargs.pop(ok)
#        
#    return ploneBatch(**kwargs)
