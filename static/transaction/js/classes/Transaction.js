class Transaction {
    constructor(transaction_id) {
        this.transaction_id = transaction_id;
    }

    setCategory(category_id, reload=false) {
        let token = getCSRFToken();
        let loader = new Loader();
        loader.show();
        return fetch(`/api/transaction/${this.transaction_id}/category`, {
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
            return data.status_code === 200;
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

    // Replaces the split lines ([{category_id, amount}], amounts positive). Resolves to the transaction,
    // or rejects with the server's message.
    setSplits(lines) {
        return this.#splitsRequest('PUT', {splits: lines});
    }

    clearSplits() {
        return this.#splitsRequest('DELETE');
    }

    #splitsRequest(method, body) {
        let loader = new Loader();
        loader.show();
        return fetch(`/api/transaction/${this.transaction_id}/splits`, {
            method: method,
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json',
            },
            body: body === undefined ? undefined : JSON.stringify(body),
        }).then(async response => {
            let data = await response.json().catch(() => ({}));
            if (response.status !== 200) {
                throw new Error(data.message || `Saving the split failed (status ${response.status})`);
            }
            return data;
        }).finally(() => {
            loader.resolve();
        });
    }
}
