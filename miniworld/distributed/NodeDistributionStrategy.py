import json
import math
from collections import defaultdict, OrderedDict
from pprint import pprint

from miniworld.distributed.ServerScore import ServerScore
from miniworld.singletons import singletons


def factory():
    if singletons.config.is_distributed_scheduler_equal():
        return NDSEqual
    elif singletons.config.is_distributed_scheduler_score():
        return NDSScore
    else:
        raise ValueError("Value unknown!")


class NodeDistributionStrategy:
    """
    Attributes
    ----------
    server_score : dict
        Dict produced and readable by :py:class:`.ServerScore`
    """

    def __init__(self):
        self.server_score = None

    def distribute_emulation_nodes(node_ids, cnt_servers):
        raise NotImplementedError

    def apply_distribution_strategy(self, node_ids, cnt_servers, server_node_distribution,
                                    distribute_remaining_fair=True, distribute_remaining_server_ids=None
                                    ):
        """

        Parameters
        ----------
        node_ids: list<int>
        cnt_servers : int
        server_node_distribution : dict<int, int>
            How many nodes each server shall manage.
        distribute_remaining_fair : bool, optional (default is True)
            Distribute the remaining nodes equally
        distribute_remaining_server_ids : list<int>
            The server ids sorted by priority so that the fair distribution begins with the "better" servers.

        Returns
        -------
        dict<int, <list<int>>>
            The nodes distributed among the servers.
            e.g: {1 : [1,2], 2 : [3,4]}
        """

        res = defaultdict(list)
        if distribute_remaining_server_ids is None:
            distribute_remaining_server_ids = range(1, cnt_servers + 1)

        last_pos, cur_pos = 0, 0

        # init the dict for all servers (we need an entry even for servers who maintain no node!)
        for server_id in range(1, cnt_servers + 1):
            res[server_id]

        def check():
            if (last_pos >= len(node_ids)):
                # we are done here
                return True

        for server_id in range(1, cnt_servers + 1):

            if server_id not in server_node_distribution:
                break
            cur_pos += server_node_distribution[server_id]
            if check():
                return res

            res[server_id] = node_ids[last_pos:cur_pos]

            last_pos = cur_pos

        if distribute_remaining_fair:
            # distribute remaining nodes
            # can happen if len(node_ids) / cnt_servers is no integer
            while True:
                for server_id in distribute_remaining_server_ids:

                    if check():
                        return res
                    res[server_id].append(node_ids[last_pos])

                    last_pos += 1

        return res


class NDSEqual(NodeDistributionStrategy):
    # TODO: for core mode, we can minimize the number of tunnels!
    def distribute_emulation_nodes(self, node_ids, cnt_servers):
        server_node_distribution = {node_id: max(1, len(node_ids) // cnt_servers) for node_id in node_ids}
        return self.apply_distribution_strategy(node_ids, cnt_servers, server_node_distribution)


class NDSScore(NodeDistributionStrategy):
    def distribute_emulation_nodes(self, node_ids, cnt_servers):
        """

        Parameters
        ----------
        node_ids
        cnt_servers

        Returns
        -------

        """
        server_node_distribution = {}
        server_score_sorted_cpu_ranking_desc = list(OrderedDict(
            sorted(self.server_score.items(), key=lambda x: ServerScore.get_cpu_score(x[1]), reverse=True)).keys())

        # calculate for each server how mandy VMs fit into the RAM
        vm_size = singletons.scenario_config.get_qemu_memory_mb()

        sum_bogomips = sum(ServerScore.get_cpu_score(x) for x in self.server_score.values())

        # distribute nodes according to their bogomips and check if the ram size limit is still not full
        for server_id in server_score_sorted_cpu_ranking_desc:
            bogomips = ServerScore.get_cpu_score(self.server_score[server_id])
            bogomips_perc = bogomips * 1.0 / sum_bogomips

            # ceal the cnt because we have a list of servers sorted by feature CPU
            cnt_assigned_nodes = int(math.ceil(bogomips_perc * len(node_ids)))

            # decrease cnt until RAM fits
            free_memory = ServerScore.get_free_mem_score(self.server_score[server_id])
            while True:
                # assume each VM has the same amount of RAM
                assigned_memory = cnt_assigned_nodes * vm_size
                ram_limit_reached = assigned_memory > free_memory
                if not ram_limit_reached:
                    break
                # decrease nodes until the ram limit is found
                cnt_assigned_nodes -= 1

            server_node_distribution[server_id] = cnt_assigned_nodes

        return self.apply_distribution_strategy(node_ids, cnt_servers, server_node_distribution,
                                                # distribute nodes fair but begin with "best" server
                                                distribute_remaining_server_ids=server_score_sorted_cpu_ranking_desc)


if __name__ == '__main__':
    # nds = NDSEqual()
    # print nds.__class__.__name__
    # pprint(nds.distribute_emulation_nodes(range(1, 5 + 1), 2))
    # pprint(nds.distribute_emulation_nodes(range(1, 1 + 1), 64))
    # pprint(nds.distribute_emulation_nodes(range(1, 2 + 1), 64))
    # pprint(nds.distribute_emulation_nodes(range(1, 132 + 1), 64))
    # pprint(nds.distribute_emulation_nodes(range(1, 128 + 1), 64))
    from miniworld.config import Scenario

    nds = NDSScore()
    print(nds.__class__.__name__)
    Scenario.set_scenario_config(json.dumps({"qemu": {"ram": "128M"}}), raw=True)

    nds.server_score = {1: {"cpu": 1000, "free_mem": 128}, 2: {"cpu": 2000, "free_mem": 255},
                        3: {"cpu": 1050.1, "free_mem": 255}}
    pprint(nds.distribute_emulation_nodes(range(1, 6), 3))
    # nicer bigbox vs rechenschieber
    nds.server_score = {1: {"cpu": 64000, "free_mem": 256000}, 2: {"cpu": 8000, "free_mem": 32000}}
    pprint(nds.distribute_emulation_nodes(range(1, 9 + 1), 2))
