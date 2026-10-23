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
    // Set once this page starts a run; when that run succeeds the page reloads to show what came in.
    let watching = false;

    let groupQuery = function() {
        let groupId = getQueryParamValue('group_id');
        return groupId ? `?group_id=${encodeURIComponent(groupId)}` : '';
    }

    // The server sends how long ago the run was, so this doesn't depend on the device's clock or time zone.
    let when = function(secondsAgo) {
        let minutes = Math.round(secondsAgo / 60);
        if (minutes < 1) {
            return 'just now';
        }
        if (minutes < 60) {
            return `${minutes} min ago`;
        }
        if (minutes < 24 * 60) {
            return `${Math.round(minutes / 60)}h ago`;
        }
        let days = Math.round(minutes / (24 * 60));
        return `${days} day${days === 1 ? '' : 's'} ago`;
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
            let finished = when(run.seconds_ago);
            if (watching) {
                setButton(buttonLabel, true);
                objs.status.textContent = compact ? 'Synced, reloading…' : 'Refreshed, reloading…';
                window.location.reload();
                return;
            } else if (compact) {
                objs.status.textContent = `Synced ${finished}`;
            } else {
                objs.status.textContent = `Last refreshed ${finished} (${run.manual ? 'manual' : 'nightly'})`;
            }
        } else {
            objs.status.classList.add('text-over');
            objs.status.textContent = `${compact ? 'Sync' : 'Last refresh'} failed ${when(run.seconds_ago)}`;
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
