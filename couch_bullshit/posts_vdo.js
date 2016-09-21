function (newDoc, oldDoc, userCtx, secObj) {
    var required_keys = ['owner', 'renderer', 'content', 'lasted', 'created', 'subject', 'threadid', 'signature'];
    log('UPDATE VALIDATIN');
    log('userCtx');
    log(userCtx);
    log('secObj');
    log(secObj);
    log('Documents');
    log(oldDoc);
    log('->');
    log(newDoc);
    if (newDoc.threadid === 'PRISMO') {
        throw 'Hey. What the fuck are you doing here?';
    }
    if (oldDoc !== null) {
        if (oldDoc.owner !== userCtx.name) {
            var admin = false;
            userCtx.roles.forEach(function(role) { if (role === 'admin') admin = true; });
            if (admin) {
                log('Administrator ' + userCtx.name + ' modifying post owned by ' + oldDoc.owner);
            } else {
                log(userCtx.name + ' with roles ' + userCtx.roles + ' cannot modify post owned by ' + oldDoc.owner);
                throw {forbidden: 'Attempted to change unowned post'};
            }
        }
    }
    if (!newDoc._deleted) {
        if (oldDoc != null && newDoc.created !== oldDoc.created) {
            throw {forbidden: 'Attempted to change post created'};
        }
        if (!newDoc.owner) {
            throw {forbidden: 'Must have an owner'};
        }
        if (isNaN(Date.parse(newDoc.created))) {
            throw {forbidden: 'Created date is not a date'};
        }
        if (isNaN(Date.parse(newDoc.lasted))) {
            throw {forbidden: 'Last edited is not a date'};
        }
        required_keys.forEach(function(key) {
            if (!key in newDoc) {
                throw {forbidden: 'Missing ' + key};
            }
        });
    }
    return true;
}
