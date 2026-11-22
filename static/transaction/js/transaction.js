let controller = function() {
    let objs = {
        "categorySelector": document.getElementById('category'),
        "tagSelector": document.getElementById('tags'),
        "splitData": document.getElementById('split-data'),
        "splitSheet": document.getElementById('split-sheet'),
        "splitForm": document.getElementById('split-form'),
        "splitLines": document.getElementById('split-lines'),
        "splitLineTemplate": document.getElementById('split-line-template'),
        "splitAddLine": document.getElementById('split-add-line'),
        "splitRemainingName": document.getElementById('split-remaining-name'),
        "splitRemainingAmount": document.getElementById('split-remaining-amount'),
        "splitError": document.getElementById('split-error'),
        "splitRemove": document.getElementById('split-remove'),
    }
    // Present only on a split transaction; changing its category then reloads to show the new split.
    let isSplit = objs.splitRemove !== null;

    let getTransactionId = function() {
        let path = window.location.pathname.split('/');
        return path[path.length - 1];
    }

    let updateTransaction = function() {
        let category_id = objs.categorySelector.value;
        let transaction_id = getTransactionId();
        let transaction = new Transaction(transaction_id);
        transaction.setCategory(category_id, isSplit);
    }

    // --- Split sheet ---------------------------------------------------------------------------
    // Amounts are worked in cents so the "what's left" figure matches the server to the penny.
    let toCents = function(raw) {
        let cleaned = String(raw).replace(/[$,\s]/g, '');
        if (cleaned === '' || isNaN(Number(cleaned))) {
            return null;
        }
        return Math.round(Number(cleaned) * 100);
    }

    let formatCents = function(cents) {
        let sign = cents < 0 ? '-' : '';
        return `${sign}$${(Math.abs(cents) / 100).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    }

    let splitTotalCents = function() {
        return Math.round(JSON.parse(objs.splitData.textContent).total * 100);
    }

    let addSplitLine = function(line) {
        let row = objs.splitLineTemplate.content.firstElementChild.cloneNode(true);
        let select = row.querySelector('.split-line-category');
        let amount = row.querySelector('.split-line-amount');
        // The transaction's own category gets what's left, so it can't also be a line.
        let primary = select.querySelector(`option[value="${objs.categorySelector.value}"]`);
        if (primary) {
            primary.remove();
        }
        if (line) {
            select.value = String(line.category_id);
            amount.value = line.amount;
        }
        select.addEventListener('change', updateRemaining);
        amount.addEventListener('input', updateRemaining);
        row.querySelector('.split-line-remove').addEventListener('click', function() {
            row.remove();
            updateRemaining();
        });
        objs.splitLines.appendChild(row);
        return row;
    }

    let readSplitLines = function() {
        return Array.from(objs.splitLines.querySelectorAll('.split-line')).map(row => ({
            category_id: row.querySelector('.split-line-category').value,
            amount: row.querySelector('.split-line-amount').value,
        }));
    }

    let updateRemaining = function() {
        let used = readSplitLines().reduce((sum, line) => sum + (toCents(line.amount) || 0), 0);
        let remaining = splitTotalCents() - used;
        objs.splitRemainingAmount.textContent = formatCents(remaining);
        objs.splitRemainingAmount.closest('.split-remaining').classList.toggle('is-over', remaining < 0);
        return remaining;
    }

    let showSplitError = function(message) {
        objs.splitError.textContent = message;
        objs.splitError.classList.toggle('d-none', !message);
    }

    let openSplitSheet = function() {
        objs.splitLines.replaceChildren();
        showSplitError('');
        let saved = JSON.parse(objs.splitData.textContent).lines;
        if (saved.length) {
            saved.forEach(addSplitLine);
        } else {
            addSplitLine();
        }
        let selected = objs.categorySelector.options[objs.categorySelector.selectedIndex];
        objs.splitRemainingName.textContent = selected ? selected.textContent.trim() : 'Uncategorized';
        updateRemaining();
    }

    let saveSplit = function(event) {
        event.preventDefault();
        let lines = readSplitLines();
        let seen = new Set();
        for (let line of lines) {
            if (!line.category_id) {
                return showSplitError('Pick a category for every line.');
            }
            if (seen.has(line.category_id)) {
                return showSplitError('Each category can only appear once.');
            }
            seen.add(line.category_id);
            let cents = toCents(line.amount);
            if (cents === null || cents <= 0) {
                return showSplitError('Every line needs an amount greater than 0.');
            }
        }
        if (updateRemaining() < 0) {
            return showSplitError('The lines add up to more than the transaction.');
        }
        let transaction = new Transaction(getTransactionId());
        let save = lines.length
            ? transaction.setSplits(lines.map(line => ({category_id: parseInt(line.category_id), amount: line.amount})))
            : transaction.clearSplits();
        save.then(() => window.location.reload())
            .catch(e => showSplitError(e.message));
    }

    let removeSplit = function() {
        if (!confirm('Unsplit this transaction? All of it goes back to its category.')) {
            return;
        }
        new Transaction(getTransactionId()).clearSplits()
            .then(() => window.location.reload())
            .catch(e => alert(e.message));
    }

    let updateTags = function() {
        let tag_ids = $('#tags').val().map(id => parseInt(id));
        let transaction = new Transaction(getTransactionId());
        transaction.setTags(tag_ids);
    }

    let init = function() {
        // "Back" returns to wherever the user came from in the app (search results, a category, ...).
        let back = document.getElementById('transaction-back');
        if (back && document.referrer.startsWith(window.location.origin)) {
            back.addEventListener('click', function(event) {
                event.preventDefault();
                history.back();
            });
        }

        objs.categorySelector.addEventListener('change', function() {
            updateTransaction()
        });

        $('#tags').on('changed.bs.select', function(e, clickedIndex, isSelected, previousValue) {
            updateTags();
        });

        // The split sheet is left out for the read-only demo user and for pending transactions.
        if (objs.splitSheet) {
            objs.splitSheet.addEventListener('show.bs.offcanvas', openSplitSheet);
            objs.splitAddLine.addEventListener('click', function() {
                addSplitLine().querySelector('.split-line-category').focus();
            });
            objs.splitForm.addEventListener('submit', saveSplit);
        }
        if (objs.splitRemove) {
            objs.splitRemove.addEventListener('click', removeSplit);
        }
    }();
}();