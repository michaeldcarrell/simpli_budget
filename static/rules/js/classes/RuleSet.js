class RuleSet {
    constructor(attributes) {
        this.name = attributes.name;
        this.category_id = attributes.category_id;
        this.id = attributes.id;
        if ((this.name === '' || this.category_id === '') && this.id === undefined) {
            throw new Error('Rule Set Name or Category ID is empty');
        }
    }

    create() {
        let loader = new Loader();
        let token = getCSRFToken();
        loader.show();
        fetch('/api/rule_set', {
            method: 'POST',
            body: JSON.stringify({
                name: this.name,
                category_id: this.category_id
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
            if (data.status_code !== 201) {
                loader.resolve();
                alert(`Failed to create Rule Set: \nStatus Code: ${data.status_code}\nBody: ${data.body}`)
                console.log(data);
            } else {
                loader.resolve();
                window.location.href = `rules/${data.body.set_id}`;
            }
        }).catch(e => {
            alert(`Rule Set Creation Failed: ${e.message}`)
        });
    }

    update_category(category_id) {
        let loader = new Loader();
        let token = getCSRFToken();
        loader.show();

        fetch(`/api/rule_set/${this.id}`, {
            method: 'PUT',
            body: JSON.stringify({
                category_id: category_id
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
                loader.resolve();
                alert(`Failed to update Rule Set: \nStatus Code: ${data.status_code}\nBody: ${data.body}`)
                console.log(data);
            } else {
                window.location.reload();
            }
        }).catch(e => {
            alert(`Rule Set Update Failed: ${e.message}`)
            loader.resolve();
        })
    }
}