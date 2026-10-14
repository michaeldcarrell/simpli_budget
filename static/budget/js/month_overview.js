let controller = function() {
    let objs = {
        generateDemoActivity: document.getElementById('generate-demo-activity'),
        sheet: document.getElementById('budget-sheet'),
        sheetForm: document.getElementById('budget-sheet-form'),
        sheetTitle: document.getElementById('budget-sheet-title'),
        sheetAmount: document.getElementById('budget-sheet-amount'),
        sheetSpentLabel: document.getElementById('budget-sheet-spent-label'),
        sheetSpent: document.getElementById('budget-sheet-spent'),
        sheetAverage: document.getElementById('budget-sheet-average'),
        sheetDefault: document.getElementById('budget-sheet-default'),
        sheetReset: document.getElementById('budget-sheet-reset'),
        sheetTransactions: document.getElementById('budget-sheet-transactions'),
    }

    // The row that opened the sheet; its data-* attributes describe the category being edited.
    let activeRow = null;

    let formatNumber = function(value) {
        return Number(value).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    }

    let fillSheet = function(row) {
        activeRow = row;
        let data = row.dataset;
        objs.sheetTitle.textContent = data.name;
        objs.sheetAmount.value = data.amount;
        objs.sheetSpentLabel.textContent = data.isIncome === 'true' ? 'Received' : 'Spent';
        objs.sheetSpent.textContent = data.spent;
        objs.sheetAverage.textContent = data.average || '—';
        objs.sheetDefault.textContent = formatNumber(data.default);
        objs.sheetReset.classList.toggle('hidden', data.isOverride !== 'true');
        objs.sheetTransactions.href = `/budget/category/${data.categoryId}?month=${data.yearMonth}`;
        objs.sheetForm.querySelector('input[name="budget-sheet-scope"][value="month"]').checked = true;
    }

    let categoryMonthFor = function(row) {
        return new CategoryMonth(parseInt(row.dataset.categoryId), parseInt(row.dataset.yearMonth));
    }

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

    let saveSheet = function(event) {
        event.preventDefault();
        if (!activeRow) {
            return;
        }
        let raw = objs.sheetAmount.value.replace(/[$,\s]/g, '');
        if (raw === '' || isNaN(Number(raw)) || Number(raw) < 0) {
            alert('Enter an amount of 0 or more.');
            objs.sheetAmount.focus();
            return;
        }

        let scope = objs.sheetForm.querySelector('input[name="budget-sheet-scope"]:checked').value;
        let categoryMonth = categoryMonthFor(activeRow);
        let save;
        if (scope === 'default') {
            // A month with its own amount would hide the new default, so drop that override too.
            save = setCategoryDefault(activeRow.dataset.categoryId, raw).then(() => {
                if (activeRow.dataset.isOverride === 'true') {
                    return categoryMonth.clearAmount();
                }
            });
        } else {
            save = categoryMonth.setAmount(raw);
        }
        save.then(() => window.location.reload()).catch(e => alert(e.message));
    }

    let inits = function() {
        objs.sheet.addEventListener('show.bs.offcanvas', function(event) {
            if (event.relatedTarget) {
                fillSheet(event.relatedTarget);
            }
        });
        objs.sheet.addEventListener('shown.bs.offcanvas', function() {
            objs.sheetAmount.select();
        });

        objs.sheetForm.addEventListener('submit', saveSheet);

        objs.sheetReset.addEventListener('click', function() {
            if (!activeRow) {
                return;
            }
            categoryMonthFor(activeRow).clearAmount()
                .then(() => window.location.reload())
                .catch(e => alert(e.message));
        });

        if (objs.generateDemoActivity) {
            objs.generateDemoActivity.addEventListener('click', function() {
                let token = getCSRFToken();
                let loader = new Loader();
                loader.show();
                fetch('/api/demo/generate_activity', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': token,
                        'Content-Type': 'application/json'
                    }
                }).then(async (res) => {
                    return {
                        status_code: res.status,
                        body: await res.json()
                    }
                }).then(data => {
                    if (data.status_code !== 200) {
                        loader.resolve();
                        alert(`Failed to generate activity: \nStatus Code: ${data.status_code}\nBody: ${JSON.stringify(data.body)}`);
                        return;
                    }
                    window.location.reload();
                }).catch(e => {
                    loader.resolve();
                    alert(`Failed to generate activity: ${e.message}`);
                    throw e;
                });
            });
        }
    }();
}();
