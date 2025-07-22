let controller = function() {
    let objs = {
        linkBtn: document.getElementById('re-auth-btn')
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
    }();
}();