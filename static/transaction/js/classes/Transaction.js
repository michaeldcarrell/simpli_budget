class Transaction {
    constructor(transaction_id) {
        this.transaction_id = transaction_id;
    }

    setCategory(category_id, reload=false) {
        let token = getCSRFToken();
        let loader = new Loader();
        loader.show();
        fetch(`/api/transaction/${this.transaction_id}/category`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': token,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                category_id: category_id
            })
        }).then(async response => {
            return {
                status_code: response.status,
                body: await response.json()
            }
        }).then(data => {
            if (data.status_code !== 200) {
                alert(`Transaction Update Failed: \nStatus Code: ${data.status_code}\nBody: ${data.body}`)
                console.log(data);
            } else if (reload) {
                window.location.reload();
            }
            loader.resolve();
        }).catch(e => {
            loader.resolve();
            alert(`Transaction Failed: ${e.message}`)
            throw e;
        })
    }

    setTags(tag_ids, reload=false) {
        let token = getCSRFToken();
        let loader = new Loader();
        loader.show();
        fetch(`/api/transaction/${this.transaction_id}/tags`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': token,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tag_ids: tag_ids
            })
        }).then(async response => {
            return {
                status_code: response.status,
                body: await response.json()
            }
        }).then(data => {
            if (data.status_code !== 200) {
                alert(`Tags Update Failed: \nStatus Code: ${data.status_code}\nBody: ${data.body}`)
                console.log(data);
            } else if (reload) {
                window.location.reload();
            }
            loader.resolve();
        }).catch(e => {
            loader.resolve();
            alert(`Tag updates Failed: ${e.message}`)
            throw e;
        })
    }
}