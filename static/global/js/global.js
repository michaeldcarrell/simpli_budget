let getCookie = (name) => {
    let cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        let cookie = cookies[i];
        let trimmed = cookie.trim();
        let parts = trimmed.split('=');
        let key = parts[0];
        let value = parts[1];
        if (key === name) {
            return value;
        }
    }
};

let getQueryParamValue = function(name) {
    let queryParamsObj = {};
    let queryParams = window.location.search.substring(1).split('&');
    queryParams.forEach(function(param) {
        let paramKeyValue = param.split('=');
        queryParamsObj[paramKeyValue[0]] = paramKeyValue[1];
    })
    return queryParamsObj[name];
}

let getCSRFToken = () => {
    return getCookie('csrftoken');
}

class Loader {
    constructor() {
        this.element = document.getElementById('loading-overlay');
    }

    show() {
        this.element.classList.remove('hidden');
    }

    resolve() {
        this.element.classList.add('hidden');
    }
}

let themeController = function() {
    const THEME_COLORS = {dark: '#121417', light: '#f4f5f7'};

    let applyTheme = function(theme) {
        let root = document.documentElement;
        root.setAttribute('data-bs-theme', theme);
        root.classList.toggle('dark', theme === 'dark');  // DataTables keys its dark styles off this class
        let themeColor = document.querySelector('meta[name="theme-color"]');
        if (themeColor) {
            themeColor.setAttribute('content', THEME_COLORS[theme]);
        }
        document.querySelectorAll('.theme-toggle').forEach(function(button) {
            button.dataset.theme = theme;
            button.setAttribute('aria-label', theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme');
        });
    }

    let saveTheme = function(theme, previousTheme) {
        fetch('/api/settings', {
            method: 'PUT',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ theme: theme })
        }).then(res => {
            if (res.status !== 200) {
                throw new Error('Failed to save theme');
            }
        }).catch(e => {
            applyTheme(previousTheme);
            alert(e.message);
        });
    }

    document.querySelectorAll('.theme-toggle').forEach(function(button) {
        button.addEventListener('click', function() {
            let current = document.documentElement.getAttribute('data-bs-theme');
            let next = current === 'dark' ? 'light' : 'dark';
            applyTheme(next);
            saveTheme(next, current);
        });
    });
}();
