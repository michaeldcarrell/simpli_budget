let objs = {
    categorySelectors: document.getElementsByClassName("transaction-category-selector")
}
let controller = function() {
    let init = function() {
        Array.from(objs.categorySelectors).forEach(function(categorySelector) {
            categorySelector.addEventListener('change', function() {
                let transaction_id = categorySelector.getAttribute('transaction_id');
                let transaction = new Transaction(transaction_id);
                transaction.setCategory(categorySelector.value, true);
            })
        })
    }();
}();