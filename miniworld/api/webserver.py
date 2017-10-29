import graphene
from flask import Flask
from flask_graphql import GraphQLView
from graphene import ObjectType, String

import miniworld
from miniworld.api.impairmentmodel import ImpairmentQuery
from miniworld.api.impairments import ImpairmentsQuery
from miniworld.api.mobility import DistancesQuery
from miniworld.api.node import NodeQuery
from miniworld.api.scenario import ScenarioStart, ScenarioStep, ScenarioAbort


class PingQuery(ObjectType):
    ping = String()

    def resolve_ping(self, args):
        return 'pong'


class Mutations(graphene.ObjectType):
    scenario_start = ScenarioStart.Field()
    scenario_step = ScenarioStep.Field()
    scenario_abort = ScenarioAbort.Field()


class Query(PingQuery, ImpairmentsQuery, NodeQuery, DistancesQuery, ImpairmentQuery):
    pass


schema = graphene.Schema(query=Query, mutation=Mutations)

app = Flask(__name__)
app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))


def main():
    # TODO: read from CLI
    config_path = None
    miniworld.init(config_path=config_path, do_init_singletons=True)
    app.run(host="0.0.0.0")


if __name__ == '__main__':
    main()
