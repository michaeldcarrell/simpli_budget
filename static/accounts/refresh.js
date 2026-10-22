let refreshController = function() {
    let objs = {
        status: document.getElementById('refresh-status'),
        button: document.getElementById('refresh-btn'),
    };

    const POLL_MS = 5000;
    let pollTimer = null;
    // Set once this page starts a run, so its result can be reported when it finishes.
    let watching = false;

    let groupQuery = function() {
        let groupId = getQueryParamValue('group_id');
        return groupId ? `?group_id=${encodeURIComponent(groupId)}` : '';
    }

    let when = function(iso) {
        let date = new Date(iso);
        let minutes = Math.round((Date.now() - date) / 60000);
        if (minutes < 1) {
            return 'just now';
        }
        if (minutes < 60) {
            return `${minutes} min ago`;
        }
        return date.toLocaleString([], {month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'});
    }

    let show = function(run) {
        objs.status.classList.remove('text-warn', 'text-over');
        if (run.active) {
            objs.status.textContent = run.state === 'queued' ? 'Refresh queued…' : 'Refreshing…';
            objs.button.disabled = true;
            pollTimer = setTimeout(load, POLL_MS);
            return;
        }
        objs.button.disabled = false;
        if (!run.state) {
            objs.status.textContent = 'Not refreshed yet';
        } else if (run.state === 'success') {
            if (watching) {
                objs.status.textContent = 'Refreshed just now. Reload a page to see new transactions.';
            } else {
                objs.status.textContent = `Last refreshed ${when(run.finished_at || run.started_at)} (${run.manual ? 'manual' : 'nightly'})`;
            }
        } else {
            objs.status.classList.add('text-over');
            objs.status.textContent = `Last refresh failed ${when(run.finished_at || run.started_at)}`;
        }
        watching = false;
    }

    let showError = function(message) {
        objs.status.classList.add('text-warn');
        objs.status.textContent = message;
        objs.button.disabled = false;
        watching = false;
    }

    let load = async function() {
        clearTimeout(pollTimer);
        try {
            let res = await fetch(`/api/transactions/refresh${groupQuery()}`);
            let data = await res.json();
            res.ok ? show(data) : showError(data.message || 'Refresh status is unavailable right now.');
        } catch (e) {
            showError('Refresh status is unavailable right now.');
        }
    }

    objs.button.addEventListener('click', async function() {
        objs.button.disabled = true;
        objs.status.textContent = 'Starting refresh…';
        try {
            let res = await fetch(`/api/transactions/refresh${groupQuery()}`, {
                method: 'POST',
                headers: {'X-CSRFToken': getCSRFToken()},
            });
            let data = await res.json();
            if (res.ok || res.status === 409) {
                watching = true;
                show(data);
            } else {
                showError(data.message || 'Couldn’t start a refresh right now.');
            }
        } catch (e) {
            showError('Couldn’t start a refresh right now.');
        }
    });

    load();
}();
