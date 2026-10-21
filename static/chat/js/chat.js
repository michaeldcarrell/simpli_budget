let chatController = function() {
    let objs = {
        messages: document.getElementById('chat-messages'),
        emptyHint: document.getElementById('chat-empty-hint'),
        form: document.getElementById('chat-form'),
        input: document.getElementById('chat-input'),
        sendBtn: document.getElementById('chat-send-btn'),
        resetBtn: document.getElementById('chat-reset-btn'),
    }

    // The conversation is kept on the server, so it follows the user across pages; it's fetched the first
    // time the panel opens on each page.
    let loaded = false;
    let busy = false;

    let renderMarkdown = function(element, text) {
        element.innerHTML = DOMPurify.sanitize(marked.parse(text));
        element.querySelectorAll('table').forEach(table => table.classList.add('table', 'table-sm'));
    }

    let addBubble = function(role) {
        objs.emptyHint.classList.add('hidden');
        let bubble = document.createElement('div');
        bubble.classList.add('chat-bubble', `chat-bubble-${role}`);
        objs.messages.appendChild(bubble);
        return bubble;
    }

    let scrollToBottom = function() {
        objs.messages.scrollTop = objs.messages.scrollHeight;
    }

    let setBusy = function(value) {
        busy = value;
        objs.sendBtn.disabled = value;
        objs.resetBtn.disabled = value;
    }

    let addError = function(bubble, text) {
        let error = document.createElement('div');
        error.classList.add('text-danger', 'small', 'mt-1');
        error.textContent = text;
        bubble.appendChild(error);
    }

    let clearMessages = function() {
        objs.messages.querySelectorAll('.chat-bubble').forEach(bubble => bubble.remove());
        objs.emptyHint.classList.remove('hidden');
    }

    let groupQuery = function() {
        let groupId = getQueryParamValue('group_id');
        return groupId ? `?group_id=${encodeURIComponent(groupId)}` : '';
    }

    let send = async function(text) {
        setBusy(true);
        addBubble('user').textContent = text;

        let bubble = addBubble('assistant');
        let body = document.createElement('div');
        let status = document.createElement('div');
        status.classList.add('chat-status', 'text-body-secondary', 'small');
        status.textContent = 'Thinking...';
        bubble.append(body, status);
        scrollToBottom();

        let answer = '';
        let newParagraph = false;

        let handleEvent = function(event) {
            if (event.type === 'text') {
                if (newParagraph && answer) {
                    answer += '\n\n';
                }
                newParagraph = false;
                answer += event.text;
                renderMarkdown(body, answer);
            } else if (event.type === 'status') {
                // Text before a tool call is a separate thought from the text after it.
                newParagraph = true;
                status.textContent = `${event.text}...`;
                return;
            } else if (event.type === 'error') {
                addError(bubble, event.text);
            }
            status.textContent = '';
            scrollToBottom();
        }

        try {
            let res = await fetch(`/api/chat${groupQuery()}`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken(),
                    'Content-Type': 'application/json'
                },
                // Lets the assistant read "this month"/"this category" as whatever page is open.
                body: JSON.stringify({
                    message: text,
                    page: {path: window.location.pathname, month: getQueryParamValue('month') || null},
                })
            });
            if (!res.ok) {
                let data = await res.json().catch(() => ({}));
                handleEvent({type: 'error', text: data.message || 'Something went wrong. Please try again.'});
            } else {
                let reader = res.body.getReader();
                let decoder = new TextDecoder();
                let buffer = '';
                while (true) {
                    let {value, done} = await reader.read();
                    if (done) {
                        break;
                    }
                    buffer += decoder.decode(value, {stream: true});
                    let lines = buffer.split('\n');
                    buffer = lines.pop();
                    lines.filter(line => line.trim()).forEach(line => handleEvent(JSON.parse(line)));
                }
            }
        } catch (e) {
            handleEvent({type: 'error', text: 'Lost connection to the assistant. Please try again.'});
        }

        status.remove();
        setBusy(false);
        objs.input.focus();
    }

    objs.form.addEventListener('submit', function(e) {
        e.preventDefault();
        let text = objs.input.value.trim();
        if (!text || busy) {
            return;
        }
        objs.input.value = '';
        send(text);
    });

    objs.input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            objs.form.requestSubmit();
        }
    });

    let load = async function() {
        loaded = true;
        setBusy(true);
        try {
            let res = await fetch(`/api/chat${groupQuery()}`);
            if (!res.ok) {
                throw new Error(res.statusText);
            }
            let data = await res.json();
            if (data.messages.length) {
                clearMessages();
            }
            data.messages.forEach(message => {
                let bubble = addBubble(message.role);
                if (message.role === 'user') {
                    bubble.textContent = message.content;
                    return;
                }
                if (message.content) {
                    let body = document.createElement('div');
                    renderMarkdown(body, message.content);
                    bubble.appendChild(body);
                }
                if (message.error) {
                    addError(bubble, message.error);
                }
            });
            scrollToBottom();
        } catch (e) {
            // Try again next time the panel opens.
            loaded = false;
        }
        setBusy(false);
    }

    objs.resetBtn.addEventListener('click', async function() {
        setBusy(true);
        await fetch(`/api/chat${groupQuery()}`, {
            method: 'DELETE',
            headers: {'X-CSRFToken': getCSRFToken()},
        }).catch(() => {});
        clearMessages();
        setBusy(false);
        objs.input.focus();
    });

    let panel = document.getElementById('chat-panel');
    panel.addEventListener('show.bs.offcanvas', () => { if (!loaded) { load(); } });
    panel.addEventListener('shown.bs.offcanvas', () => objs.input.focus());
}

chatController();
