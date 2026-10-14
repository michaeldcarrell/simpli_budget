let controller = function() {
    let objs = {
        form: document.getElementById('new-category-form'),
        addSheet: document.getElementById('add-category-sheet'),
        typeSelect: document.getElementById('new-category-type'),
        nameInput: document.getElementById('new-category-name'),
        amountInput: document.getElementById('new-category-amount'),
        errorBox: document.getElementById('new-category-error'),
        editSheet: document.getElementById('edit-category-sheet'),
        editForm: document.getElementById('edit-category-form'),
        editTitle: document.getElementById('edit-category-title'),
        editAmount: document.getElementById('edit-category-amount'),
        editAverage: document.getElementById('edit-category-average'),
        removeButton: document.getElementById('remove-category-btn'),
        removeModalEl: document.getElementById('remove-category-modal'),
        removeCategoryName: document.getElementById('remove-category-name'),
        confirmRemoveBtn: document.getElementById('confirm-remove-category-btn'),
        createGroupModalEl: document.getElementById('create-category-type-modal'),
        newGroupNameInput: document.getElementById('new-category-type-name'),
        newGroupErrorBox: document.getElementById('new-category-type-error'),
        confirmCreateGroupBtn: document.getElementById('confirm-create-category-type-btn'),
    }
    // The row that opened the edit sheet; its data-* attributes describe the category.
    let activeRow = null;

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

    let request = function(method, url, body, okStatuses) {
        let loader = new Loader();
        loader.show();
        return fetch(url, {
            method: method,
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json'
            },
            body: body ? JSON.stringify(body) : undefined
        }).then(async (res) => {
            let data = await res.json();
            if (!okStatuses.includes(res.status)) {
                throw new Error(data.message || 'Something went wrong');
            }
            return data;
        }).finally(() => {
            loader.resolve();
        });
    }

    let fillEditSheet = function(row) {
        activeRow = row;
        objs.editTitle.textContent = row.dataset.name;
        objs.editAmount.value = Number(row.dataset.amount).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        objs.editAverage.textContent = row.dataset.average
            ? `${row.dataset.averageMonths}-month average: ${row.dataset.average}`
            : 'No complete months of history yet.';
    }

    let inits = function() {
        [objs.amountInput, objs.editAmount].forEach(function(input) {
            input.addEventListener('input', function() {
                formatAmountInput(input);
            });
        });

        objs.editSheet.addEventListener('show.bs.offcanvas', function(event) {
            if (event.relatedTarget) {
                fillEditSheet(event.relatedTarget);
            }
        });
        objs.editSheet.addEventListener('shown.bs.offcanvas', function() {
            objs.editAmount.select();
        });
        objs.addSheet.addEventListener('shown.bs.offcanvas', function() {
            objs.nameInput.focus();
        });

        objs.editForm.addEventListener('submit', function(event) {
            event.preventDefault();
            let raw = objs.editAmount.value.replace(/,/g, '') || '0';
            request('PUT', `/api/category/${activeRow.dataset.categoryId}`, {default_monthly_amount: raw}, [200])
                .then(() => window.location.reload())
                .catch(e => alert(e.message));
        });

        let removeModal = new bootstrap.Modal(objs.removeModalEl);
        let createGroupModal = new bootstrap.Modal(objs.createGroupModalEl);

        objs.removeButton.addEventListener('click', function() {
            objs.removeCategoryName.textContent = activeRow.dataset.name;
            bootstrap.Offcanvas.getOrCreateInstance(objs.editSheet).hide();
            removeModal.show();
        });

        objs.confirmRemoveBtn.addEventListener('click', function() {
            removeModal.hide();
            request('DELETE', `/api/category/${activeRow.dataset.categoryId}`, null, [200])
                .then(() => window.location.reload())
                .catch(e => alert(e.message));
        });

        objs.typeSelect.addEventListener('change', function() {
            if (objs.typeSelect.value !== '__create_group__') {
                return;
            }
            objs.typeSelect.value = objs.typeSelect.options[0].value;
            objs.newGroupNameInput.value = '';
            objs.newGroupErrorBox.classList.add('hidden');
            // A sheet and a modal both trap focus, so swap one for the other rather than stacking them.
            bootstrap.Offcanvas.getOrCreateInstance(objs.addSheet).hide();
            createGroupModal.show();
        });
        objs.createGroupModalEl.addEventListener('shown.bs.modal', function() {
            objs.newGroupNameInput.focus();
        });
        objs.createGroupModalEl.addEventListener('hidden.bs.modal', function() {
            bootstrap.Offcanvas.getOrCreateInstance(objs.addSheet).show();
        });

        objs.confirmCreateGroupBtn.addEventListener('click', function() {
            objs.newGroupErrorBox.classList.add('hidden');
            request('POST', '/api/category_type', {category_type_name: objs.newGroupNameInput.value}, [201])
                .then(() => window.location.reload())
                .catch(e => {
                    objs.newGroupErrorBox.textContent = e.message || 'Failed to create group';
                    objs.newGroupErrorBox.classList.remove('hidden');
                });
        });

        objs.form.addEventListener('submit', function(event) {
            event.preventDefault();
            objs.errorBox.classList.add('hidden');
            request('POST', '/api/category', {
                category_type_id: parseInt(objs.typeSelect.value),
                category_name: objs.nameInput.value,
                default_monthly_amount: objs.amountInput.value.replace(/,/g, '') || 0,
            }, [200, 201])
                .then(() => window.location.reload())
                .catch(e => {
                    objs.errorBox.textContent = e.message || 'Failed to create category';
                    objs.errorBox.classList.remove('hidden');
                });
        });
    }();
}();
