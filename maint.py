#!/usr/bin/env python3
import argparse
import http.client
import base64
import traceback
import json
import pprint
import mimetypes

gargs = None
parser = argparse.ArgumentParser()
parser.add_argument('--passwd', type=str, default='berfberfberfberf')
parser.add_argument('--host', type=str, help='Host to connect to',
                    default='localhost:5984')
parser.add_argument('--initialize', action='store_true', help='Create databases and try to set root password')

class Script(object):
    def __init__(self, filename):
        self.filename = filename

def expand_scripts(doc):
    if isinstance(doc, Script):
        return open(doc.filename).read()
    if isinstance(doc, dict):
        return {k: expand_scripts(v) for k, v in doc.items()}
    else:
        return doc

root_user = {
    'name': 'root',
    'nick': 'root',
    'avatar': '/static/sys/prophat.jpg',
    'type': 'user',
    'password': None,
    'roles': [ 'admin' ],
    'signature': 'When one has much to put into them, a day has a hundred pockets\n- Nietzsche ',
}
root_post = {
   'owner': 'root',
   'subject': 'Beans',
   'content': 'Beans',
   'created': '2016-04-20T04:20:00.000Z',
   'lasted': '2016-04-20T04:20:00.000Z'
}

documents_by_url = expand_scripts({
    '/posts/_design/posts': {
        'language': 'javascript',
        'validate_doc_update': Script('posts_vdo.js'),
        'updates': {
            'post': Script('posts_updates.js')
        },
        'views': {
            'thread': {
                'map': 'function(doc) { emit(doc.threadid, null); }'
            }
        }
    },
	'/_users/_design/users': {
        'language': 'javascript',
        'validate_doc_update': Script('users_vdo.js'),
    },
	'/static/_design/static': {
        'language': 'javascript',
        'validate_doc_update': "function (newDoc, oldDoc, userCtx, secObj) { if (userCtx.name == 'root') return true; else throw {forbidden:'nope'}}"
    },
    '/static/sys': {},
})

# If couchdb presented _rev for security docs, this wouldn't be a special case
secdocs_by_db  = {
    'static': {
        '_id': '_security',
        'members': {
            'names': [ ],
            'roles': [ ]
        },
        'admins': {
            'names': [ ],
            'roles': [ ]
        }
    },
    '_users': {
        '_id': '_security',
        'members': {
            'names': [ ],
            'roles': [ ]
        },
        'admins': {
            'names': [ ],
            'roles': [ ]
        }
    },
    'posts': {
        '_id': '_security',
        'members': {
            'names': [ ],
            'roles': [ ]
        },
        'admins': {
            'names': [ ],
            'roles': [ 'admin' ]
        }
    },
}
sys_attachments = [
    'sharkBBS.htm',
    'prophat.jpg',
    'd3.js',
]
config_by_name = {
	'couch_httpd_auth/users_db_public': '"true"',
	'couch_httpd_auth/public_fields': '"nick, title, avatar, signature"',
    'couch_httpd_auth/allow_persistent_cookies': '"true"',
    'couch_httpd_auth/timeout': '"86400"',
}

class CouchException(http.client.HTTPException): # Bitch, I am not fucking relaxed!
    def __init__(self, url, doc):
        if 'reason' in doc:
            super().__init__('%s(%s): %s' % (doc['error'], doc['reason'], url))
        else:
            super().__init__('%s: %s' % (doc['error'], url))
class NotFound(CouchException):
    pass
class Conflict(CouchException):
    pass
class Forbidden(CouchException):
    pass
class Unauthorized(CouchException):
    pass
class OutOfBandModification(Exception):
    pass
exctypes_by_status = {
    401: Unauthorized,
    404: NotFound,
    409: Conflict,
    403: Forbidden,
}

