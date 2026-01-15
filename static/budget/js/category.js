let objs = {
    categorySelectors: document.getElementsByClassName("transaction-category-selector"),
}

let controller = function() {
    let init = function() {
        let getCategoryMonth = function() {
            let category_id = parseInt(window.location.pathname.split('/').reverse()[0]);
            let month_id = parseInt(getQueryParamValue('month'));
            objs.categoryMonth = new CategoryMonth(category_id, month_id);
        }();

        Array.from(objs.categorySelectors).forEach(function(categorySelector) {
            categorySelector.addEventListener('change', function() {
                let transaction_id = categorySelector.getAttribute('transaction_id');
                let transaction = new Transaction(transaction_id);
                transaction.setCategory(categorySelector.value, false);
                if (objs.categoryMonth.transaction_count === 0) {
                    window.location.href = `/?month=${objs.categoryMonth.month_id}`;
                }
            })
        })
    }();
}();