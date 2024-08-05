import time
import json
from flask import Flask, request, jsonify, render_template, Response, session
from flask_session import Session
from orjson import orjson
from openai import OpenAI
import os
import traceback
from datetime import timedelta
import base64

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management
app.config['SESSION_TYPE'] = 'filesystem'  # Store session data on the filesystem
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Set session lifetime
app.config['UPLOAD_FOLDER'] = 'uploads'  # Folder to store uploaded files
full_response = ''
Session(app)

# Set your API key here
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@app.route('/')
def home():
    return render_template('index.html')

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
    
def encode_base64(text):
    return base64.b64encode(text.encode('utf-8')).decode('utf-8')

def decode_base64(text):
    return base64.b64decode(text.encode('utf-8')).decode('utf-8')

def encode_json(text):
    return json.dumps(text)

def decode_json(text):
    return json.loads(text)

def stream_response(messages):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0,
            stream=True,  # Enable streaming mode
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
                if content:
                    full_response += content
                    content = content.replace('\n', '\\n')  # Replace newlines with a special sequence
                    encoded_content = encode_json(content)
                    #encoded_content = encode_base64(content)
                    yield f"data: {encoded_content}\n\n"
                    # yield f"data: {content}\n\n"
                    # if content == '\\n':
                    #     print("Yielded newline")
        print(f"Full response: {full_response}")
    except Exception as e:
        error_message = traceback.format_exc()  # Get the full traceback
        print(f"Error: {str(e)}")
        print(f"Traceback:\n{error_message}")
        yield f"data: Error: {str(e)}\n\n"

@app.route('/send', methods=['POST'])
def send_message():
    user_input = request.form.get('message')
    print(f"User input: {user_input}")  # Log the user input

    file = request.files.get('file')
    if file and file.filename != '':
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        base64_image = encode_image(file_path)
        user_input += f"\n[File uploaded: {file.filename}]"
        image_message = {
            "role": "user",
            "content": [
                {"type": "text", "text": user_input},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{base64_image}"}
                }
            ]
        }
    else:
        image_message = {"role": "user", "content": user_input}
    
    # Initialize session history if not already present
    if 'history' not in session:
        print("Session history not found. Initializing.")
        session['history'] = [{"role": "system", "content": "You are a helpful assistant."}]
    
    # Add the user's message to the history
    session['history'].append(image_message)
    session.modified = True  # Mark the session as modified
    #print(f"Session history: {session['history'][:50]}")

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
        #print(f"Updated session history: {session['history'][:50]}")  # Debug statement
        return jsonify({"status": "Session updated"})
    else:
        return jsonify({"error": "No history found in session"}), 400

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
