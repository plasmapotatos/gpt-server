import time
from flask import Flask, request, jsonify, render_template, Response, session
from openai import OpenAI
import os
import traceback
from datetime import timedelta

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management
app.config['SESSION_TYPE'] = 'filesystem'  # Store session data on the filesystem
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Set session lifetime
full_response = ''
# Set your API key here
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@app.route('/')
def home():
    return render_template('index.html')

def stream_response(messages):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0,
            stream=True, # Enable streaming mode
        )
        global full_response
        full_response = ''
        skip = 0
        for chunk in response:
            skip += 1
            if skip < 2:
                continue
            if chunk.choices:
                delta = chunk.choices[0].delta
                content = delta.content if delta.content else '\0'
                print(f"Content: {content}")
                if content:
                    full_response += content
                    yield f"data: {content}\n\n"
        print(f"Full response: {full_response}")
        # Store the full response in the session history
    except Exception as e:
        error_message = traceback.format_exc()  # Get the full traceback
        print(f"Error: {str(e)}")
        print(f"Traceback:\n{error_message}")
        yield f"data: Error: {str(e)}\n\n"


@app.route('/send', methods=['POST'])
def send_message():
    user_input = request.json.get('message')
    print(f"User input: {user_input}")  # Log the user input

    # Initialize session history if not already present
    if 'history' not in session:
        print("Session history not found. Initializing.")
        session['history'] = [{"role": "system", "content": "You are a helpful assistant."}]
    # Add the user's message to the history
    session['history'].append({"role": "user", "content": user_input})
    session.modified = True  # Mark the session as modified
    print(f"Session history: {session['history']}")

    return jsonify({"status": "Message received", "message": session['history']})

@app.route('/chat', methods=['GET'])
def chat():
    # Use session history for the stream response
    return Response(stream_response(session['history']), mimetype='text/event-stream')

@app.route('/update_session', methods=['POST'])
def update_session():
    assistant_response = request.json.get('response')
    print(f"Assistant response: {assistant_response}")  # Log the assistant response

    if 'history' in session:
        session['history'].append({"role": "assistant", "content": assistant_response})
        session.modified = True  # Ensure session changes are saved
        print(f"Updated session history: {session['history']}")  # Debug statement
        return jsonify({"status": "Session updated"})
    else:
        return jsonify({"error": "No history found in session"}), 400
if __name__ == '__main__':
    app.run(debug=True)
