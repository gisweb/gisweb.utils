from Products.CMFCore.utils import getToolByName

from Products.CMFPlomino.PlominoForm import PlominoForm
from Products.CMFPlomino.PlominoDocument import PlominoDocument
from Products.CMFPlomino.index import PlominoIndex
from Products.CMFPlomino.exceptions import PlominoScriptException
#from Products.CMFPlomino.PlominoAction import PlominoAction

from workflow_utils import getChainFor, getStatesInfo, getTransitionsInfo
from workflow_utils import getWorkflowInfo, getInfoForState, getInfoFor

from url_utils import urllib_urlencode

# Security import
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.CMFPlomino.config import READ_PERMISSION

PlominoIndex.security = ClassSecurityInfo()
PlominoIndex.security.declareProtected(READ_PERMISSION, 'create_child')
PlominoIndex.security.declareProtected(READ_PERMISSION, 'oncreate_child')
PlominoIndex.security.declareProtected(READ_PERMISSION, 'onsave_child')
PlominoIndex.security.declareProtected(READ_PERMISSION, 'ondelete_child')
PlominoIndex.security.declareProtected(READ_PERMISSION, 'ondelete_parent')
PlominoIndex.security.declareProtected(READ_PERMISSION, 'beforecreate_child')
PlominoIndex.security.declareProtected(READ_PERMISSION, 'wf_getChainFor')
PlominoIndex.security.declareProtected(READ_PERMISSION, 'wf_statesInfo')
PlominoIndex.security.declareProtected(READ_PERMISSION, 'wf_transitionsInfo')
PlominoIndex.security.declareProtected(READ_PERMISSION, 'wf_workflowInfo')

InitializeClass(PlominoDocument)

defaults = dict(
    parentKey = 'parentDocument',
    parentLinkKey = 'linkToParent',
    childrenListKey = 'childrenList_%s'
)


def getPath(doc, virtual=False):
    '''
    uniformo il recupero del valore per il doclink
    '''
    doc_path = doc.doc_path()
    pd_path_list = doc.REQUEST.physicalPathToVirtualPath(doc_path) if virtual else None
    return '/'.join(pd_path_list or doc_path)


def setParenthood(ChildDocument, parent_id, CASCADE=True, setDocLink=False, **kwargs):
    '''
    Set parent reference in child document
    '''

    parentKey = kwargs.get('parentKey') or defaults.get('parentKey')
    parentLinkKey = kwargs.get('parentLinkKey') or defaults.get('parentLinkKey')

    ParentDocument = ChildDocument.getParentDatabase().getDocument(parent_id)
    Parent_path = getPath(ParentDocument)

    ChildDocument.setItem(parentKey, ParentDocument.getId())
    ChildDocument.setItem('CASCADE', CASCADE)
    if setDocLink:
        ChildDocument.setItem(parentLinkKey, [Parent_path])
        ChildDocument.REQUEST.set(parentLinkKey, [Parent_path])


def setChildhood(ChildDocument, parent_id, backToParent='anchor', **kwargs):
    '''
    Set child reference on parent document
    '''

    parentKey = kwargs.get('parentKey') or defaults.get('parentKey')
    childrenListKey = kwargs.get('childrenListKey') or defaults.get('childrenListKey')

    db = ChildDocument.getParentDatabase()
    ParentDocument = db.getDocument(parent_id)

    childrenList_name = childrenListKey % ChildDocument.Form
    childrenList = ParentDocument.getItem(childrenList_name, []) or []
    childrenList.append(getPath(ChildDocument))

    idx = db.getIndex()
    for fieldname in (parentKey, 'CASCADE', ):
        if fieldname not in idx.indexes():
            idx.createFieldIndex(fieldname, 'TEXT', refresh=True)

    ParentDocument.setItem(childrenList_name, childrenList)

    if backToParent:
        backUrl = ParentDocument.absolute_url()
        if backToParent == 'anchor':
            backUrl = '%s#%s' % (backUrl, childrenList_name)
        ChildDocument.setItem('plominoredirecturl', backUrl)


def oncreate_child(self, parent_id='', backToParent='anchor', **kwargs):
    '''
    Actions to perform on creation of a ChildDocument
    '''

    parentKey = kwargs.get('parentKey') or defaults.get('parentKey')

    # if no parent_id passed
    # first take from the child itself
    #if not parent_id:
        #parent_id = self.getItem(parentKey)

    # second take from the request
    if not parent_id:
        parent_id = self.REQUEST.get(parentKey)

    if parent_id:
        setParenthood(self, parent_id, **kwargs)
        setChildhood(self, parent_id, backToParent, **kwargs)

def onsave_child(self, backToParent=False):
    '''
    Actions to perform on save of a ChildDocument
    '''
    if not self.isNewDocument():
        if self.getItem('plominoredirecturl') and not backToParent:
            self.removeItem('plominoredirecturl')


