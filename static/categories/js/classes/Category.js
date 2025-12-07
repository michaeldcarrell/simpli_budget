class Category {
    constructor(id=null, default_month_amount=null) {
        this.id = id
        this.default_month_amount = default_month_amount;
    }

    update_default_monthly_amount(amount, input_ele) {
        let loader = new Loader();
        let token = getCSRFToken();
        loader.show();
        fetch(`/api/category/${this.id}`, {
            method: 'POST',
            body: JSON.stringify({
                default_monthly_amount: amount
            }),
            headers: {
                'X-CSRFToken': token,
                'Content-Type': 'application/json'
            }
        }).then(async (res) => {
            return {
                status_code: res.status,
                body: await res.json()
            }
        }).then(data => {
            if (data.status_code !== 200) {
                alert(`Failed to update Category: \nStatus Code: ${data.status_code}\nBody: ${data.body}`)
                console.log(data);
                input_ele.value = this.default_month_amount;
            } else {
                this.default_month_amount = amount;
            }
            loader.resolve();
        }).catch(e => {
            alert(`Category Update Failed: ${e.message}`)
            input_ele.value = this.default_month_amount;
            loader.resolve();
        })
    }
}