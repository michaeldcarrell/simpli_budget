class CategoryMonth {
    constructor(category_id, month_id) {
        this.category_id = category_id;
        this.month_id = month_id;
    }

    get transactions() {
        return document.getElementsByClassName('transaction-category-selector');
    }

    get transaction_count() {
        let count = 0;
        for (let i = 0; i < this.transactions.length; i++) {
            if (parseInt(this.transactions[i].value) === this.category_id) {
                count++;
            }
        }
        return count;
    }

    // Sets this month's budgeted amount, overriding the category default.
    setAmount(amount) {
        return this.#request('POST', {year_month: this.month_id, amount: amount});
    }

    // Removes this month's override so it goes back to the category default.
    clearAmount() {
        return this.#request('DELETE', {year_month: this.month_id});
    }

    #request(method, body) {
        let loader = new Loader();
        loader.show();
        return fetch(`/api/category/${this.category_id}/month`, {
            method: method,
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body)
        }).then(async response => {
            let data = await response.json();
            if (response.status !== 200) {
                throw new Error(data.message || 'Failed to update budgeted amount');
            }
            return data;
        }).finally(() => {
            loader.resolve();
        });
    }
}