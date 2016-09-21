function (doc, req) {
    var now = new Date().toISOString(),
        newDoc = JSON.parse(req.body);
    if (!doc) {
        if (req.id !== undefined) {
            newDoc._id = req.id;
        } else {
            newDoc._id = req.uuid;
        }
        newDoc.created = now;
        newDoc.lasted = now;
        return [newDoc, ''];
    } else {
        log('EDIT THE DOCUMENTSIN G');
        log(newDoc);
        log(req);
        if (req.id && doc._id && req.id !== doc._id) {
            throw {conflict: 'Contradictory request'};
        }
        doc._id = doc._id || req.id || req.uuid;
        if (doc._rev !== newDoc._rev) {
            throw {conflict: 'MVCCCCCC conflict' + doc._rev + ' vs ' + newDoc._rev};
        }
        Object.keys(newDoc).forEach(function(k) {
            log('THING MUTATED');
            log(k);
            if (k !== 'created') { 
                doc[k] = newDoc[k];
            }
        });
        doc.lasted = now;
        log(doc);
        return [doc, ''];
    }
}
