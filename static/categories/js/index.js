let controller = function() {
    let objs = {
        form: document.getElementById('new-category-form'),
        typeSelect: document.getElementById('new-category-type'),
        nameInput: document.getElementById('new-category-name'),
        amountInput: document.getElementById('new-category-amount'),
        errorBox: document.getElementById('new-category-error'),
        deleteButtons: document.getElementsByClassName('delete-category-btn'),
        removeModalEl: document.getElementById('remove-category-modal'),
        removeCategoryName: document.getElementById('remove-category-name'),
        confirmRemoveBtn: document.getElementById('confirm-remove-category-btn'),
        createGroupModalEl: document.getElementById('create-category-type-modal'),
        newGroupNameInput: document.getElementById('new-category-type-name'),
        newGroupErrorBox: document.getElementById('new-category-type-error'),
        confirmCreateGroupBtn: document.getElementById('confirm-create-category-type-btn'),
    }
    let state = {
        pendingCategoryId: null,
    }
    let formatAmountInput = function(input) {
        let cursorFromEnd = input.value.length - input.selectionStart;
        let raw = input.value.replace(/[^\d.]/g, '');

        // only allow one decimal point
        let firstDot = raw.indexOf('.');
        if (firstDot !== -1) {
            raw = raw.slice(0, firstDot + 1) + raw.slice(firstDot + 1).replace(/\./g, '');
        }

        let [whole, decimal] = raw.split('.');
        let formattedWhole = whole ? Number(whole).toLocaleString('en-US') : '';
        input.value = decimal !== undefined ? `${formattedWhole}.${decimal}` : formattedWhole;

        let newPosition = Math.max(input.value.length - cursorFromEnd, 0);
        input.setSelectionRange(newPosition, newPosition);
    }
    let saveCategoryAmount = function(input) {
        let raw = input.value.replace(/,/g, '') || '0';
        let savedRaw = input.dataset.savedValue.replace(/,/g, '');
        if (raw === savedRaw) {
            return;
        }

        let categoryId = input.getAttribute('data-category-id');
        let token = getCSRFToken();
        let loader = new Loader();
        loader.show();
        fetch(`/api/category/${categoryId}`, {
            method: 'PUT',
            headers: {
                'X-CSRFToken': token,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ default_monthly_amount: raw })
        }).then(async (res) => {
            return {
                status_code: res.status,
                body: await res.json()
            }
        }).then(data => {
            loader.resolve();
            if (data.status_code !== 200) {
                alert(data.body.message || 'Failed to update category');
                input.value = input.dataset.savedValue;
                return;
            }
            input.value = Number(data.body.default_monthly_amount).toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
            });
            input.dataset.savedValue = input.value;
        }).catch(e => {
            loader.resolve();
            alert(e.message);
            input.value = input.dataset.savedValue;
            throw e;
        });
    }
    let inits = function() {
        objs.amountInput.addEventListener('input', function() {
            formatAmountInput(objs.amountInput);
        });

        Array.from(document.getElementsByClassName('category-amount-input')).forEach(function(input) {
            input.dataset.savedValue = input.value;
            input.addEventListener('input', function() {
                formatAmountInput(input);
            });
            input.addEventListener('keydown', function(event) {
                if (event.key === 'Enter') {
                    input.blur();
                }
            });
            input.addEventListener('blur', function() {
                saveCategoryAmount(input);
            });
        });

        let removeModal = new bootstrap.Modal(objs.removeModalEl);
        let createGroupModal = new bootstrap.Modal(objs.createGroupModalEl);

        objs.typeSelect.addEventListener('change', function() {
            if (objs.typeSelect.value !== '__create_group__') {
                return;
            }
            objs.typeSelect.value = objs.typeSelect.options[0].value;
            objs.newGroupNameInput.value = '';
            objs.newGroupErrorBox.classList.add('hidden');
            createGroupModal.show();
        });

        objs.confirmCreateGroupBtn.addEventListener('click', function() {
            objs.newGroupErrorBox.classList.add('hidden');

            let token = getCSRFToken();
            let loader = new Loader();
            loader.show();
            fetch('/api/category_type', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': token,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    category_type_name: objs.newGroupNameInput.value,
                })
            }).then(async (res) => {
                return {
                    status_code: res.status,
                    body: await res.json()
                }
            }).then(data => {
                if (data.status_code !== 201) {
                    loader.resolve();
                    objs.newGroupErrorBox.textContent = data.body.message || 'Failed to create group';
                    objs.newGroupErrorBox.classList.remove('hidden');
                    return;
                }
                window.location.reload();
            }).catch(e => {
                loader.resolve();
                objs.newGroupErrorBox.textContent = e.message;
                objs.newGroupErrorBox.classList.remove('hidden');
                throw e;
            });
        });

        Array.from(objs.deleteButtons).forEach(function(button) {
            button.addEventListener('click', function() {
                state.pendingCategoryId = button.getAttribute('data-category-id');
                objs.removeCategoryName.textContent = button.getAttribute('data-category-name');
                removeModal.show();
            });
        });

        objs.confirmRemoveBtn.addEventListener('click', function() {
            removeModal.hide();

            let token = getCSRFToken();
            let loader = new Loader();
            loader.show();
            fetch(`/api/category/${state.pendingCategoryId}`, {
                method: 'DELETE',
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
                    alert(data.body.message || 'Failed to remove category');
                    return;
                }
                window.location.reload();
            }).catch(e => {
                loader.resolve();
                alert(e.message);
                throw e;
            });
        });

        objs.form.addEventListener('submit', function(event) {
            event.preventDefault();
            objs.errorBox.classList.add('hidden');

            let token = getCSRFToken();
            let loader = new Loader();
            loader.show();
            fetch('/api/category', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': token,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    category_type_id: parseInt(objs.typeSelect.value),
                    category_name: objs.nameInput.value,
                    default_monthly_amount: objs.amountInput.value.replace(/,/g, '') || 0,
                })
            }).then(async (res) => {
                return {
                    status_code: res.status,
                    body: await res.json()
                }
            }).then(data => {
                if (data.status_code !== 201 && data.status_code !== 200) {
                    loader.resolve();
                    objs.errorBox.textContent = data.body.message || 'Failed to create category';
                    objs.errorBox.classList.remove('hidden');
                    return;
                }
                window.location.reload();
            }).catch(e => {
                loader.resolve();
                objs.errorBox.textContent = e.message;
                objs.errorBox.classList.remove('hidden');
                throw e;
            });
        });
    }();
}();
