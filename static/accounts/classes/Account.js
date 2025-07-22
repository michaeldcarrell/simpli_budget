class Account {
    constructor(account_id, link_token=null) {
        this.account_id = account_id;
        this.link_token = link_token;
    }

    getLinkToken() {
        let djangoToken = getCSRFToken();
        let loader = new Loader();
        loader.show();
        fetch(`/api/accounts/${this.account_id}/link_token`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': djangoToken,
                'Content-Type': 'application/json'
            }
        }).then(async (res) => {
            return {
                status_code: res.status,
                body: await res.json()
            }
        }).then(data => {
            if (data.status_code !== 200) {
                alert(`Failed to get Link Token: \nStatus Code: ${data.status_code}\nBody: ${data.body}`)
                console.log(data);
            }
            this.link_token = data.body.link_token.token;
            console.log(data.body);
            console.log('Link Token', this.link_token);
            loader.resolve();
        }).catch(e => {
            loader.resolve();
            alert(`Link Token Collection Failed: ${e.message}`)
            throw e;
        });
    }
}