from Products.CMFPlomino.PlominoForm import PlominoForm
from Products.CMFPlomino.PlominoDocument import PlominoDocument
from Products.CMFPlomino.index import PlominoIndex

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
InitializeClass(PlominoDocument)

defaults = dict(
    parentKey = 'parentDocument',
    parentLinkKey = 'linkToParent',
    childrenListKey = 'listOf_%s'
)


def getPath(doc, virtual=False):

    doc_path = doc.doc_path()
    
    pd_path_list = doc.REQUEST.physicalPathToVirtualPath(doc_path) if virtual else None

    return '/'.join(pd_path_list or doc_path)


def setParenthood(childDocument, parent_id, CASCADE=True, setDocLink=False, **kwargs):
    '''
    Set parent reference in child document
    '''

    locals().update(defaults)
    locals().update(kwargs)
    
    ParentDocument = self.getParentDatabase().getDocument(parent_id)
    Parent_path = getPath(parentDocument)

    childDocument.setItem(parentKey, ParentDocument.getId())
    childDocument.setItem('CASCADE', CASCADE)
    if setDocLink:
        childDocument.setItem(parentLinkKey, [Parent_path])


def setChildhood(childDocument, parent_id, backToParent='anchor', **kwargs):
    '''
    Set child reference on parent document
    '''
    
    locals().update(defaults)
    locals().update(kwargs)
    
    db = childDocument.getParentDatabase()
    ParentDocument = db.getDocument(parent_id)
    
    childrenList_name = childrenListKey % childDocument.Form
    childrenList = ParentDocument.getItem(childrenList_name, []) or []
    childrenList.append(getPath(childDocument))
    
    idx = db.getIndex()
    for fieldname in (parentKey, 'CASCADE', ):
        if fieldname not in idx.indexes():
            idx.createFieldIndex(fieldname, 'TEXT', refresh=True)
    
    ParentDocument.setItem(childrenList_name, childrenList)
    
    if backToParent:
        backUrl = ParentDocument.absolute_url()
        if backToParent == 'anchor':
            backUrl = '%s#%s' % (backUrl, childrenList_name)
        childDocument.setItem('plominoredirecturl', backUrl)


def oncreate_child(self, parent_id='', backToParent='anchor', **kwargs):
    '''
    Actions to perform on creation of a childDocument
    '''

    locals().update(defaults)
    locals().update(kwargs)
    
    # if no parent_id passed
    # first take from the child itself
    if not parent_id:
        parent_id = self.getItem(parentKey)
    
    # second take from the request
    if not parent_id:
        parent_id = self.REQUEST.get(parentKey)

    if parent_id:
        setParenthood(self, parent_id, child.id, **kwargs)
        setChildhood(self, parent_id, child.id, backToParent, **kwargs)


def onsave_child(self):
    '''
    Actions to perform on save of a childDocument
    '''
    if not self.isNewDocument():
        if self.getItem('plominoredirecturl'):
            self.removeItem('plominoredirecturl')


def ondelete_child(self, anchor=True, **kwargs):
    '''
    Actions to perform on deletion of a childDocument
    '''
    
    locals().update(defaults)
    locals().update(kwargs)
    
    db = self.getParentDatabase()
    ParentDocument = db.getDocument(self.getItem(parentKey))
    childrenList_name = childrenListKey % self.Form
    childrenList = ParentDocument.getItem(childrenList_name)
    url = getPath(self)
    childrenList.remove(url)
    ParentDocument.setItem(childrenList_name, childrenList)
    
    backUrl = parent.absolute_url()
    if anchor:
        backUrl = '%s#%s' % (backUrl, childrenList_name)
    self.REQUEST.set('returnurl', backUrl)

def ondelete_parent(self, **kwargs):
    '''
    Actions to perform on deletion of a parentDocument
    '''
    
    locals().update(defaults)
    locals().update(kwargs)

    db = self.getParentDatabase()
    idx = db.getIndex()
    request = {parentKey: parent.id}
    res = idx.dbsearch(request)
    toRemove = []
    for rec in res:
        if rec.CASCADE:
            toRemove += [rec.id]
        else:
            rec.getObject().removeItem(parentKey)
    db.deleteDocuments(ids=toRemove, massive=False)


def create_child(self, form_name, request={}, applyhidewhen=True, **kwargs):
    '''
    Use it to create a child document from scripts
    '''

    db = self.getParentDatabase()
    form = db.getForm(form_name)
    ChildDocument = db.createDocument()
    ChildDocument.setItem('Form', form_name)
    form.readInputs(ChildDocument, request, applyhidewhen=applyhidewhen)
    setParenthood(self, parent.id, doc.id, **kwargs)
    setChildhood(self, parent.id, doc.id, **kwargs)
    ChildDocument.save()
    return ChildDocument.getId()


PlominoDocument.create_child = create_child
PlominoDocument.oncreate_child = oncreate_child
PlominoDocument.onsave_child = onsave_child
PlominoDocument.ondelete_child = ondelete_child
PlominoDocument.ondelete_parent = ondelete_parent