def req(method, url, body=None, headers=None):
    if headers is None:
        headers = {}
    conn = http.client.HTTPConnection(gargs.host)
    req = conn.request(method, url, body=body, headers=headers)
    resp = conn.getresponse()
    ct = resp.getheader('Content-Type')
    cts = ct.split(';')
    ctmap = {ctparam[0].strip(): ctparam[1].strip() if len(ctparam) > 1 else None for ctparam in [ct.split('=') for ct in cts]}
    charset = ctmap['charset'] if 'charset' in ctmap else 'ascii'
    doc = json.loads(str(resp.read(), charset))
    if resp.status // 100 != 2:
        raise exctypes_by_status[resp.status](url, doc)
    return doc

def req_with_auth(method, url, body=None, headers=None):
    if headers is None:
        headers = {}
    headers['Authorization'] = 'Basic %s' % base64.b64encode(bytes('%s:%s' % ('root', gargs.passwd), 'ascii')).decode('ascii')
    return req(method, url, body, headers)

def put_doc(url, doc): # doc should be a dict
    resp = req_with_auth('PUT', url, json.dumps(doc), {'Content-Type': 'application/json'})
    assert resp['ok'], 'Response was not ok: %s' % pprint.pformat(resp)

def doc_needs_update(old_doc, doc):
    modified_keys = set(old_doc.keys()) - set(doc.keys()) - {'_rev', '_id', '_attachments'}
    # If a doc has gained keys, it's probably been modified out of band and we don't want to muck with it
    if modified_keys:
        raise OutOfBandModification('Document %s has modified keys %s' % (url, modified_keys))
    modified = False
    for k in doc.keys():
        if k in old_doc and old_doc[k] != doc[k]:
            modified = True
    return modified

if __name__ == '__main__':
    try:
        gargs = parser.parse_args()
        print('SharkBBS maintainence script attempt 3, codename \'I still hate couchdb\'')
        print('Aguments: %r' % gargs)
        if gargs.initialize:
            root_user_url = '/_users/org.couchdb.user:root'
            conn = http.client.HTTPConnection(gargs.host)
            doc = req('PUT', '/_config/admins/root', body='"%s"' % gargs.passwd)
            print('Created admin.')
            try:
                old_doc = req_with_auth('GET', root_user_url)
                raise OutOfBandModification('Root user already exists: %r' % old_doc)
            except NotFound:
                root_user['password'] = gargs.passwd
                put_doc(root_user_url, root_user)
                put_doc(root_post_url, root_post)
                print('Created root user.')
            req_with_auth('PUT', "/static")
            req_with_auth('PUT', "/posts")

        for url, doc in documents_by_url.items():
            try:
                old_doc = req_with_auth('GET', url)
                if doc_needs_update(old_doc, doc):
                    doc['_rev'] = old_doc['_rev']
                    print('Updating %s' % url)
                    put_doc(url, doc)
                else:
                    print('Unmodified: %s' % url)
            except NotFound: # we don't need to add _rev if the doc doesn't exist yet
                print('Creating %s' % url)
                put_doc(url, doc)
        for db, doc in secdocs_by_db.items():
            try:
                url = '/%s/_security' % db
                old_doc = req_with_auth('GET', url)
                if doc_needs_update(old_doc, doc):
                    put_doc(url, doc)
                    print('Updating %s' % url)
                else:
                    print('Unmodified: %s' % url)
            except NotFound:
                put_doc(url, doc)
        sys_rev = req_with_auth('GET', '/static/sys')['_rev']
        for filename in sys_attachments:
            mimetype, encoding = mimetypes.guess_type(filename)
            if mimetype is None:
                raise TypeError('Could not determine mime type of %s' % filename)
            doc = req_with_auth('PUT', '/static/sys/%s?rev=%s' % (filename, sys_rev), body=open(filename, 'rb').read(), headers={'Content-Type': mimetype})
            print('Uploaded attachment %s got %s' % (filename, doc))
            sys_rev = doc['rev']
        for key, value in config_by_name.items():
            doc = req_with_auth('PUT', '/_config/%s' % key, body=value, headers={'Content-Type': 'application/json'})
            print('Set config %s from %s to %s' % (key, doc, value))
    except:
        traceback.print_exc()
    finally:
        print('Done.')
        #input()
