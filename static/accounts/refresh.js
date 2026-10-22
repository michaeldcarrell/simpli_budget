// "Refresh now" for transactions: the Bank sync section on the accounts page, and the compact
// "Synced 3h ago · Refresh" line (status element marked data-compact) on the transactions page.
let refreshController = function() {
    let objs = {
        status: document.getElementById('refresh-status'),
        button: document.getElementById('refresh-btn'),
    };

    const POLL_MS = 5000;
    const compact = objs.status.hasAttribute('data-compact');
    const buttonLabel = objs.button.textContent;
    let pollTimer = null;
    // Set once this page starts a run, so its result can be reported when it finishes.
    let watching = false;
    // After a run this page started succeeds, the button reloads the page to show what came in.
    let showNew = false;

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
        if (minutes < 24 * 60) {
            return `${Math.round(minutes / 60)}h ago`;
        }
        return date.toLocaleString([], {month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'});
    }

    let setButton = function(label, disabled) {
        objs.button.textContent = label;
        objs.button.disabled = disabled;
    }

    let show = function(run) {
        objs.status.classList.remove('text-warn', 'text-over');
        if (run.active) {
            objs.status.textContent = compact ? 'Syncing…' : (run.state === 'queued' ? 'Refresh queued…' : 'Refreshing…');
            setButton(buttonLabel, true);
            pollTimer = setTimeout(load, POLL_MS);
            return;
        }
        setButton(buttonLabel, false);
        if (!run.state) {
            objs.status.textContent = compact ? 'Not synced yet' : 'Not refreshed yet';
        } else if (run.state === 'success') {
            let finished = when(run.finished_at || run.started_at);
            if (watching) {
                showNew = true;
                setButton(compact ? 'Show new' : 'Reload', false);
                objs.status.textContent = compact ? 'Synced just now' : 'Refreshed just now.';
            } else if (compact) {
                objs.status.textContent = `Synced ${finished}`;
            } else {
                objs.status.textContent = `Last refreshed ${finished} (${run.manual ? 'manual' : 'nightly'})`;
            }
        } else {
            objs.status.classList.add('text-over');
            objs.status.textContent = `${compact ? 'Sync' : 'Last refresh'} failed ${when(run.finished_at || run.started_at)}`;
        }
        watching = false;
    }

    let showError = function(message) {
        objs.status.classList.add('text-warn');
        objs.status.textContent = compact ? 'Sync status unavailable' : message;
        setButton(buttonLabel, false);
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
        if (showNew) {
            window.location.reload();
            return;
        }
        setButton(buttonLabel, true);
        objs.status.textContent = compact ? 'Starting sync…' : 'Starting refresh…';
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
