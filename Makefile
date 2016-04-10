HOST=10.1.10.10:5984
USER=root
PASSWORD=berfberfberfberf
BASEURL=http://$(USER):$(PASSWORD)@$(HOST)

.PHONY: dbs bulldoze refresh documents config static

CREATE_IF_NOT_EXISTS=curl -sS -X PUT $(BASEURL)/$1|jq '(.error//"file_exists")=="file_exists"'|grep '^true$$'
DELETE_IF_EXISTS=curl -sS -X DELETE $(BASEURL)/$(1)|jq '(.error//"not_found")=="not_found"'|grep '^true$$'
UPLOAD_DOC=cat $(1) | ./upload_document.sh $(BASEURL)/$(2)
UPDATE_CONFIG=curl -f -H "Content-Type: application/json" -X PUT -d $(1) $(BASEURL)/_config/$(2) 
,=, 

refresh: static config
    
dbs: 
	$(call CREATE_IF_NOT_EXISTS,static) 
	$(call CREATE_IF_NOT_EXISTS,posts) 

config: dbs
	$(call UPDATE_CONFIG,'"true"',couch_httpd_auth/users_db_public)
	$(call UPDATE_CONFIG,'"nick$(,)title$(,)avatar$(,)signature"',couch_httpd_auth/public_fields)
	cat posts.json | ./upload_document.sh $(BASEURL)/posts/_design/posts 
	cat users.json | ./upload_document.sh $(BASEURL)/_users/_design/users 
	cat posts_sec.json | ./upload_document.sh $(BASEURL)/posts/_security 
	cat static.json | ./upload_document.sh $(BASEURL)/static/_design/static
	cat empty_sec.json | ./upload_document.sh $(BASEURL)/static/_security
	cat empty_sec.json | ./upload_document.sh $(BASEURL)/_users/_security

static: dbs
	echo "{}" | ./upload_document.sh $(BASEURL)/static/sys 
	cat root.json| ./upload_document.sh $(BASEURL)/posts/root
	./upload_attachment.sh $(BASEURL)/static/sys sharkBBS.htm text/html
	./upload_attachment.sh $(BASEURL)/static/sys prophat.jpg image/jpeg
	./upload_attachment.sh $(BASEURL)/static/sys d3.js application/javascript

bulldoze:
	$(call DELETE_IF_EXISTS,static)
	$(call DELETE_IF_EXISTS,posts)
	rm curl.log
