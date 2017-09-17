__author__ = 'Nils Schmidt'


class TemplateContentProvider:

    def get_template_dict(self, *args, **kwargs):
        ''' Return a dictionary with key/value pairs which shall be usable in a template '''
        raise NotImplementedError
