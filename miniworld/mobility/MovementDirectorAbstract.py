
# encoding: utf-8

__author__ = "Patrick Lampe, Nils schmidt"
__email__ = "uni at lampep.de, schmidt89 at informatik.uni-marburg.de"

# TODO:


class MovementDirectorAbstract():

    def simulate_one_step(self):
        """
        simulates the next step for all nodes
        """
        for node in self.nodes.get_list_of_nodes().values():
            node.step()
