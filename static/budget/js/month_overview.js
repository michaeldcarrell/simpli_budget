let controller = function() {
    let objs = {
        generateDemoActivity: document.getElementById('generate-demo-activity'),
    }

    let inits = function() {
        if (objs.generateDemoActivity) {
            objs.generateDemoActivity.addEventListener('click', function() {
                let token = getCSRFToken();
                let loader = new Loader();
                loader.show();
                fetch('/api/demo/generate_activity', {
                    method: 'POST',
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
                        alert(`Failed to generate activity: \nStatus Code: ${data.status_code}\nBody: ${JSON.stringify(data.body)}`);
                        return;
                    }
                    window.location.reload();
                }).catch(e => {
                    loader.resolve();
                    alert(`Failed to generate activity: ${e.message}`);
                    throw e;
                });
            });
        }
    }();
}();
