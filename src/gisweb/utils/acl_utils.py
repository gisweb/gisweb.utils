#!/usr/bin/python
# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from zope.app.component.hooks import getSite

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

def getAllUserRoles(context):
    db = context.getParentDatabase()
    plominoRoles = db.getCurrentUserRoles()
    ploneRoles = db.getCurrentUser().getRolesInContext(context)
    return ploneRoles+plominoRoles
