let objs = {
    categorySelectors: document.getElementsByClassName("transaction-category-selector"),
    categoryMonthContainer: document.getElementById("category-month"),
    sheet: document.getElementById('budget-sheet'),
    sheetForm: document.getElementById('budget-sheet-form'),
    sheetAmount: document.getElementById('budget-sheet-amount'),
    sheetReset: document.getElementById('budget-sheet-reset'),
}

let controller = function() {
    let setCategoryDefault = function(categoryId, amount) {
        let loader = new Loader();
        loader.show();
        return fetch(`/api/category/${categoryId}`, {
            method: 'PUT',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ default_monthly_amount: amount })
        }).then(async response => {
            let data = await response.json();
            if (response.status !== 200) {
                throw new Error(data.message || 'Failed to update the default budget');
            }
            return data;
        }).finally(() => {
            loader.resolve();
        });
    }

    let saveBudget = function(event) {
        event.preventDefault();
        let raw = objs.sheetAmount.value.replace(/[$,\s]/g, '');
        if (raw === '' || isNaN(Number(raw)) || Number(raw) < 0) {
            alert('Enter an amount of 0 or more.');
            objs.sheetAmount.focus();
            return;
        }

        let scope = objs.sheetForm.querySelector('input[name="budget-sheet-scope"]:checked').value;
        let categoryMonth = objs.categoryMonth;
        let save;
        if (scope === 'default') {
            // A month with its own amount would hide the new default, so drop that override too.
            save = setCategoryDefault(categoryMonth.category_id, raw).then(() => {
                if (objs.categoryMonthContainer.dataset.isOverride === 'true') {
                    return categoryMonth.clearAmount();
                }
            });
        } else {
            save = categoryMonth.setAmount(raw);
        }
        save.then(() => window.location.reload()).catch(e => alert(e.message));
    }

    let init = function() {
        let getCategoryMonth = function() {
            let category_id = parseInt(window.location.pathname.split('/').reverse()[0]);
            let month_id = parseInt(objs.categoryMonthContainer.dataset.yearMonth);
            objs.categoryMonth = new CategoryMonth(category_id, month_id);
        }();

        Array.from(objs.categorySelectors).forEach(function(categorySelector) {
            categorySelector.addEventListener('change', function() {
                let transaction_id = categorySelector.getAttribute('transaction_id');
                let transaction = new Transaction(transaction_id);
                transaction.setCategory(categorySelector.value, false);
                if (objs.categoryMonth.transaction_count === 0) {
                    window.location.href = `/budget?month=${objs.categoryMonth.month_id}`;
                }
            })
        })

        // The budget sheet is left out for the read-only demo user.
        if (objs.sheet) {
            objs.sheet.addEventListener('shown.bs.offcanvas', function() {
                objs.sheetAmount.select();
            });
            objs.sheetForm.addEventListener('submit', saveBudget);
        }
        if (objs.sheetReset) {
            objs.sheetReset.addEventListener('click', function() {
                objs.categoryMonth.clearAmount()
                    .then(() => window.location.reload())
                    .catch(e => alert(e.message));
            });
        }
    }();
}();