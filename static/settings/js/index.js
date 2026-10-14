let controller = function() {
    let objs = {
        discordIdInput: document.getElementById('discord-user-id'),
        notificationEmailInput: document.getElementById('notification-email'),
        notificationFrequencyInput: document.getElementById('notification-frequency-days'),
        notificationToggles: document.getElementsByClassName('notification-category-toggle'),
    }

    let saveTextSetting = function(input, field, label) {
        let value = input.value.trim();
        if (value === (input.dataset.savedValue || '')) {
            return;
        }

        let token = getCSRFToken();
        let loader = new Loader();
        loader.show();
        fetch('/api/settings', {
            method: 'PUT',
            headers: {
                'X-CSRFToken': token,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ [field]: value })
        }).then(async (res) => {
            return {
                status_code: res.status,
                body: await res.json()
            }
        }).then(data => {
            loader.resolve();
            if (data.status_code !== 200) {
                alert(data.body.message || `Failed to update ${label}`);
                input.value = input.dataset.savedValue || '';
                return;
            }
            input.dataset.savedValue = data.body[field] || '';
            input.value = input.dataset.savedValue;
        }).catch(e => {
            loader.resolve();
            alert(e.message);
            input.value = input.dataset.savedValue || '';
            throw e;
        });
    }

    let saveNotificationFrequencyDays = function(input) {
        let value = parseInt(input.value, 10);
        if (String(value) === (input.dataset.savedValue || '')) {
            return;
        }
        if (!Number.isInteger(value) || value < 1) {
            alert('Notification frequency must be a whole number of days, at least 1.');
            input.value = input.dataset.savedValue || '';
            return;
        }

        let token = getCSRFToken();
        let loader = new Loader();
        loader.show();
        fetch('/api/settings', {
            method: 'PUT',
            headers: {
                'X-CSRFToken': token,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ notification_frequency_days: value })
        }).then(async (res) => {
            return {
                status_code: res.status,
                body: await res.json()
            }
        }).then(data => {
            loader.resolve();
            if (data.status_code !== 200) {
                alert(data.body.message || 'Failed to update notification frequency');
                input.value = input.dataset.savedValue || '';
                return;
            }
            input.dataset.savedValue = String(data.body.notification_frequency_days);
            input.value = input.dataset.savedValue;
        }).catch(e => {
            loader.resolve();
            alert(e.message);
            input.value = input.dataset.savedValue || '';
            throw e;
        });
    }

    let saveNotificationCategory = function(input) {
        let categoryId = input.getAttribute('data-category-id');
        let subscribed = input.checked;
        let token = getCSRFToken();
        let loader = new Loader();
        loader.show();
        fetch(`/api/category/${categoryId}/notification`, {
            method: 'PUT',
            headers: {
                'X-CSRFToken': token,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ subscribed: subscribed })
        }).then(async (res) => {
            return {
                status_code: res.status,
                body: await res.json()
            }
        }).then(data => {
            loader.resolve();
            if (data.status_code !== 200) {
                alert(data.body.message || 'Failed to update notification category');
                input.checked = !subscribed;
            }
        }).catch(e => {
            loader.resolve();
            alert(e.message);
            input.checked = !subscribed;
            throw e;
        });
    }

    let inits = function() {
        objs.discordIdInput.dataset.savedValue = objs.discordIdInput.value;
        objs.discordIdInput.addEventListener('keydown', function(event) {
            if (event.key === 'Enter') {
                objs.discordIdInput.blur();
            }
        });
        objs.discordIdInput.addEventListener('blur', function() {
            saveTextSetting(objs.discordIdInput, 'discord_user_id', 'Discord User ID');
        });

        objs.notificationEmailInput.dataset.savedValue = objs.notificationEmailInput.value;
        objs.notificationEmailInput.addEventListener('keydown', function(event) {
            if (event.key === 'Enter') {
                objs.notificationEmailInput.blur();
            }
        });
        objs.notificationEmailInput.addEventListener('blur', function() {
            saveTextSetting(objs.notificationEmailInput, 'notification_email', 'Notification Email');
        });

        objs.notificationFrequencyInput.dataset.savedValue = objs.notificationFrequencyInput.value;
        objs.notificationFrequencyInput.addEventListener('keydown', function(event) {
            if (event.key === 'Enter') {
                objs.notificationFrequencyInput.blur();
            }
        });
        objs.notificationFrequencyInput.addEventListener('blur', function() {
            saveNotificationFrequencyDays(objs.notificationFrequencyInput);
        });

        Array.from(objs.notificationToggles).forEach(function(toggle) {
            toggle.addEventListener('change', function() {
                saveNotificationCategory(toggle);
            });
        });
    }();
}();
