#!/usr/bin/env python

"""
A simple command line tool for dumping a source file using the Clang Index
Library.
"""


opts = None


def get_diag_info(diag):
    return {'severity': diag.severity,
            'location': diag.location,
            'spelling': diag.spelling,
            'ranges': diag.ranges,
            'fixits': diag.fixits}

id_dict = {}


def get_cursor_id(cursor, location_str):
    global id_dict
    if cursor is None:
        return None
    cursor_id = "%s|%s|%d|%d|%d|%d" % (location_str,
                                       cursor.kind,
                                       cursor.extent.start.line,
                                       cursor.extent.start.column,
                                       cursor.extent.end.line,
                                       cursor.extent.end.column
                                       )
    return cursor_id


def get_info(neo4j_helper, node, parent=None, depth=0):
    # if opts.maxDepth is not None and depth >= opts.maxDepth:
    #    children = None
    location_str = None
    if str(node.kind) == "CursorKind.TRANSLATION_UNIT":
        location_str = node.spelling
    else:
        try:
            location_str = str(node.location.file.name)
        except AttributeError:
            print node.kind, node.location, node.extent
            print node.spelling
            print list(node.get_tokens())
            location_str = node.hash
    node_dict = {'id': get_cursor_id(node, location_str),
                 'kind': str(node.kind),
                 'usr': str(node.get_usr()),
                 'spelling': node.spelling,
                 'location': location_str,
                 'extent_start': str(node.extent.start),
                 'extent_end': str(node.extent.end),
                 'is_definition': node.is_definition(),
                 'definition_id': str(node.get_definition())}
    if neo4j_helper.create_node(node_dict):
        [get_info(neo4j_helper, c, parent=node_dict)
            for c in node.get_children()]
    if parent is not None:
        neo4j_helper.create_relationship(
            parent['id'], node_dict['id'], 'Has')


def main():
    from neo4j_helper import Neo4jClangHelper

    from clang.cindex import Index
    from pprint import pprint

    from optparse import OptionParser

    global opts

    parser = OptionParser("usage: %prog [options] {filename} [clang-args*]")
    parser.add_option("", "--show-ids", dest="showIDs",
                      help="Compute cursor IDs (very slow)",
                      action="store_true", default=False)
    parser.add_option("", "--max-depth", dest="maxDepth",
                      help="Limit cursor expansion to depth N",
                      metavar="N", type=int, default=None)
    parser.add_option("", "--filter", dest="fnameFilter",
                      help="file name filter for nodes.")
    parser.add_option("", "--neo4j-port", dest="neo4jPort",
                      help="Neo4j bolt service port", type=int, default=7687)
    parser.add_option("", "--neo4j-host", dest="neo4jHost",
                      help="Neo4j bolt service host", default="127.0.0.1")
    parser.add_option("", "--neo4j-user", dest="neo4jUser",
                      help="Neo4j auth user name.")
    parser.add_option("", "--neo4j-pass", dest="neo4jPass",
                      help="Neo4j auth password.")
    parser.disable_interspersed_args()
    (opts, args) = parser.parse_args()

    if len(args) == 0:
        parser.error('invalid number arguments')

    index = Index.create()

    tu = index.parse(None, args)
    if not tu:
        parser.error("unable to load input")

    helper = Neo4jClangHelper('neo4j', 'passw0rd')
    helper.create_unique('ASTNode', 'node_id')
    pprint(('diags', map(get_diag_info, tu.diagnostics)))
    get_info(helper, tu.cursor)
    helper.close()

if __name__ == '__main__':
    main()
