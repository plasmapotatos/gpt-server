document.getElementById('input').addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});

document.getElementById('send').addEventListener('click', submit);

document.getElementById('input').addEventListener('keydown', function (e) {
    if (e.keyCode === 13 && !e.shiftKey) {
        e.preventDefault();
        submit();
    }
});

function submit() {
    let input = document.getElementById('input').value;
    let file = document.getElementById('file').files[0];
    if (input.trim() === '' && !file) return;

    console.log("User input:", input);

    let messageContainer = document.createElement('div');
    messageContainer.classList.add('message', 'user-message');
    messageContainer.textContent = input;
    document.getElementById('messages').appendChild(messageContainer);

    let formData = new FormData();
    formData.append('message', input);
    if (file) {
        formData.append('file', file);
        console.log("File uploaded:", file.name);
    }

    fetch('/send', {
        method: 'POST',
        body: formData
    }).then(response => {
        console.log("Fetch response status:", response.status);
        return response.json();
    }).then(data => {
        setupEventSource();
    }).catch(error => {
        console.error("Fetch error:", error);
    });

    document.getElementById('input').value = '';
    document.getElementById('input').style.height = 'auto';
    document.getElementById('file').value = ''; // Reset file input
}

function decodeBase64(text) {
    return atob(text);
}

function setupEventSource() {
    const eventSource = new EventSource('/chat');

    eventSource.onopen = function () {
        console.log("EventSource connection opened.");
    };

    eventSource.onerror = function (error) {
        console.error("EventSource error:", error);
        eventSource.close();
    };

    let botMessageContainer = null;
    let fullResponse = '';

    eventSource.onmessage = function (event) {
        console.log("Received event data:", event.data);

        event.data.replace(/\n/g, '<br>');

        if (event.data === '') {
            console.log("Received empty string. Replacing with newline.");
            event.data = '\n';
        }

        if (event.data === '\0') {
            console.log("Received EOT character. Closing EventSource connection.");
            eventSource.close();
            fetch('/update_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ response: fullResponse })
            }).then(response => response.json())
                .then(data => console.log("Session update response:", data))
                .catch(error => console.error("Session update error:", error));
            return;
        }

        if (!botMessageContainer) {
            botMessageContainer = document.createElement('div');
            botMessageContainer.classList.add('message', 'bot-message');
            document.getElementById('messages').appendChild(botMessageContainer);
        }
        // Decode the base64-encoded data
        const decodedResponse = JSON.parse(event.data);

        // Append the decoded data to the full response
        fullResponse += decodedResponse;
        console.log(fullResponse)
        //fullResponse += event.data
        //fullResponse = fullResponse.replace("\\n", '<br>');
        
        fullResponse = fullResponse.replace(/\\n/g, '<br>');
        botMessageContainer.innerHTML = `<pre>${fullResponse}</pre>`;
        document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
    };
}
