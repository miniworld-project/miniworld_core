import argparse
import os

import graphene
from flask import Flask
from flask_graphql import GraphQLView
from graphene import ObjectType, String

import miniworld
from miniworld.api.impairmentmodel import ImpairmentQuery
from miniworld.api.node import NodeQuery, NodeExecuteCommand
from miniworld.api.connection import ConnectionQuery
from miniworld.api.scenario import ScenarioStart, ScenarioStep, ScenarioAbort


class PingQuery(ObjectType):
    ping = String()

    def resolve_ping(self, args):
        return 'pong'


class Mutations(graphene.ObjectType):
    scenario_start = ScenarioStart.Field()
    scenario_step = ScenarioStep.Field()
    scenario_abort = ScenarioAbort.Field()
    node_execute_command = NodeExecuteCommand.Field()


class Query(PingQuery, NodeQuery, ConnectionQuery, ImpairmentQuery):
    node = graphene.relay.Node.Field()


schema = graphene.Schema(query=Query, mutation=Mutations)
app = Flask(__name__)
app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))


def main():
    root_parser = argparse.ArgumentParser(description='MiniWorld network emulator')
    root_parser.add_argument('-c', '--config', default=os.environ.get('MW_CONFIG'), help="The config file")
    args = root_parser.parse_args()
    config_path = os.path.abspath(args.config) if args.config is not None else None
    miniworld.init(config_path=config_path, do_init_singletons=True)
    app.run(host="0.0.0.0")


if __name__ == '__main__':
    main()
