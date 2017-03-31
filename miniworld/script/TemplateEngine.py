
__author__ = 'Nils Schmidt'

from miniworld.log import get_logger

KEYWORD_NODE_ID = "node_id"

log = get_logger(__name__)

class TemplateEngine:
    '''
    A template engine for writing template shell scripts.
    Keywords are optionally! If unusued, an empty string is used instead and a warning is logged.
    '''

    def __init__(self, script_str):
        '''
        Parameters
        ----------
        script_str
            The script as string.
        '''
        self.script_str = script_str

    def render(self, **kwargs):

        return self.script_str.format(**kwargs)

def render_script_from_flo(flo, **kwargs):
    '''
    Parameters
    ----------
    flo : file-like-object
    '''
    flo.seek(0)
    te = TemplateEngine(flo.read())
    return te.render(**kwargs)

if __name__ == '__main__':

    #from miniworld.model.emulation.nodeclass import NodeClass
    #nc = NodeClass()
    #nc.

    print(render_script_from_flo("../../templates/std_network.sh"))
    print(render_script_from_flo("../../templates/std_network.sh", ipv4_addr = "192.168.0.1"))
    #print render_script_from_flo("../../templates/std_network.sh", **{KEYWORD_IPV4_ADDR_AP : "192.168.0.1"})


    # with open("../../templates/std_network.sh", "r") as f:
    #     te = TemplateEngine(f.read())
    #     print te.render()
    #     print te.render(ipv4_addr = "192.168.0.1")


