let objs = {
    categorySelectors: document.getElementsByClassName("transaction-category-selector"),
    amountInput: document.getElementById("category-month-amount"),
    amountReset: document.getElementById("category-month-reset"),
    amountDefaultNote: document.getElementById("category-month-default-note"),
}

let controller = function() {
    let init = function() {
        let getCategoryMonth = function() {
            let category_id = parseInt(window.location.pathname.split('/').reverse()[0]);
            let month_id = parseInt(objs.amountInput.dataset.yearMonth);
            objs.categoryMonth = new CategoryMonth(category_id, month_id);
        }();

        let showCategoryMonth = function(categoryMonth) {
            objs.amountInput.value = Number(categoryMonth.amount).toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
            });
            objs.amountInput.dataset.savedValue = objs.amountInput.value;
            objs.amountReset.classList.toggle('d-none', !categoryMonth.is_override);
            objs.amountDefaultNote.classList.toggle('d-none', categoryMonth.is_override);
        }

        let revertAmount = function(e) {
            alert(e.message);
            objs.amountInput.value = objs.amountInput.dataset.savedValue;
        }

        objs.amountInput.dataset.savedValue = objs.amountInput.value;
        objs.amountInput.addEventListener('change', function() {
            let raw = objs.amountInput.value.replace(/[$,\s]/g, '');
            if (raw === objs.amountInput.dataset.savedValue.replace(/,/g, '')) {
                return;
            }
            if (raw === '') {
                // Clearing the field means "stop overriding this month"
                objs.categoryMonth.clearAmount().then(showCategoryMonth).catch(revertAmount);
                return;
            }
            objs.categoryMonth.setAmount(raw).then(showCategoryMonth).catch(revertAmount);
        });
        objs.amountInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                objs.amountInput.blur();
            }
        });
        objs.amountReset.addEventListener('click', function() {
            objs.categoryMonth.clearAmount().then(showCategoryMonth).catch(revertAmount);
        });

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