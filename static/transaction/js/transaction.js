let controller = function() {
    let objs = {
        categorySelector: document.getElementById('category'),
    }

    let updateTransaction = function() {
        let category_id = objs.categorySelector.value;
        let transaction_id = window.location.pathname.split('/')[-1];
        fetch('/api/transaction', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                transaction_id: transaction_id,
                category_id: category_id
            })
        }).then(async response => {
            return {
                status_code: response.status,
                body: await response.json()
            }
        }).then(data => {
            console.log(data);
        })
    }

    let init = function() {
        objs.categorySelector.addEventListener('change', function() {
            console.log('changed category:', objs.categorySelector.value);
            updateTransaction()
        })
    }();
}();