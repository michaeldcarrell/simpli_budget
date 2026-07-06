let controller = function() {
    let objs = {
        addAccountBtn: document.getElementById('add-account-btn'),
    };

    let exchangePublicToken = function(publicToken, institutionId) {
        let token = getCSRFToken();
        let loader = new Loader();
        loader.show();
        fetch('/api/accounts/new', {
            method: 'POST',
            headers: {
                'X-CSRFToken': token,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                public_token: publicToken,
                institution_id: institutionId,
            })
        }).then(async response => {
            return {
                status_code: response.status,
                body: await response.json(),
            };
        }).then(data => {
            if (data.status_code !== 200) {
                alert(`Add Account Failed: \nStatus Code: ${data.status_code}\nBody: ${JSON.stringify(data.body)}`);
                console.log(data);
                loader.resolve();
                return;
            }
            window.location.reload();
        }).catch(e => {
            loader.resolve();
            alert(`Add Account Failed: ${e.message}`);
            throw e;
        });
    };

    let inits = function() {
        if (!objs.addAccountBtn || objs.addAccountBtn.disabled) {
            return;
        }

        let handler = Plaid.create({
            token: objs.addAccountBtn.getAttribute('link-token'),
            onLoad: function() {},
            onSuccess: function(publicToken, metadata) {
                let institutionId = metadata.institution ? metadata.institution.institution_id : null;
                exchangePublicToken(publicToken, institutionId);
            },
            onExit: function(err, metadata) {},
            onEvent: function(eventName, metadata) {},
        });

        objs.addAccountBtn.addEventListener('click', function() {
            handler.open();
        });
    }();
}();
