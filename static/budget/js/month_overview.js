let controller = function() {
    let objs = {
        nextMonth: document.getElementById('next-month'),
        lastMonth: document.getElementById('last-month'),
        generateDemoActivity: document.getElementById('generate-demo-activity'),
        amountInputs: document.getElementsByClassName('category-month-amount'),
    }
    let inits = function() {
        objs.nextMonth.addEventListener('click', function() {
            let href = this.getAttribute('data-href');
            window.location.href = href;
        });

        objs.lastMonth.addEventListener('click', function() {
            let href = this.getAttribute('data-href');
            window.location.href = href;
        });

        Array.from(objs.amountInputs).forEach(function(amountInput) {
            let categoryMonth = new CategoryMonth(
                parseInt(amountInput.dataset.categoryId),
                parseInt(amountInput.dataset.yearMonth)
            );

            let showCategoryMonth = function(data) {
                amountInput.value = Number(data.amount).toFixed(2);
                amountInput.dataset.savedValue = amountInput.value;
                amountInput.classList.toggle('category-month-override', data.is_override);
                amountInput.title = data.is_override
                    ? 'Set for this month only. Clear to go back to the category default.'
                    : 'Using the category default';
            }

            let revertAmount = function(e) {
                alert(e.message);
                amountInput.value = amountInput.dataset.savedValue;
            }

            amountInput.dataset.savedValue = amountInput.value;
            amountInput.addEventListener('change', function() {
                let raw = amountInput.value.replace(/[$,\s]/g, '');
                if (raw !== '' && Number(raw) === Number(amountInput.dataset.savedValue)) {
                    amountInput.value = amountInput.dataset.savedValue;
                    return;
                }
                if (raw === '') {
                    // Clearing the field means "stop overriding this month"
                    categoryMonth.clearAmount().then(showCategoryMonth).catch(revertAmount);
                    return;
                }
                categoryMonth.setAmount(raw).then(showCategoryMonth).catch(revertAmount);
            });
            amountInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') {
                    amountInput.blur();
                }
            });
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