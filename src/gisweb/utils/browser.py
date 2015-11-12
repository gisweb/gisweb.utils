from plone.app.controlpanel.filter import FilterControlPanelAdapter


class ResetFilters(object):
    def __init__(self, context, request):
        self.context, self.request = context, request
    def __call__(self):
        adapter = FilterControlPanelAdapter(self.context)
        adapter.nasty_tags = []
        adapter.stripped_tags = []
        adapter.custom_tags += ['iframe', 'embed']
        self.request.response.redirect(
            self.context.absolute_url() + '/@@filter-controlpanel')
