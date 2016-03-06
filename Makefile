HOST=localhost:5984
USER=root
PASSWORD=berfberfberfberf
BASEURL=http://$(USER):$(PASSWORD)@$(HOST)

.PHONY: dbs bulldoze static_content refresh

CREATE_IF_NOT_EXISTS=curl -sS -X PUT $(BASEURL)/$1|jq '(.error//"file_exists")=="file_exists"'|grep '^true$$'
DELETE_IF_EXISTS=curl -sS -X DELETE $(BASEURL)/$(1)|jq '(.error//"not_found")=="not_found"'|grep '^true$$'

refresh: static_content
    
dbs: 
	$(call CREATE_IF_NOT_EXISTS,static) 
	$(call CREATE_IF_NOT_EXISTS,posts) 
    

assets: dbs
	echo "{}" | ./upload_document.sh $(BASEURL)/static/sys 
	./upload_attachment.sh $(BASEURL)/static/sys prophat.jpg image/jpeg
	./upload_attachment.sh $(BASEURL)/static/sys sharkBBS.htm text/html
	./upload_attachment.sh $(BASEURL)/static/sys d3.js application/javascript

bulldoze:
	$(call DELETE_IF_EXISTS,static)
	$(call DELETE_IF_EXISTS,posts)
