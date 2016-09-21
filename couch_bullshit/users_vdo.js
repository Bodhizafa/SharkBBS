function (newDoc, oldDoc, userCtx, secObj) {
    ['nick', 'avatar', 'signature'].forEach(function(field) {
        if (newDoc[field] === undefined) {
            throw {forbidden: 'Field is undefined: ' + field};
        } else if (newDoc[field] === null) {
            throw {forbidden: 'Field is null: ' + field};
        }
    });
    if (!userCtx.name) {
        if (oldDoc) {
            throw {forbidden: 'Who are you? What are you doing'};
        }
        if (newDoc.passcode != 'everyone has a plumbus in their home') {
            throw {forbidden: 'Incorrect secret passcode'};
        } else {
            log('Registered new user: ' + newDoc.name);
            return true;
        }
    }
    if (userCtx.name != oldDoc.name) {
        throw {forbidden: 'Cannot modify ' + oldDoc.name + ' as ' + userCtx.name};
    }
    if (userCtx.name != newDoc.name) {
        throw {forbidden: 'Cannot modify your name from ' + userCtx.name + ' to ' + newDoc.name};
    }
    return true;
}
