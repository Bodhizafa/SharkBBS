function (newDoc, oldDoc, userCtx, secObj) {
    log('USERS UPDATE VALIDATING');
    log(oldDoc);
    log('->');
    log(newDoc);
    ['nick', 'avatar', 'signature'].forEach(function(field) {
        if (newDoc[field] === undefined) {
            throw {forbidden: 'Field is undefined: ' + field};
        } else if (newDoc[field] === null) {
            throw {forbidden: 'Field is null: ' + field};
        }
    });
    return true;
}
