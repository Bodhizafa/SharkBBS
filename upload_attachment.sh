#!/bin/bash
# Real databases can insrep, couchdb sucks, so it has this boilerplate.
# $1 = full URL of document to attach to
# $2 = local filename
# $3 = MIME type

ERROR=$(curl -s -X PUT -H "Content-type: $3" --data-binary @$2 $1/$(basename $2)|jq .error|sed 's/\s+$//')

if [ $ERROR = 'null' ]; then
    exit 0;
elif [ $ERROR = '"conflict"' ]; then
    REV=$(curl -s -X GET $1|jq -r ._rev|sed 's/\s+$//')
    ERROR=$(curl -s -X PUT -H "Content-type: $3" --data-binary @$2 $1/$(basename $2)?rev=${REV}|jq -r ._rev|sed 's/\s+$//')
    if [ $ERROR = 'null' ]; then
        exit 0;
    fi
fi
echo "Attachment upload failed: $ERROR";
exit 1;
