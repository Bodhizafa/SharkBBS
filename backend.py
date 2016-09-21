#!/bin/env python3
# vim: set fileencoding:utf-8

"""
Copyright Landon Meernik

==The Backend
I hate writing backends, but it turns out I hate learning other people's even more.
By that I mean holy shit couchdb is a steaming pile of bedbug ridden, semen stained,
cat piss smelling, mold infested, springs-showing, damp garbage from under a bridge.
Because of this, I am forced to write this thing. In theory it's pretty damn general
and I hope I won't have to to it again.

This file is hate shrine to it, because I tried desparately to use it for this, and
it sucked too damn hard.
"""

"""
Maps paths and parameters from HTTP requests to SQL queries, runs them, and
spits out structured data (currently CSV or JSON). Designed for use as a
backend for web-based visualization tools.

==Request Format

<server>:3103/path part 1>/<path part 2>/<path part 3r?param1=p1val&param2=p2val

would be split into .
path: path in json_namespace[database] (described below)
params: {param1: p1val, param2: p2val} - dict of GET.

the first --skip elements in path are ignored, this is because nginx passes the full
proxy_path through and we don't want to ave to include that in our namespace, so by
default /FUCKYOU/posts/ will be treated as /posts/ because --skip defaults to 1

The value associated with said key is the namespace navigated
by path. Each path element refers to stepping down to the 'children' node,
so for example:

request
    /data/posts?thread_id=341
would execute
    ns['children']['posts'] % {thread_id: 341}
which parameter key is which ? is defined by the order of the 'params' field.

and return the results as a list of colname:val JSON maps.

==Namespace definition/navigation

A namespace is a tree of nodes, each of which is be one of the following:

A node with one query and no parameters:
(returns the results of query)
{
    "query": "<some SQL query>"
}

A node with parameters:
(substitutes the GET parameters specified by 'params' into 'query', then executes)
{
    "query": "<some %s SQL query %s>"
    "params" : ['param1_name', 'param2_name']
}

A list of nodes with different parameters:
(Chooses the node that matches the provided parameters. All variants must
    return results with the same colum set and no two variants should have the
    same param set)
[
    {
        "query": "<some SQL query>"
    }, {
        "query": "<some SQL query WHERE col1='%s'",
        "params": ["col1_filter"]
    }, {
        "query": "<some SQL query WHERE col1='%s' AND col2='%s'",
        "params": ["col1_filter", "col2_filter"]
    }
]

A node with children:
(effectively a directory, usually children will be various subsets of the
    unfiltered query, or query is absent)
{
    "query": "<some SQL query>" # if omitted, this node will reutrn emptyset.
    "children": {
        "filter1": <namepace node>,
        "filter2": <namespace node>
    }
}

Pattern matched list nodes cannot have children.
"""

import http.server
import urllib.parse
import argparse
import json
import sqlite3
from collections import Counter

parser = argparse.ArgumentParser("Shark Backend. Bites users occasionally")

parser.add_argument("--ns", type=argparse.FileType('r'), help="JSON namespace file")
parser.add_argument("--initsql", type=argparse.FileType('r'), help="SQL file to execute upon startup")
parser.add_argument("--db", type=str, help="sqlite db file")
parser.add_argument("--port", type=int, help="port to listen on", default=3103)
parser.add_argument("--skip", type=int, help="ignore this many non-empty path elements (for when you have this nested under some nginx proxy)", default=1)

class NotFoundError(LookupError):
    pass

class BadParamsError(LookupError):
    pass

class Encoder(json.JSONEncoder):
    # a JSON encoder that serializes datetimes as ISO8601 strings, which JS
    # parses nicely.
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        else:
            return json.JSONEncoder.default(self, obj)

class RequestHandler(http.server.BaseHTTPRequestHandler):
    def respond(self, obj, code=200):
        self.send_response(code)
        self.send_header('Content-Type', "application/json")
        self.end_headers()
        s = json.dumps(obj, indent=2, ensure_ascii=True, cls=Encoder)
        self.wfile.write(s.encode('ascii'))

    def do_GET(self):
        res = urllib.parse.urlparse(self.path)
        params = { # urlparse passes EVERYTHING back as a list, this extracts singletons.
            key : val[0] if len(val) == 1 else val
            for key, val in urllib.parse.parse_qs(res.query).items()
        }
        path = [pe for pe in res.path.split("/") if pe][self.server.skip:];
        if not path:
            self.respond(self.server.ns)
            return
        try:
            query, porder = self.server.get_query(path, params)
            dc = self.server.dbconn.cursor()
            if porder is not None:
                dc.execute(query, [params[k] for k in porder])
            else:
                dc.execute(query)
            names = [name for name, _, _, _, _, _, _ in dc.description]
            res = [dict(zip(names, vals)) for vals in dc.fetchall()]
            self.respond(res)
        except sqlite3.OperationalError as e:
            self.respond({"error": str(type(e)), "value": str(e)}, 500)
        except NotFoundError as e:
            self.respond({"error": str(type(e)), "value": str(e)}, 404)

    def do_POST(self):
        print("got a POST request")
        self.respond({"error": str(NotImplementedError), "value": "Not Implemented"}, 501)

    def do_PUT(self):
        print("got a PUT request")
        self.respond({"error": str(NotImplementedError), "value": "Not Implemented"}, 501)

    def do_DELETE(self):
        print("got a DELETE request")
        self.respond({"error": str(NotImplementedError), "value": "Not Implemented"}, 501)

class Server(http.server.HTTPServer):
    def __init__(self, port, ns, db, initsql, skip):
        self.dbconn = sqlite3.connect(db)
        self.ns = json.load(ns)
        self.skip = skip
        if initsql:
            dc = self.dbconn.cursor()
            dc.executescript(initsql.read())
            dc.close()
        super().__init__(('', port), RequestHandler)

    def get_query(self, path, params):
        """
        Return the query asked for by path that matches the given param names
        """
        if not path:
            raise NotFoundError("No path specified")
        if not params:
            params = {}
        cur = self.ns
        try: # actually traverse the namespace finding the node we're looking for
            for pe in path:
                cur = cur['children'][pe]
        except KeyError as e:
            raise NotFoundError("Couldn't find %s in JSON namespace: %s: cur: %r" % (str(path), str(e), cur));
        params_present_counter = Counter(params.keys());
        def try_query (qmap):
            if Counter(qmap['params']) != params_present_counter:
                raise BadParamsError("Parameters %r do not match query params: %r" % (params, qmap))
            if 'params' in qmap and qmap['params']:
                return qmap['query'], qmap['params']
            else:
                return qmap['query'], None

        if 'query' in cur:
            return try_query(cur)
        else:
            # is a list, find matching query
            for qmap in cur:
                try:
                    if 'params' not in qmap:
                        qmap['params'] = []
                    return try_query(qmap)
                except BadParamsError:
                    pass
            raise BadParamsError("Cannot find query for params: %r in path %s" % (params, path))
def main(**args):
    s = Server(**args)
    print("calling serve_forever")
    s.serve_forever()

if __name__ == "__main__":
    args = parser.parse_args()
    main(**vars(args))
