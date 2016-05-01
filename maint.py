import argparse
import http.client 
import base64
import traceback
import json
import pprint

gargs = None
parser = argparse.ArgumentParser()
parser.add_argument("--user", type=str, default="root")
parser.add_argument("--passwd", type=str, default="berfberfberfberf")
parser.add_argument("--host", type=str, help="Host to connect to",
                    default="localhost:5984")

documents_by_url = {
    '/posts/_design/posts': 'posts.json',
	'/_users/_design/users': 'users.json',
	'/static/_design/static': 'static.json',
    '/static/sys': 'empty_doc.json',
}
# If couchdb presented _rev for security docs, this wouldn't be necessary
secdocs_by_db  = { 
    'static': 'empty_sec.json',
    '_users': 'empty_sec.json',
    'posts': 'posts_sec.json',
}
sys_attachments = [
    'sharkBBS.htm',
    'prophat.jpg',
    'd3.js',
]
config_by_name = {
	'couch_httpd_auth/users_db_public': 'true',
	'couch_httpd_auth/public_fields': 'nick,title,avatar,signature', # Why isn't this a JSON array?
}

def req_with_auth(url):
    conn = http.client.HTTPConnection(gargs.host)
    headers = {'Authorization': 'Basic %s' % base64.b64encode(bytes("%s:%s" % (gargs.user, gargs.passwd), 'ascii')).decode('ascii')}
    req = conn.request("GET", url, headers=headers)
    resp = conn.getresponse()
    ct = resp.getheader('Content-Type')
    cts = ct.split(';')
    ctmap = {ctparam[0]: ctparam[1] if len(ctparam) > 1 else None for ctparam in [ct.split('=') for ct in cts]}
    charset = ctmap['charset'] if 'charset' in ctmap else 'ascii'
    return json.loads(str(resp.read(), charset))

if __name__ == '__main__':
    try:
        gargs = parser.parse_args()
        print("SharkBBS maintainence script attempt 3, codename 'I still hate couchdb'")
        print("Aguments: %r" % gargs)
        for url, doc_filename in documents_by_url.items():
            doc = req_with_auth(url)
            try:
                print("Requested %s, got %s" % (url, req_with_auth(url)['_rev']))
            except KeyError:
                print('No rev for %s' % url)
                pprint.pprint(doc)
    except:
        traceback.print_exc()
    finally:
        print('Done.')
        input()
