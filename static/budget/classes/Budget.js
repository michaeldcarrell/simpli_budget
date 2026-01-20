class Budget {
    constructor() {
        this.transactions = [];
    }

    async getTransactions(
        page = 1,
        page_size = 10,
    ) {
        let token = getCSRFToken();

        try {
            const params = new URLSearchParams({
                page: page,
                page_size: page_size,
            });

            const res = await fetch(`/api/transactions?${params.toString()}`, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': token,
                    'Content-Type': 'application/json'
                }
            });

            const body = await res.json();
            if (res.status !== 200) {
                alert(`Failed to get Transactions: \nStatus Code: ${res.status}\nBody: ${body}`)
                console.log('Transactions fetched: error');

                return []
            }
            console.log('Transactions fetched: fetch');
            return body;
        } catch (e) {
            alert(`Failed to get Transactions: ${e.message}`)
            console.log(e);
            return [];
        }
    }

    async searchTransactions(page, page_size, filters, ordering) {
        let token = getCSRFToken();

        try {
            const request_body = {
                page: page,
                page_size: page_size,
                filters: filters,
                ordering: ordering,
            }

            const res = await fetch(`/api/transactions`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': token,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(request_body)
            });

            const body = await res.json();
            if (res.status !== 200) {
                alert(`Failed to get Transactions: \nStatus Code: ${res.status}\nBody: ${body}`)
                console.log('Transactions fetched: error');

                return []
            }
            console.log('Transactions fetched: fetch');
            return body;
        } catch (e) {
            alert(`Failed to get Transactions: ${e.message}`)
            console.log(e);
            return [];
        }
    }
}