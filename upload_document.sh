#!/bin/bash
# More boilerplate to make interacting with couchdb suck a _little_ less.
# $1 URL to upload to, document contents should be provided via stdin
TEMPFILE=$(mktemp)
cat > $TEMPFILE
echo "Uploading $1" >> curl.log
ERROR=$(curl -s -X PUT -H "Content-type: application/json" -d @${TEMPFILE} $1|tee -a curl.log|jq .error|sed 's/\s+$//')
if [ $ERROR = 'null' ]; then
    exit 0;
elif [ $ERROR = '"conflict"' ]; then
    REV=$(curl -s -X GET $1|jq -r ._rev|sed 's/\s+$//');
    ERROR=$(curl -s -X PUT -H "Content-type: application/json" -d @${TEMPFILE} $1?rev=${REV}|tee -a curl.log|jq .error |sed 's/\s+$//');
    if [ $ERROR = 'null' ]; then
        exit 0;
    fi
fi
echo "Doc upload failed: $ERROR .";
exit 1;

