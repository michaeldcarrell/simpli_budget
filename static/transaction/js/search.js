let controller = async function() {
    let budget = new Budget();
    console.log(budget.transactions);
    let objs = {
        dataTable: new DataTable('#transactions-table', {
            serverSide: true,
            processing: true,
            paging: true,
            pageLength: 10,
            search: {
                return: true
            },
            order: [[0, 'desc']],
            layout: {
                topStart: 'buttons'
            },
            buttons: [
                {
                    text: 'Export',
                    action: async function(e, dt) {
                        const filters = {};
                        dt.columns().every(function() {
                            const searchValue = this.search();
                            if (searchValue) {
                                filters[this.dataSrc()] = searchValue;
                            }
                        });

                        let order_by = {};
                        const order = dt.order();
                        if (order && order.length > 0) {
                            order_by.column = dt.column(order[0][0]).dataSrc();
                            order_by.direction = order[0][1];
                        }

                        const columns = [
                            {data: 'date', title: 'Date'},
                            {data: 'name', title: 'Name'},
                            {data: 'amount', title: 'Amount'},
                            {data: 'account', title: 'Account'},
                            {data: 'category', title: 'Category'},
                            {data: 'tags', title: 'Tags'}
                        ];
                        const escapeCsv = function(value) {
                            const stringValue = value === null || value === undefined ? '' : String(value);
                            return `"${stringValue.replace(/"/g, '""')}"`;
                        };
                        const rows = [columns.map(column => escapeCsv(column.title)).join(',')];

                        const totalRecords = dt.page.info().recordsDisplay;
                        if (totalRecords > 0) {
                            const response = await budget.searchTransactions(1, totalRecords, filters, order_by);
                            response.transactions.forEach(transaction => {
                                rows.push(columns.map(column => escapeCsv(transaction[column.data])).join(','));
                            });
                        }

                        const blob = new Blob([rows.join('\n')], {type: 'text/csv;charset=utf-8;'});
                        const url = URL.createObjectURL(blob);
                        const link = document.createElement('a');
                        link.href = url;
                        link.download = 'Transactions.csv';
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        URL.revokeObjectURL(url);
                    }
                }
            ],
            columns: [
                {data: 'date', title: 'Date'},
                {data: 'name', title: 'Name'},
                {data: 'amount', title: 'Amount'},
                {data: 'account', title: 'Account'},
                {data: 'category', title: 'Category'},
                {data: 'tags', title: 'Tags'}
            ],
            ajax: async function(data, callback, settings) {
                const page = (data.start / data.length) + 1;

                const filters = {};
                data.columns.forEach(column => {
                    if (column.search.value) {
                        filters[column.data] = column.search.value;
                    }
                })

                let order_by = {};
                if (data.order && data.order.length > 0) {
                    const orderItem = data.order[0]; // Get the primary sort column
                    order_by.column = data.columns[orderItem.column].data;
                    order_by.direction = orderItem.dir;
                }

                const response = await budget.searchTransactions(page, data.length, filters, order_by);

                callback({
                    draw: data.draw,
                    recordsTotal: response.paging.total_records,
                    recordsFiltered: response.paging.total_records,
                    data: response.transactions
                })
            },
            initComplete: function() {
                this.api()
                    .columns()
                    .every(function() {
                        let column = this;
                        let title = column.footer().textContent;

                        let input = document.createElement("input");
                        input.placeholder = title;
                        column.footer().replaceChildren(input);

                        if (title === 'Date') {
                            $(input).daterangepicker({
                                autoUpdateInput: false,
                                locale: {
                                    cancelLabel: 'Clear'
                                }
                            });

                            $(input).on('apply.daterangepicker', function(ev, picker) {
                                $(this).val(picker.startDate.format('MM/DD/YYYY') + ' - ' + picker.endDate.format('MM/DD/YYYY'));
                                column.search($(this).val()).draw();
                            });

                            $(input).on('cancel.daterangepicker', function(ev, picker) {
                                $(this).val('');
                                column.search($(this).val()).draw();
                            });
                        }
                        else if (['Account', 'Tags'].includes(title)) {
                            let selectorId = title.toLowerCase();
                            let selector = document.getElementById(`${selectorId}-template`).cloneNode(true);
                            selector.removeAttribute('id');
                            column.footer().replaceChildren(selector);

                            selector.addEventListener('change', function(e) {
                                if (column.search() !== this.value) {
                                    column.search(this.value).draw();
                                }
                            });
                        }
                        else if (title === 'Category') {
                            let selector = document.getElementById('category-template').cloneNode(true);
                            selector.removeAttribute('id');
                            column.footer().replaceChildren(selector);

                            selector.addEventListener('change', function(e) {
                                if (column.search() !== this.value) {
                                    column.search(this.value).draw();
                                }
                            });
                        }
                        else {
                            input.addEventListener('keyup', function(e) {
                                if (e.key === 'Enter') {
                                    if (column.search() !== this.value) {
                                        column.search(this.value).draw();
                                    }
                                }
                            });
                        }
                    })
            }
        })
    }
    let init = function() {

    }();
}();