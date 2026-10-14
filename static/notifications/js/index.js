let controller = function() {
    let objs = {
        discordIdInput: document.getElementById('discord-user-id'),
        notificationChannelToggles: document.getElementsByClassName('notification-channel-toggle'),
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

    let saveToggleSetting = function(input) {
        let field = input.dataset.field;
        let enabled = input.checked;
        let token = getCSRFToken();
        let loader = new Loader();
        loader.show();
        fetch('/api/settings', {
            method: 'PUT',
            headers: {
                'X-CSRFToken': token,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ [field]: enabled })
        }).then(async (res) => {
            return {
                status_code: res.status,
                body: await res.json()
            }
        }).then(data => {
            loader.resolve();
            if (data.status_code !== 200) {
                alert(data.body.message || `Failed to update ${input.dataset.label}`);
                input.checked = !enabled;
            }
        }).catch(e => {
            loader.resolve();
            alert(e.message);
            input.checked = !enabled;
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

    let initHelpTooltips = function() {
        // Touch screens can't hover, and iOS Safari doesn't focus buttons on tap, so
        // there the info icons open on tap and close on the next tap anywhere.
        let touchOnly = window.matchMedia('(hover: none)').matches;
        let helpButtons = Array.from(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        helpButtons.forEach(function(el) {
            new bootstrap.Tooltip(el, { trigger: touchOnly ? 'click' : 'hover focus' });
        });
        if (touchOnly) {
            document.addEventListener('click', function(event) {
                helpButtons.forEach(function(el) {
                    if (!el.contains(event.target)) {
                        bootstrap.Tooltip.getInstance(el).hide();
                    }
                });
            });
        }
    }

    let inits = function() {
        initHelpTooltips();

        objs.discordIdInput.dataset.savedValue = objs.discordIdInput.value;
        objs.discordIdInput.addEventListener('keydown', function(event) {
            if (event.key === 'Enter') {
                objs.discordIdInput.blur();
            }
        });
        objs.discordIdInput.addEventListener('blur', function() {
            saveTextSetting(objs.discordIdInput, 'discord_user_id', 'Discord User ID');
        });

        Array.from(objs.notificationChannelToggles).forEach(function(toggle) {
            toggle.addEventListener('change', function() {
                saveToggleSetting(toggle);
            });
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
