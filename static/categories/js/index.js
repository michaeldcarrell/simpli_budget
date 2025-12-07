let controller = function() {
    let objs = {
        amounts: document.getElementsByClassName('amount'),
    };

    let inits = function() {
        let amountMonitors = function() {
            for (let i = 0; i < objs.amounts.length; i++) {
                let ele = objs.amounts[i];
                let amount = parseFloat(ele.value);
                console.log(ele.getAttribute('category-id'));
                let category = new Category(ele.getAttribute('category-id'));
                ele.addEventListener('change', function() {
                    category.update_default_monthly_amount(parseFloat(this.value), this);
                });
            }
        }();
    }();
}();