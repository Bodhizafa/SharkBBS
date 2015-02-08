#!/bin/bash
ROOT='http://localhost:5984';
putpage() {
    URL=${ROOT}/static/${1}
    curl -X PUT -d '{"root":"index.htm"}' ${URL}
    REV=$(curl -X GET ${URL} | jq -r '._rev')
    echo "Overwriting $REV of $URL/index.htm"
    curl -X PUT -H "Content-Type: text/html" --data-binary @${2} ${URL}/index.htm?rev=${REV}
}

putstatic() {
    URL=${ROOT}/static/${1}
    REV=$(curl -X GET ${URL} | jq -r '._rev')
    MIMETYPE=$(file --mime-type $1|cut -d' ' -f2)
    FNAME=$(basename ${2})
    echo "Overwriting ${REV} of ${URL}/${FNAME}"
    curl -X PUT -H "Content-type: $MIMETYPE" --data-binary @${2} ${URL}/${FNAME}?rev=${REV}
}

putdoc() {
    URL=${ROOT}/${1}
    curl -X PUT -H "Content-type: application/json" -d @${2} ${URL}
    REV=$(curl -X GET ${URL} | jq -r '._rev')
    curl -X PUT -H "Content-type: application/json" -d @${2} ${URL}?rev=${REV}
}

curl -X PUT ${ROOT}/static
curl -X PUT ${ROOT}/posts
putpage davenport davenport.htm
putstatic davenport prophat.jpg
putdoc posts/_design/thread thread.json

