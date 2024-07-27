import time
from flask import Flask, request, jsonify, render_template, Response, session
from openai import OpenAI
import os
import traceback

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management

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
        for chunk in response:
            if chunk.choices:
                message = chunk.choices[0].delta.content
                yield f"data: {message}\n\n"
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

    return jsonify({"status": "Message received", "message": session['history']})

@app.route('/chat', methods=['GET'])
def chat():
    # Use session history for the stream response
    return Response(stream_response(session['history']), mimetype='text/event-stream')
if __name__ == '__main__':
    app.run(debug=True)
