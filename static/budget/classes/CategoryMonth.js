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
}