
# TODO: DOC
class ConnectionDetails(object):

    def __init__(self, connection, link_quality):
        self.connection = connection
        self.link_quality = link_quality

    def update_link_quality(self, link_quality):
        self.link_quality = link_quality