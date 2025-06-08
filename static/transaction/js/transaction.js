let controller = function() {
    let objs = {
        categorySelector: document.getElementById('category'),
    }

    let getTransactionId = function() {
        let path = window.location.pathname.split('/');
        return path[path.length - 1];
    }

    let updateTransaction = function() {
        let category_id = objs.categorySelector.value;
        let transaction_id = getTransactionId();
        let token = getCSRFToken();
        fetch('/api/transaction', {
            method: 'POST',
            headers: {
                'X-CSRFToken': token,
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
            if (data.status_code !== 200) {
                alert(`Transaction Update Failed: \nStatus Code: ${data.status_code}\nBody: ${data.body}`)
            }
        }).catch(e => {
            alert(`Transaction Failed: ${e.message}`)
        })
    }

    let init = function() {
        objs.categorySelector.addEventListener('change', function() {
            updateTransaction()
        })
    }();
}();