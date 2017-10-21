import graphene
from flask import Flask
from flask_graphql import GraphQLView
from graphene import ObjectType, String

import miniworld
from miniworld.api.node import NodeQuery
from miniworld.api.scenario import ScenarioStart, ScenarioStep


class PingQuery(ObjectType):
    ping = String()

    def resolve_ping(self, args):
        return 'Pong'


class Mutations(graphene.ObjectType):
    scenario_start = ScenarioStart.Field()
    scenario_step = ScenarioStep.Field()


class Query(PingQuery, NodeQuery):
    pass


schema = graphene.Schema(query=Query, mutation=Mutations)

app = Flask(__name__)
app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))

if __name__ == '__main__':
    # TODO: read from CLI
    config_path = None
    miniworld.init(config_path=config_path, do_init_singletons=True)
    app.run(host="0.0.0.0")
