let controller = function() {
    const PAGE_SIZE = 50;
    // URL query params this page reads and writes, so a filtered view can be bookmarked or shared.
    const PARAMS = ['q', 'start', 'end', 'category', 'account', 'tag'];

    let budget = new Budget();
    let objs = {
        summary: document.getElementById('tx-summary'),
        exportButton: document.getElementById('tx-export'),
        searchForm: document.getElementById('tx-search-form'),
        searchInput: document.getElementById('tx-search'),
        chipMonth: document.getElementById('tx-chip-month'),
        chipUncategorized: document.getElementById('tx-chip-uncategorized'),
        filterCount: document.getElementById('tx-filter-count'),
        list: document.getElementById('tx-list'),
        empty: document.getElementById('tx-empty'),
        more: document.getElementById('tx-more'),
        filterSheet: document.getElementById('tx-filter-sheet'),
        filterForm: document.getElementById('tx-filter-form'),
        filterClear: document.getElementById('tx-filter-clear'),
        filterStart: document.getElementById('tx-filter-start'),
        filterEnd: document.getElementById('tx-filter-end'),
        filterCategory: document.getElementById('tx-filter-category'),
        filterAccount: document.getElementById('tx-filter-account'),
        filterTag: document.getElementById('tx-filter-tag'),
    }

    let state = {};
    let page = 0;
    let totalRecords = 0;
    let loadedCount = 0;
    let requestId = 0;
    // Day sections already on screen, keyed by ISO date, so the next page can append into them.
    let days = {};

    let readStateFromUrl = function() {
        let params = new URLSearchParams(window.location.search);
        state = {};
        PARAMS.forEach(key => { state[key] = params.get(key) || ''; });
    }

    let writeStateToUrl = function() {
        let params = new URLSearchParams();
        PARAMS.forEach(key => { if (state[key]) params.set(key, state[key]); });
        let query = params.toString();
        history.replaceState(null, '', query ? `${window.location.pathname}?${query}` : window.location.pathname);
    }

    let isoToApiDate = function(iso) {
        let [year, month, day] = iso.split('-');
        return `${month}/${day}/${year}`;
    }

    // The search API takes the same filter keys the old DataTables page sent.
    let apiFilters = function() {
        let filters = {};
        if (state.q) filters['name'] = state.q;
        if (state.start || state.end) {
            let start = state.start ? isoToApiDate(state.start) : '01/01/1900';
            let end = state.end ? isoToApiDate(state.end) : '12/31/2999';
            filters['date'] = `${start} - ${end}`;
        }
        if (state.category !== '') filters['category.category_name'] = state.category;
        if (state.account) filters['account'] = state.account;
        if (state.tag) filters['tags'] = state.tag;
        return filters;
    }

    let currentMonthRange = function() {
        let now = new Date();
        let pad = n => String(n).padStart(2, '0');
        let last = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
        let prefix = `${now.getFullYear()}-${pad(now.getMonth() + 1)}`;
        return {start: `${prefix}-01`, end: `${prefix}-${pad(last)}`};
    }

    let parseAmount = function(text) {
        return Number(String(text).replace(/[$,]/g, ''));
    }

    let formatNumber = function(value) {
        return Math.abs(value).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    }

    let dayLabel = function(iso) {
        let date = new Date(`${iso}T00:00:00`);
        let label = date.toLocaleDateString('en-US', {weekday: 'short', month: 'short', day: 'numeric'});
        let today = new Date();
        today.setHours(0, 0, 0, 0);
        let diff = Math.round((today - date) / 86400000);
        if (diff === 0) return `Today · ${label}`;
        if (diff === 1) return `Yesterday · ${label}`;
        if (date.getFullYear() !== today.getFullYear()) {
            return date.toLocaleDateString('en-US', {weekday: 'short', month: 'short', day: 'numeric', year: 'numeric'});
        }
        return label;
    }

    let el = function(tag, className, text) {
        let node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined) node.textContent = text;
        return node;
    }

    let daySection = function(iso) {
        if (days[iso]) {
            return days[iso];
        }
        let section = el('section', 'tx-day');
        let header = el('div', 'tx-day-header');
        header.appendChild(el('h2', 'eyebrow m-0', dayLabel(iso)));
        let total = el('span', 'num small text-body-secondary');
        header.appendChild(total);
        section.appendChild(header);
        objs.list.appendChild(section);
        days[iso] = {section: section, total: total, out: 0};
        return days[iso];
    }

    let renderTransaction = function(transaction) {
        let day = daySection(transaction.date);
        let amount = parseAmount(transaction.amount);
        let inflow = amount < 0;
        if (!inflow) {
            day.out += amount;
            day.total.textContent = `${formatNumber(day.out)} out`;
        }

        let row = el('a', 'tx-row');
        row.href = `/transaction/${transaction.id}`;
        row.appendChild(el('span', 'tx-name', transaction.name));
        row.appendChild(el('span', 'tx-amount' + (inflow ? ' inflow' : ''), (inflow ? '+' : '') + formatNumber(amount)));
        let uncategorized = !transaction.category || transaction.category === 'Uncategorized';
        let meta = [transaction.category || 'Uncategorized', transaction.account].filter(Boolean).join(' · ');
        row.appendChild(el('span', 'tx-meta' + (uncategorized ? ' uncategorized' : ''), meta));
        row.appendChild(el('span', 'tx-tags', transaction.tags || ''));
        day.section.appendChild(row);
    }

    let describeFilters = function() {
        let parts = [`${totalRecords.toLocaleString('en-US')} transaction${totalRecords === 1 ? '' : 's'}`];
        let format = iso => new Date(`${iso}T00:00:00`).toLocaleDateString('en-US', {month: 'short', day: 'numeric', year: 'numeric'});
        if (state.start && state.end) parts.push(`${format(state.start)} – ${format(state.end)}`);
        else if (state.start) parts.push(`from ${format(state.start)}`);
        else if (state.end) parts.push(`through ${format(state.end)}`);
        return parts.join(' · ');
    }

    let syncControls = function() {
        objs.searchInput.value = state.q;
        let month = currentMonthRange();
        objs.chipMonth.setAttribute('aria-pressed', String(state.start === month.start && state.end === month.end));
        objs.chipUncategorized.setAttribute('aria-pressed', String(state.category === '0'));

        let count = (state.start || state.end ? 1 : 0) + (state.category !== '' ? 1 : 0) + (state.account ? 1 : 0) + (state.tag ? 1 : 0);
        objs.filterCount.textContent = count;
        objs.filterCount.classList.toggle('hidden', count === 0);

        objs.filterStart.value = state.start;
        objs.filterEnd.value = state.end;
        objs.filterCategory.value = state.category;
        objs.filterAccount.value = state.account;
        objs.filterTag.value = state.tag;
    }

    let loadPage = async function() {
        let thisRequest = ++requestId;
        objs.more.disabled = true;
        let response = await budget.searchTransactions(page + 1, PAGE_SIZE, apiFilters(), {column: 'date', direction: 'desc'});
        if (thisRequest !== requestId || !response.transactions) {
            return;  // a newer search replaced this one, or the request failed (Budget already alerted)
        }
        page += 1;
        totalRecords = response.paging.total_records;
        response.transactions.forEach(renderTransaction);
        loadedCount += response.transactions.length;

        objs.summary.textContent = describeFilters();
        objs.empty.classList.toggle('hidden', totalRecords > 0);
        objs.more.classList.toggle('hidden', !response.paging.has_next_page);
        objs.more.disabled = false;
        objs.more.textContent = `Load more (${loadedCount.toLocaleString('en-US')} of ${totalRecords.toLocaleString('en-US')})`;
    }

    let reload = function() {
        page = 0;
        loadedCount = 0;
        days = {};
        objs.list.replaceChildren();
        objs.summary.textContent = 'Loading…';
        objs.more.classList.add('hidden');
        objs.empty.classList.add('hidden');
        writeStateToUrl();
        syncControls();
        loadPage();
    }

    let exportCsv = async function() {
        let columns = [
            {data: 'date', title: 'Date'},
            {data: 'name', title: 'Name'},
            {data: 'amount', title: 'Amount'},
            {data: 'account', title: 'Account'},
            {data: 'category', title: 'Category'},
            {data: 'tags', title: 'Tags'}
        ];
        let escapeCsv = function(value) {
            let text = value === null || value === undefined ? '' : String(value);
            return `"${text.replace(/"/g, '""')}"`;
        };
        let rows = [columns.map(column => escapeCsv(column.title)).join(',')];
        if (totalRecords > 0) {
            let loader = new Loader();
            loader.show();
            let response = await budget.searchTransactions(1, totalRecords, apiFilters(), {column: 'date', direction: 'desc'});
            loader.resolve();
            (response.transactions || []).forEach(transaction => {
                rows.push(columns.map(column => escapeCsv(transaction[column.data])).join(','));
            });
        }

        let blob = new Blob([rows.join('\n')], {type: 'text/csv;charset=utf-8;'});
        let url = URL.createObjectURL(blob);
        let link = document.createElement('a');
        link.href = url;
        link.download = 'Transactions.csv';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    let inits = function() {
        readStateFromUrl();

        objs.searchForm.addEventListener('submit', function(event) {
            event.preventDefault();
            state.q = objs.searchInput.value.trim();
            objs.searchInput.blur();
            reload();
        });
        // Clearing the field with the search box's own "x" should show everything again.
        objs.searchInput.addEventListener('search', function() {
            if (objs.searchInput.value === '' && state.q) {
                state.q = '';
                reload();
            }
        });

        objs.chipMonth.addEventListener('click', function() {
            let month = currentMonthRange();
            let active = state.start === month.start && state.end === month.end;
            state.start = active ? '' : month.start;
            state.end = active ? '' : month.end;
            reload();
        });

        objs.chipUncategorized.addEventListener('click', function() {
            state.category = state.category === '0' ? '' : '0';
            reload();
        });

        objs.filterForm.addEventListener('submit', function(event) {
            event.preventDefault();
            state.start = objs.filterStart.value;
            state.end = objs.filterEnd.value;
            state.category = objs.filterCategory.value;
            state.account = objs.filterAccount.value;
            state.tag = objs.filterTag.value;
            bootstrap.Offcanvas.getOrCreateInstance(objs.filterSheet).hide();
            reload();
        });

        objs.filterClear.addEventListener('click', function() {
            PARAMS.forEach(key => { if (key !== 'q') state[key] = ''; });
            bootstrap.Offcanvas.getOrCreateInstance(objs.filterSheet).hide();
            reload();
        });

        objs.more.addEventListener('click', loadPage);
        objs.exportButton.addEventListener('click', exportCsv);

        reload();
    }();
}();
