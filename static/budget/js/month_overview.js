let controller = function() {
    let objs = {
        nextMonth: document.getElementById('next-month'),
        lastMonth: document.getElementById('last-month')
    }
    let inits = function() {
        objs.nextMonth.addEventListener('click', function() {
            let href = this.getAttribute('data-href');
            window.location.href = href;
        });

        objs.lastMonth.addEventListener('click', function() {
            let href = this.getAttribute('data-href');
            window.location.href = href;
        });
    }();
}();