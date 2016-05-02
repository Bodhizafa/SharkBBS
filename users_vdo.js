function (newDoc, oldDoc, userCtx, secObj) {
    ['nick', 'avatar', 'signature'].forEach(function(field) {
        if (newDoc[field] === undefined) {
            throw {forbidden: 'Field is undefined: ' + field};
        } else if (newDoc[field] === null) {
            throw {forbidden: 'Field is null: ' + field};
        }
    });
    if (newDoc.passcode != 'smoke the better pole') {
        throw {forbidden: 'Incorrect secret passcode'};
    }
    return true;
}
