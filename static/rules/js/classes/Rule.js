class Rule {
    constructor(set_id, match_string, match_number, match_type_id) {
        this.set_id = set_id;
        this.match_string = match_string;
        this.match_number = match_number;
        this.match_type_id = match_type_id;
    }

    create() {
        let loader = new Loader();
        let token = getCSRFToken();
        loader.show();

        fetch(`/api/rule_set/${this.set_id}/rule`, {
            method: 'POST',
            body: JSON.stringify({
                match_string: this.match_string,
                match_number: this.match_number,
                match_type_id: this.match_type_id
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
                alert(`Failed to create Rule: \nStatus Code: ${data.status_code}\nBody: ${data.body}`)
                console.log(data);
            } else {
                window.location.reload();
            }
        }).catch(e => {
            alert(`Rule Creation Failed: ${e.message}`)
        })
    }
}