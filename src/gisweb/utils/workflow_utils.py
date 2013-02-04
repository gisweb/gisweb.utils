from Products.CMFCore.utils import getToolByName

def getChainFor(context):
    """
    Restituisce gli id dei workflow associati al contesto.
    """
    pw = getToolByName(context.getParentDatabase(), 'portal_workflow')
    return pw.getChainFor(context)


def getInfoFor(context, arg, *args, **kwargs):
    """
    Cicla getInfoFor su tutti i workflow richiesti o su quelli assegnati
    al documento.
    """

    pw = getToolByName(context.getParentDatabase(), 'portal_workflow')

    infos = {}
    for wf_id in kwargs.get('wf_ids') or getChainFor(context):
        wf = getToolByName(pw, wf_id)
        infos[wf_id] = dict([(var, wf.getInfoFor(context, var, None)) \
            for var in set([arg]+list(args))])

    if kwargs.get('single') in (None, True, ) and len(infos)==1:
        val = infos.values()[0]
        if len(val) == 1:
            return val.values()[0]
        else:
            return val
    else:
        return infos


def getWorkflowInfo(doc, wf_ids=[], single=True, args=[]):
    """
    Restituisce informazioni su tutti i workflow associati alla pratica.
    Argomenti richiedibili: title (default), description,
        initial_state, state_var
    """

    pw = getToolByName(doc.getParentDatabase(), 'portal_workflow')

    infos = []
    for wf_id in wf_ids or getChainFor(doc):
        wf = getToolByName(pw, wf_id)
        info = dict([(k, getattr(wf, k)) for k in set(['title']+args)])
        info['id'] = wf.getId()
        infos.append(info)

    if len(infos) == 1 and single:
        return infos[0]
    else:
        return infos

def getInfoForState(context, wf_id, state_id, args=[]):
    """
    Restituisce informazioni sullo stato richiesto.
    """

    pw = getToolByName(context.getParentDatabase(), 'portal_workflow')
    wf = getToolByName(pw, wf_id)
    status = getToolByName(wf.states, state_id)

    return dict([(k, getattr(status, k)) for k in set(['title']+args)])


def getStatesInfo(doc, state_id=None, single=True, args=[]):
    """
    Restituisce informazioni sugli stati della pratica per tutti i
    workflow ad essa associati.
    Argomenti richiedibili: title (default), description,
        transitions, permission_roles, group_roles, var_values
    single=True: solitamente si ha a che fare con un workflow solo quindi
        ci si aspetta un solo stato
    """

    pw = getToolByName(doc.getParentDatabase(), 'portal_workflow')

    infos = []
    for wf_id in getChainFor(doc):

        wf = getToolByName(pw, wf_id)
        status_id = state_id or wf.getInfoFor(doc, 'review_state', None)

        if status_id:
            status = getToolByName(wf.states, status_id)
            info = dict([(k, getattr(status, k)) for k in set(['title']+args)])
            info['id'] = status.getId()
            info['wf_id'] = wf_id
            infos.append(info)

    if len(infos) == 1 and single:
        return infos[0]
    else:
        return infos


def getTransitionsInfo(doc, single=False, supported_only=True, args=[]):
    """
    Restituisce informazioni sulle transizioni disponibili per la pratica
    relative ai workflow ad essa associati.
    Argomenti richiedibili: title (default), description, ...
    """

    args = list(args)
    if 'title' not in args:
        args.append('title')

    tr_infos = getStatesInfo(doc, state_id=None, single=False, args=['transitions'])

    pw = getToolByName(doc.getParentDatabase(), 'portal_workflow')

    infos = []
    for i in tr_infos:
        wf = getToolByName(pw, i['wf_id'])
        tr_def = {'wf_id': i['wf_id']}
        for tr_id in i['transitions']:
            if (supported_only and wf.isActionSupported(doc, tr_id)) or not supported_only:
                transition = getToolByName(wf.transitions, tr_id)
                info = dict([(k, getattr(transition, k)) for k in set(['title']+args)])
                info['id'] = transition.getId()
                info.update(tr_def)

                infos.append(info)

    if len(infos) == 1 and single:
        return infos[0]
    else:
        return infos

def doActionIfAny(doc, wf_var='transition_on_save', args=[]):
    """
    Esegue le transizioni del workflow che devono essere eseguite al
    salvataggio della pratica.
    wf_var: nome della variabile di workflow contenente la lista delle
        transizioni abilitate. Se valutata come falsa le transizioni
        disponibili sono considerate tutte da eseguire.
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

    return getStatesInfo(doc, args=args)
