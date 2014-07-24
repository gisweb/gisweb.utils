from Products.CMFCore.utils import getToolByName

def getChainFor(context):
    """
    Restituisce gli id dei workflow associati al contesto.
    """
    pw = getToolByName(context.getParentDatabase(), 'portal_workflow')
    return pw.getChainFor(context)


def updateAllRoleMappingsFor(doc, script=False):
    """ Changes the object permissions according to the current workflow states. """

    pw = getToolByName(doc.getParentDatabase(), 'portal_workflow')
    changes = dict()

    wf_ids = pw.getChainFor(doc)

    # do precedenza al primo wf della catena
    for wf_id in reversed(wf_ids):
        wf = getToolByName(pw, wf_id)
        changes[wf_id] = dict(review_state=0)
        if not pw.getStatusOf(wf_id, doc):
            new_state = wf._executeTransition(doc)
            if new_state:
                changes[wf_id]['new_state'] = new_state.getId()
        changes[wf_id]['permissions'] = wf.updateRoleMappingsFor(doc)

    if script:
        import transaction
        transaction.commit()

    return changes


def getInfoFor(context, arg, *args, **kwargs):
    """
    Basically expose the getInfoFor method of the associated workflows.
    Accepted args:
    * wf_id: id of the desidered workflow to probe
        (by default the first is considered).
    * as_list: if true the result is returned in a list
    """

    pw = getToolByName(context.getParentDatabase(), 'portal_workflow')

    wf_id = kwargs.get('wf_id') or context.wf_statesInfo()[0]['wf_id']
    wf = getToolByName(pw, wf_id)

    if args:
        args = set(i for i in (arg, )+args)
        if kwargs.get('as_list'):
            return [wf.getInfoFor(context, var, None) for var in args]
        else:
            return dict((var, wf.getInfoFor(context, var, None), ) \
                for var in args)
    else:
        return wf.getInfoFor(context, arg, None)


def getWorkflowInfo(doc, single=True, args=[], **kwargs):
    """
    Restituisce informazioni su tutti i workflow associati alla pratica.
    Argomenti richiedibili: title (default), description,
        initial_state, state_var
    """

    pw = getToolByName(doc.getParentDatabase(), 'portal_workflow')

    wf_ids = kwargs.get('wf_ids') or []
    if not wf_ids and 'wf_id' in kwargs:
        single = True
        wf_ids = [kwargs['wf_id']]
    else:
        single = False

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

def getInfos(From, default, *args):
    """
    """
    info = dict()
    for k in args:
        try:
            info[k] = getattr(From, k)
        except AttributeError, err:
            if default:
                info[k] = default

    return info

def getStatesInfo(doc, state_id='review_state', args=[], default=None, **kwargs):
    """
    Restituisce informazioni sugli stati della pratica per tutti i
    workflow ad essa associati.
    Argomenti richiedibili: title (default), description,
        transitions, permission_roles, group_roles, var_values
    args: lista degli attributi richiesti
    default: valore di default (vedi getInfos)
    """

    pw = getToolByName(doc.getParentDatabase(), 'portal_workflow')

    args = set(['title']+args)

    single = False
    if 'wf_id' in kwargs:
        wf_list = (kwargs['wf_id'], )
        single = True
    elif 'wf_ids' in kwargs:
        wf_list = kwargs['wf_ids']
    else:
        wf_list = getChainFor(doc)

    infos = []
    for wf_id in wf_list:
        wf = getToolByName(pw, wf_id)

        if state_id in ('review_state', ):
            local_state_id = wf.getInfoFor(doc, 'review_state', None)
        else:
            local_state_id = state_id

        if local_state_id:
            status = getToolByName(wf.states, local_state_id)
            info = getInfos(status, default, *args)
            #info = dict([(k, getattr(status, k)) for k in set(['title']+args)])
            info['id'] = status.getId()
            info['wf_id'] = wf_id
            infos.append(info)
        else:
            for tmp_state_id in wf.states.keys():
                status = getToolByName(wf.states, tmp_state_id)
                info = getInfos(status, default, *args)
                #info = dict([(k, getattr(status, k)) for k in set(['title']+args)])
                info['id'] = status.getId()
                info['wf_id'] = wf_id
                infos.append(info)

    if len(infos) == 1 and single:
        return infos[0]
    else:
        return infos

def getTransitionsInfo(doc, supported_only=True, state_id='review_state',
    args=[], default=None, **kwargs):
    """
    Restituisce informazioni sulle transizioni disponibili per la pratica
    relative ai workflow ad essa associati.
    Argomenti richiedibili: title (default), description, ...
    """

    args = list(args)
    if 'title' not in args:
        args.append('title')

    # supported_only=True ha senso solo per le transizioni disponibili allo stato corrente
    supported_only = supported_only and state_id=='review_state'

    if 'wf_id' in kwargs:
        v = kwargs.pop('wf_id')
        kwargs['wf_ids'] = (v, )

    tr_infos = getStatesInfo(doc, state_id=state_id, args=['transitions'], **kwargs)

    pw = getToolByName(doc.getParentDatabase(), 'portal_workflow')

    infos = []
    for i in tr_infos:
        wf = getToolByName(pw, i['wf_id'])
        tr_def = {'wf_id': i['wf_id']}
        for tr_id in i['transitions']:

            if (state_id=='review_state' and supported_only \
                and wf.isActionSupported(doc, tr_id)) or not supported_only:
                transition = getToolByName(wf.transitions, tr_id)

                info = getInfos(transition, default, *set(['title']+args))

                info['id'] = transition.getId()
                info.update(tr_def)
                infos.append(info)

    return infos


def doActionIfAny(doc, wf_var='transition_on_save', args=[]):
    """
    Esegue le transizioni del workflow che devono essere eseguite al
    salvataggio della pratica.
    wf_var: nome della variabile di workflow contenente la lista delle
        transizioni abilitate. Se valutata come falsa le transizioni
        disponibili sono considerate arbitrariamente tutte da eseguire.
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
