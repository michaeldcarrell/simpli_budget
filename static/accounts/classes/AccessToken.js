class PlaidAccessToken {
    constructor(accessTokenId) {
        this.accessTokenId = accessTokenId;
    }

    exchangePublicTokenAndStore(publicToken, institutionId=null) {
        let token = getCSRFToken();
        let loader = new Loader();
        fetch(`/api/access_token/${this.accessTokenId}`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': token,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                public_token: publicToken,
                institution_id: institutionId
            })
        }).then(async response => {
            return {
                status_code: response.status,
                body: await response.json()
            }
        }).then(data => {
            if (data.status_code !== 200) {
                alert(`Access Token Update Failed: \nStatus Code: ${data.status_code}\nBody: ${data.body}`)
                console.log(data);
            }
            loader.resolve();
        }).catch(e => {
            loader.resolve();
            alert(`Access Token Exchange Failed: ${e.message}`)
            throw e;
        })
    }
}