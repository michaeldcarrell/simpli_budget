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