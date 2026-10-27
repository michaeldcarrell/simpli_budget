let controller = function() {
    let objs = {
        generateDemoActivity: document.getElementById('generate-demo-activity'),
    }

    let initHelpTooltips = function() {
        // Touch screens can't hover, and iOS Safari doesn't focus buttons on tap, so
        // there the info icon opens on tap and closes on the next tap anywhere.
        let touchOnly = window.matchMedia('(hover: none)').matches;
        let helpButtons = Array.from(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        helpButtons.forEach(function(el) {
            new bootstrap.Tooltip(el, { trigger: touchOnly ? 'click' : 'hover focus' });
        });
        if (touchOnly) {
            document.addEventListener('click', function(event) {
                helpButtons.forEach(function(el) {
                    if (!el.contains(event.target)) {
                        bootstrap.Tooltip.getInstance(el).hide();
                    }
                });
            });
        }
    }

    let inits = function() {
        initHelpTooltips();

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
