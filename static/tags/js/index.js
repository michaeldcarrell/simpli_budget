let controller = function() {
    let objs = {
        form: document.getElementById('new-tag-form'),
        typeSelect: document.getElementById('new-tag-type'),
        nameInput: document.getElementById('new-tag-name'),
        errorBox: document.getElementById('new-tag-error'),
        deleteButtons: document.getElementsByClassName('delete-tag-btn'),
        removeModalEl: document.getElementById('remove-tag-modal'),
        removeTagName: document.getElementById('remove-tag-name'),
        confirmRemoveBtn: document.getElementById('confirm-remove-tag-btn'),
        createTypeModalEl: document.getElementById('create-tag-type-modal'),
        newTypeNameInput: document.getElementById('new-tag-type-name'),
        newTypeErrorBox: document.getElementById('new-tag-type-error'),
        confirmCreateTypeBtn: document.getElementById('confirm-create-tag-type-btn'),
    }
    let state = {
        pendingTagId: null,
    }
    let inits = function() {
        let removeModal = new bootstrap.Modal(objs.removeModalEl);
        let createTypeModal = new bootstrap.Modal(objs.createTypeModalEl);

        objs.typeSelect.addEventListener('change', function() {
            if (objs.typeSelect.value !== '__create_type__') {
                return;
            }
            objs.typeSelect.value = objs.typeSelect.options[0].value;
            objs.newTypeNameInput.value = '';
            objs.newTypeErrorBox.classList.add('hidden');
            createTypeModal.show();
        });

        objs.confirmCreateTypeBtn.addEventListener('click', function() {
            objs.newTypeErrorBox.classList.add('hidden');

            let token = getCSRFToken();
            let loader = new Loader();
            loader.show();
            fetch('/api/tag_type', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': token,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: objs.newTypeNameInput.value,
                })
            }).then(async (res) => {
                return {
                    status_code: res.status,
                    body: await res.json()
                }
            }).then(data => {
                if (data.status_code !== 201) {
                    loader.resolve();
                    objs.newTypeErrorBox.textContent = data.body.message || 'Failed to create tag type';
                    objs.newTypeErrorBox.classList.remove('hidden');
                    return;
                }
                window.location.reload();
            }).catch(e => {
                loader.resolve();
                objs.newTypeErrorBox.textContent = e.message;
                objs.newTypeErrorBox.classList.remove('hidden');
                throw e;
            });
        });

        Array.from(objs.deleteButtons).forEach(function(button) {
            button.addEventListener('click', function() {
                state.pendingTagId = button.getAttribute('data-tag-id');
                objs.removeTagName.textContent = button.getAttribute('data-tag-name');
                removeModal.show();
            });
        });

        objs.confirmRemoveBtn.addEventListener('click', function() {
            removeModal.hide();

            let token = getCSRFToken();
            let loader = new Loader();
            loader.show();
            fetch(`/api/tag/${state.pendingTagId}`, {
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
                    alert(data.body.message || 'Failed to remove tag');
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
            fetch('/api/tag', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': token,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    tag_type_id: parseInt(objs.typeSelect.value),
                    name: objs.nameInput.value,
                })
            }).then(async (res) => {
                return {
                    status_code: res.status,
                    body: await res.json()
                }
            }).then(data => {
                if (data.status_code !== 201 && data.status_code !== 200) {
                    loader.resolve();
                    objs.errorBox.textContent = data.body.message || 'Failed to create tag';
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
