from Products.CMFCore.utils import getToolByName

def getChainFor(context):
    pw = getToolByName(context, 'portal_workflow')
    return pw.getChainFor(context)

def getStatesInfo(doc, *args):
    """
    Restituisce informazioni sulgli stati della pratica per tutti i
    workflow ad essa associati.
    Argomenti richiedibili: title (default), description,
        transitions, permission_roles, group_roles, var_values
    """

    args = list(args)
    if 'title' not in args:
        args.append('title')

    pw = getToolByName(doc.getParentDatabase(), 'portal_workflow')
    
    infos = []
    for wf_id in pw.getChainFor(doc):

        wf = getToolByName(pw, wf_id)
        status_id = wf.getInfoFor(doc, 'review_state', None)

        if status_id:
            status = getToolByName(wf.states, status_id)
            info = dict([(k, getattr(status, k)) for k in args])
            info['id'] = status.getId()

            infos.append(info)

    if len(infos) == 1:
        return infos[0]
    else:
        return infos

def doActionIfAny(doc, wf_var='transition_on_save', *args):
    """
    Esegue le transizioni del workflow che devono essere eseguite al
    salvataggio della pratica.
    wf_var: nome della variabile di workflow contenente la lista delle
        transizioni abilitate. Se valutata come falsa le transizioni
        disponibili sono considerate tutte eseguibili.
    """
    
    pw = getToolByName(doc, 'portal_workflow')
    transitions = []
    for wf_id in getChainFor(doc):
        wf = getToolByName(pw, wf_id)
        for tr in wf.transitions:
            execute = False
            if wf_var:
                execute = tr in wf.getInfoFor(doc, wf_var, [])
            else:
                execute = True
            if execute and wf.isActionSupported(doc, tr):
                wf.doActionFor(doc, tr)

    return getStatesInfo(doc, *args)
