import graphene

from miniworld import singletons
from miniworld.util import JSONConfig


class ScenarioStart(graphene.Mutation):
    class Arguments:
        scenario_config = graphene.String()

    scenario_config = graphene.JSONString()

    def mutate(self, info, scenario_config):
        scenario_config = JSONConfig.read_json_config(scenario_config, raw=True)  # type: Dict
        auto_stepping = None
        force_snapshot_boot = None
        singletons.simulation_manager.start(scenario_config, auto_stepping=auto_stepping,
                                            force_snapshot_boot=force_snapshot_boot)
        return ScenarioStart(scenario_config=scenario_config)


class ScenarioStep(graphene.Mutation):
    class Arguments:
        steps = graphene.Int()

    steps = graphene.Int()

    def mutate(self, info, steps):
        singletons.simulation_manager.step(steps)
        return ScenarioStep(steps=steps)