def ondelete_child(self, anchor=True, **kwargs):
    '''
    Actions to perform on deletion of a ChildDocument
    '''

    parentKey = kwargs.get('parentKey') or defaults.get('parentKey')
    childrenListKey = kwargs.get('childrenListKey') or defaults.get('childrenListKey')

    if parentKey in self.getItems():
        db = self.getParentDatabase()
        ParentDocument = db.getDocument(self.getItem(parentKey))
        childrenList_name = childrenListKey % self.Form
        childrenList = ParentDocument.getItem(childrenList_name)
        url = getPath(self)
        childrenList.remove(url)
        ParentDocument.setItem(childrenList_name, childrenList)

        backUrl = ParentDocument.absolute_url()
        if anchor:
            backUrl = '%s#%s' % (backUrl, childrenList_name)
        self.REQUEST.set('returnurl', backUrl)

def ondelete_parent(self, **kwargs):
    '''
    Actions to perform on deletion of a ParentDocument
    '''

    parentKey = kwargs.get('parentKey') or defaults.get('parentKey')

    db = self.getParentDatabase()
    idx = db.getIndex()
    request = {parentKey: self.id}
    res = idx.dbsearch(request)
    toRemove = []
    for rec in res:
        if rec.CASCADE:
            toRemove += [rec.id]
        else:
            rec.getObject().removeItem(parentKey)
    db.deleteDocuments(ids=toRemove, massive=False)
    self.REQUEST.set('returnurl', db.absolute_url())

def getWhereToRedirect(db, redirect_to, using, **kwargs):

    destination = db.getView(redirect_to) or db.getForm(redirect_to) or db
    messages = []

    if destination==db and redirect_to:
        messages.append(('Destination "%s" not found.' % redirect_to, 'error'))

    if hasattr(destination, using):
        destinationUrl = '%s/%s' % (destination.absolute_url(), using)
    else:
        destinationUrl = destination.absolute_url()
        if using:
            messages.append(('Template "%s" not found.' % using, 'error'))

    if kwargs:
        query_string = urllib_urlencode(kwargs)
        destinationUrl += '?%s' % query_string

    return destinationUrl, messages


def beforecreate_child(self, redirect_to='', using='', message=(), **kwargs):
    """
    Action to take before child creation.
    message: ("Indicazioni per l'utente", 'info')
    """

    parentKey = kwargs.get('parentKey') or defaults.get('parentKey')
    db = self.getParentDatabase()

    if not db.getDocument(self.REQUEST.get(parentKey)):
        destinationUrl, messages = getWhereToRedirect(db, redirect_to, using, **kwargs)
        if self.REQUEST.get(parentKey):
            messages.append(('Given id seams not to correspond to a valid plominoDocument.', 'error'))
        else:
            if isinstance(message, basestring):
                message = (message, )
            messages.append(message or ('No plominoDocument id given.', 'warning'))
        plone_tools = getToolByName(db.aq_inner, 'plone_utils')
        for msg in messages:
            plone_tools.addPortalMessage(*msg, request=self.REQUEST)
        self.REQUEST.RESPONSE.redirect(destinationUrl)


def create_child(self, form_name, request={}, applyhidewhen=True, **kwargs):
    '''
    Use it to create a child document from scripts
    '''

    db = self.getParentDatabase()
    form = db.getForm(form_name)
    ChildDocument = db.createDocument()
    ChildDocument.setItem('Form', form_name)
    form.readInputs(ChildDocument, request, applyhidewhen=applyhidewhen)
    setParenthood(ChildDocument, self.id, **kwargs)
    setChildhood(ChildDocument, self.id, **kwargs)
    ChildDocument.save()
    return ChildDocument.getId()

PlominoDocument.create_child = create_child
PlominoDocument.oncreate_child = oncreate_child
PlominoDocument.onsave_child = onsave_child
PlominoDocument.ondelete_child = ondelete_child
PlominoDocument.ondelete_parent = ondelete_parent
PlominoForm.beforecreate_child = beforecreate_child

def wf_getChainFor(self):
    return getChainFor(context)

def wf_workflowInfo(self, wf_ids=None, single=True, args=[]):
    return getWorkflowInfo(self, wf_ids=wf_ids, single=single, args=args)

def wf_statesInfo(self, state_id=None, single=True, args=[]):
    return getStatesInfo(self, state_id=state_id, single=single, args=args)

def wf_transitionsInfo(self, single=False, supported_only=True, args=[]):
    return getTransitionsInfo(self, single=single, supported_only=supported_only, args=args)

def wf_getInfoForState(self, wf_id, state_id, args=[]):
    return getInfoForState(self, wf_id, state_id, args=args)

def wf_getInfoFor(self, arg, *args, **kwargs):
    return getInfoFor(self, arg, *args, **kwargs)

PlominoDocument.wf_getChainFor = wf_getChainFor
PlominoDocument.wf_workflowInfo = wf_workflowInfo
PlominoDocument.wf_statesInfo = wf_statesInfo
PlominoDocument.wf_transitionsInfo = wf_transitionsInfo
PlominoDocument.wf_getInfoFor = wf_getInfoFor
PlominoForm.wf_getChainFor = wf_getChainFor
PlominoForm.wf_workflowInfo = wf_workflowInfo
PlominoForm.wf_statesInfo = wf_statesInfo
PlominoForm.wf_transitionsInfo = wf_transitionsInfo
PlominoForm.wf_getInfoForState = wf_getInfoForState
