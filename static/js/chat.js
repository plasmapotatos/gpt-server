// Adjust the height of the textarea dynamically
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
    if (input.trim() === '') return;

    console.log("User input:", input);  // Print user input to the console

    let messageContainer = document.createElement('div');
    messageContainer.classList.add('message', 'user-message');
    messageContainer.textContent = input;
    document.getElementById('messages').appendChild(messageContainer);

    // Send the user input via a POST request
    fetch('/send', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: input })
    }).then(response => {
        console.log("Fetch response status:", response.status);  // Print fetch response status
        return response.json();
    }).then(data => {
        //console.log("Fetch response data:", data);  // Print fetch response data
        setupEventSource(); // Initialize EventSource after the fetch request completes
    }).catch(error => {
        console.error("Fetch error:", error);  // Print fetch error
    });

    document.getElementById('input').value = '';
    document.getElementById('input').style.height = 'auto'; // Reset height
}

function setupEventSource() {
    // Set up the EventSource connection
    const eventSource = new EventSource('/chat');

    eventSource.onopen = function () {
        console.log("EventSource connection opened.");  // Log when the connection is opened
    };

    eventSource.onerror = function (error) {
        console.error("EventSource error:", error);  // Log any connection errors
        eventSource.close();  // Close the EventSource connection on error
    };

    let botMessageContainer = null;
    let fullResponse = '';

    eventSource.onmessage = function (event) {
        console.log("Received event data:", event.data);

        if (event.data === '\0') {
            console.log("Received EOT character. Closing EventSource connection.");
            eventSource.close();
            // Update the session with the full assistant response
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
        botMessageContainer.textContent += event.data;
        fullResponse += event.data
        // Scroll to the bottom of the chatbox
        document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
    };
}
