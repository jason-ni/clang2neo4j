from neo4j.v1 import GraphDatabase
from neo4j.v1 import basic_auth


class Neo4jClangHelper(object):

    def __init__(self, user_name, password, host='127.0.0.1', port=7687):
        super(Neo4jClangHelper, self).__init__()
        self._driver = GraphDatabase.driver(
            "bolt://{host}:{port}".format(host=host, port=port),
            auth=basic_auth(user_name, password)
        )
        self._session = self._driver.session()

    def close(self):
        self._session.close()

    def create_unique(self, node_lable, field_name):
        self._session.run("CREATE CONSTRAINT ON (p:{label})"
                          "ASSERT p.{field} IS UNIQUE".format(
                              label=node_lable,
                              field=field_name
                          ))

    def create_node(self, node):
        display_name = node['kind']
        if node['spelling']:
            display_name = node['spelling']
        node['display_name'] = display_name
        res = self._session.run("MATCH (node:ASTNode)"
                                "WHERE node.node_id={id}"
                                "RETURN node", node)
        if len(list(res)) == 0:
            self._session.run("CREATE (node:ASTNode "
                              "{name: {display_name}, "
                              "node_id: {id},"
                              "kind: {kind},"
                              "usr: {usr}, spelling: {spelling},"
                              "location: {location}, "
                              "extent_start: {extent_start},"
                              "extent_end: {extent_end},"
                              "is_definition: {is_definition}"
                              "})", node)
            return True
        else:
            return False

    def create_relationship(self, id_1, id_2, rname):
        self._session.run(
            "MATCH (node_1:ASTNode) where node_1.node_id = \"{id_1}\" "
            "MATCH (node_2:ASTNode) where node_2.node_id = \"{id_2}\" "
            "CREATE (node_1)-[r:{rname}]->(node_2)".format(
                id_1=id_1,
                id_2=id_2,
                rname=rname)
        )


def main():
    helper = Neo4jClangHelper('neo4j', 'passw0rd')
    helper.create_unique('ASTNode', 'node_id')
    helper.create_node({
        'id': 1,
        'kind': "AAAA",
        'spelling': '',
        'usr': 'usr',
        'location': 'location',
        'extent_start': 100,
        'extent_end': 200,
        'is_definition': 'yes'
    })
    helper.create_node({
        'id': 2,
        'kind': "BBBB",
        'spelling': '',
        'usr': 'usr',
        'location': 'location',
        'extent_start': 100,
        'extent_end': 200,
        'is_definition': 'yes'
    })
    helper.create_relationship(1, 2, 'Has')
    helper.create_node({
        'id': 2,
        'kind': "BBBB",
        'spelling': '',
        'usr': 'usr',
        'location': 'location',
        'extent_start': 100,
        'extent_end': 200,
        'is_definition': 'yes'
    })
    helper.close()


if __name__ == '__main__':
    main()
