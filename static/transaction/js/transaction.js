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
        let transaction = new Transaction(transaction_id);
        transaction.setCategory(category_id);
    }

    let init = function() {
        objs.categorySelector.addEventListener('change', function() {
            updateTransaction()
        })
    }();
}();