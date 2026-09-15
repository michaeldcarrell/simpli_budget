let controller = function() {
    let objs = {
        linkBtn: document.getElementById('re-auth-btn'),
        givenNameInput: document.getElementById('given-name')
    }

    let saveGivenName = function(input) {
        let value = input.value.trim();
        if (value === (input.dataset.savedValue || '')) {
            return;
        }

        let accountId = input.getAttribute('data-account-id');
        let token = getCSRFToken();
        let loader = new Loader();
        loader.show();
        fetch(`/api/accounts/${accountId}`, {
            method: 'PUT',
            headers: {
                'X-CSRFToken': token,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ given_name: value })
        }).then(async (res) => {
            return {
                status_code: res.status,
                body: await res.json()
            }
        }).then(data => {
            loader.resolve();
            if (data.status_code !== 200) {
                alert(data.body.message || 'Failed to update given name');
                input.value = input.dataset.savedValue || '';
                return;
            }
            input.dataset.savedValue = data.body.given_name || '';
            input.value = input.dataset.savedValue;
        }).catch(e => {
            loader.resolve();
            alert(e.message);
            input.value = input.dataset.savedValue || '';
            throw e;
        });
    }

    let getLinkToken = function () {
        return objs.linkBtn.getAttribute('link-token');
    };

    (async function ($) {
        try {
            console.log(getLinkToken());
            var handler = Plaid.create({
                token: getLinkToken(),
                onLoad: function () {
                },
                onSuccess: function (public_token, metadata) {
                    console.log(public_token);
                    console.log(metadata);
                    let access_token_id = parseInt(objs.linkBtn.getAttribute('access-token-id'));
                    let accessToken = new PlaidAccessToken(access_token_id);
                    accessToken.exchangePublicTokenAndStore(public_token);
                },
                onExit: function (err, metadata) {
                },
                onEvent: function (eventName, metadata) {
                }
            });

            $('#add-account').on('click', function (e) {
                handler.open();
            });
        } catch (e) { console.log(e); }
    })(jQuery);

    let plaidPopout = function(accessToken, accessTokenId){
        (async function ($) {
            try {
                console.log(accessToken);
                var handler = Plaid.create({
                    token: accessToken,
                    onLoad: function () {
                    },
                    onSuccess: function (public_token, metadata) {
                        console.log(public_token);
                        console.log(metadata);
                        let accessToken = new PlaidAccessToken(accessTokenId);
                        accessToken.exchangePublicTokenAndStore(public_token);
                    },
                    onExit: function (err, metadata) {
                    },
                    onEvent: function (eventName, metadata) {
                    }
                });

                handler.open();

                // $(this).on('click', function (e) {
                //     handler.open();
                // });
            } catch (e) { console.log(e); }
        })(jQuery);
    }

    let inits = function() {
        objs.linkBtn.addEventListener('click', function() {
           let account = new Account(
               this.getAttribute('account-id'),
               this.getAttribute('link-token')
            );
           plaidPopout(account.link_token, this.getAttribute('access-token-id'));
        });

        objs.givenNameInput.dataset.savedValue = objs.givenNameInput.value;
        objs.givenNameInput.addEventListener('keydown', function(event) {
            if (event.key === 'Enter') {
                objs.givenNameInput.blur();
            }
        });
        objs.givenNameInput.addEventListener('blur', function() {
            saveGivenName(objs.givenNameInput);
        });
    }();
}();