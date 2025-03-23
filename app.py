from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, Response
from pytoon.animator import animate
from moviepy.editor import VideoFileClip
from gtts import gTTS
import os
from dotenv import load_dotenv
from google import genai  # Importing Google GenAI SDK
from io import BytesIO
from PIL import Image
import base64
import threading
import speech_recognition as sr  # Import the speech recognition library
import re  # Import the regular expression module
from flask_session import Session  # Import Flask-Session for server-side sessions
from cohere import Client as CohereClient  # Import Cohere SDK

# Load environment variables from .env file
load_dotenv()

# Get the Gemini API key from the environment
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Initialize Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

# Initialize Cohere client
COHERE_API_KEY = os.getenv('COHERE_API_KEY')
cohere_client = CohereClient(api_key=COHERE_API_KEY)

app = Flask(__name__)

# Configure session
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a secure secret key
app.config['SESSION_TYPE'] = 'filesystem'  # Use filesystem-based sessions
Session(app)

@app.route('/')
def index():
    # Check if user data exists in the session
    if 'user_data' not in session:
        return redirect(url_for('user_input'))  # Redirect to the user input page
    return render_template('index.html')

@app.route('/user-input')
def user_input():
    return render_template('user_input.html')

# Store conversation history in memory
conversation_history = []

@app.route('/generate-video', methods=['POST'])
def generate_video():
    data = request.get_json()
    text = data.get('text', '')

    if not text.strip():
        return jsonify({'error': 'Text input is required'}), 400

    try:
        # Generate speech from text
        speech = gTTS(text)
        speech_file = "speech.mp3"
        speech.save(speech_file)

        # Create animation
        animation = animate(audio_file=speech_file)

        # Overlay animation on a background video
        background_video_path = "/home/vynavin/Documents/Projects/GoogleGenai/vid.mp4"  # Ensure this file exists
        output_video_path = "static/output.mp4"
        background_video = VideoFileClip(background_video_path)
        animation.export(path=output_video_path, background=background_video, scale=0.7)

        return jsonify({'videoUrl': f'/{output_video_path}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate-frames', methods=['POST'])
def generate_frames():
    try:
        data = request.get_json()
        text = data.get('text', '').strip()  # Ensure text is stripped of leading/trailing spaces
        if not text:
            return jsonify({'error': 'No text provided'}), 400

        # Retrieve user data from session
        user_data = session.get('user_data', {})
        name = user_data.get('name', 'User')
        age = user_data.get('age', '8')  # Default to 8 if age is not provided
        issues = user_data.get('issues', '')
        goals = user_data.get('goals', '')

        # Load conversation history from session
        conversation_history = session.get('conversation_history', [])

        # Append user input to conversation history with proper formatting
        conversation_history.append(f"User ({name}): {text}")

        # Pass the conversation history to Gemini for processing
        history = "\n".join(conversation_history)
        gemini_response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=(
                f"{history}\nAI: Please respond in a way that is kid-friendly and understandable for {age}-year-olds. "
                f"While trying to solve the following issues where possible, but don't lean in too much on them: {issues}. and their goals are: {goals}. "
                f"Keep responses concise, easy to understand, outgoing, and under 300 characters. Avoid inappropriate, disturbing, or incorrect information. "
                f"If the question is inappropriate or disturbing (in terms of for an 8-year-old), subtly guide the user to a more appropriate topic. "
                f"But make corrections for anything major such as profane language or incorrect information. You should always try to help the user reach their goals. Their goals are: {goals}"
            )
        )

        # Ensure the response object has the expected structure
        if not hasattr(gemini_response, 'text'):
            raise ValueError("Invalid response structure from Gemini API")

        # Use Cohere to moderate the Gemini response
        moderation_response = cohere_client.generate(
            model='command-xlarge',
            prompt=(
                f"Moderate the following response to ensure it is appropriate for an 8-year-old. "
                f"Remove any inappropriate, disturbing, or incorrect information. "
                f"Response: {gemini_response.text}\nModerated Response:"
            ),
            max_tokens=300
        )

        # Ensure the moderation response has the expected structure
        if not moderation_response.generations or not moderation_response.generations[0].text:
            raise ValueError("Invalid moderation response structure from Cohere API")

        # Sanitize the moderated response
        processed_text = re.sub(r'[^a-zA-Z0-9,./?\'" ]', '', moderation_response.generations[0].text).strip()

        # Append AI response to conversation history with proper formatting
        conversation_history.append(f"AI: {processed_text}")

        # Save updated conversation history in session
        session['conversation_history'] = conversation_history

        # Generate additional AI-powered feedback and ratings
        feedback_response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=(
                f"{history}\nBased on the user's input and goals ({goals}), provide the following:\n"
                f"4. Provide general feedback on the user (not ai) as a string."
            )
        )

        parent_feedback_response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=(
                f"{history}\nBased on the user's input and goals ({goals}), provide the following:\n"
                f"4. Provide parent feedback as a string so that the users parents can help the user"
            )
        )
        goals_progress = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=(
                f"{history}\nBased on the user's input and goals ({goals}), provide the following:\n"
                f"rate progress on the following goals on a scale of 0 - 100: {goals}"
            )
        )
        issues_progress = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=(
                f"{history}\nBased on the user's input and issues ({issues}), provide the following:\n"
                f"rate progress on the following resolving of issues on a scale of 0 - 100: {issues}"
            )
        )

        #extract the number straight from goals and issues
        goalsProg = re.findall(r'\d+', goals_progress.text)
        issuesProg = re.findall(r'\d+', issues_progress.text)

        # Ensure the feedback response has the expected structure
        if not hasattr(feedback_response, 'text'):
            raise ValueError("Invalid feedback response structure from Gemini API")
        try:

            session['parentfeedback'] = parent_feedback_response.text
            print(session.get('parentfeedback'))
            session['generalfeedback'] = feedback_response.text
            print(session.get('generalfeedback'))
            session['goals'] = goalsProg[0]
            print(session.get('goals'))
            session['issues'] = issuesProg[0]
            print(session.get('issues'))
            print(f"Feedback and ratings saved in session: {session}")

        except Exception as e:
            print(f"Error parsing feedback response: {e}")

        # Generate speech from the processed text
        speech = gTTS(processed_text)
        speech.save("speech.mp3")

        # Create animation
        animation = animate(audio_file="speech.mp3", fps=24)  # Use reduced FPS

        def frame_generator():
            for frame in animation.final_frames:
                # Convert frame (numpy array) to JPEG for smaller size
                image = Image.fromarray(frame)
                if image.mode == "RGBA":  # Convert RGBA to RGB if necessary
                    image = image.convert("RGB")
                buffer = BytesIO()
                image.save(buffer, format="JPEG", quality=70)  # Use JPEG with reduced quality
                base64_frame = base64.b64encode(buffer.getvalue()).decode('utf-8')
                yield f"data:image/jpeg;base64,{base64_frame}\n"

        # Include audio file as base64
        with open("speech.mp3", "rb") as audio_file:
            audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')

        return Response(
            frame_generator(),
            headers={"X-Audio-Base64": audio_base64},  # Send audio as a custom header
            content_type='text/plain'
        )
    except ValueError as ve:
        # Handle specific validation errors
        print(f"Validation Error in /generate-frames: {ve}")
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        # Log the error for debugging
        print(f"Error in /generate-frames: {e}")
        return jsonify({'error': 'An internal error occurred. Please try again later.'}), 500

@app.route('/language-learning', methods=['GET', 'POST'])
def language_learning():
    if request.method == 'GET':
        return jsonify({'message': 'Please use POST to send data to this endpoint.'}), 405

    data = request.get_json()
    language = data.get('language', 'en')
    user_message = data.get('message', '')

    if not user_message.strip():
        return jsonify({'error': 'Message is required'}), 400

    try:
        # Use Cohere to generate a multilingual response
        cohere_response = cohere_client.generate(
            model='command-xlarge',
            prompt=(
                f"Respond to the following message in {language} in a way that is kid-friendly and understandable for 8-year-olds. "
                f"Keep responses concise and under 300 characters. Avoid inappropriate, disturbing, or incorrect information. "
                f"If the question is inappropriate or disturbing, subtly guide the user to a more appropriate topic.\n\n"
                f"Message: {user_message}\nResponse:"
            ),
            max_tokens=300
        )

        # Ensure the response object has the expected structure
        if not cohere_response.generations or not cohere_response.generations[0].text:
            raise ValueError("Invalid response structure from Cohere API")

        # Extract and sanitize the response text
        processed_text = re.sub(r'[^a-zA-Z,./ ]', '', cohere_response.generations[0].text.strip())

        return jsonify({'response': processed_text})
    except ValueError as ve:
        # Handle specific validation errors
        print(f"Validation Error in /language-learning: {ve}")
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        # Log the error for debugging
        print(f"Error in /language-learning: {e}")
        return jsonify({'error': 'An internal error occurred. Please try again later.'}), 500

@app.route('/gemini-conversation', methods=['POST'])
def gemini_conversation():
    global conversation_history
    data = request.get_json()
    language = data.get('language', 'en')
    user_message = data.get('message', '')

    if not user_message.strip():
        return jsonify({'error': 'Message is required'}), 400

    try:
        # Append user input to conversation history
        conversation_history.append(f"User: {user_message}")

        # Pass the conversation history to Gemini for processing
        history = "\n".join(conversation_history)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=(
                f"{history}\nAI: Please respond in {language} in a way that is kid-friendly and understandable for 8-year-olds. "
                f"Keep responses concise and under 300 characters. Avoid inappropriate, disturbing, or incorrect information. "
                f"If the question is inappropriate or disturbing, subtly guide the user to a more appropriate topic."
            )
        )

        # Ensure the response object has the expected structure
        if not hasattr(response, 'text'):
            raise ValueError("Invalid response structure from Gemini API")

        # Sanitize the model's output to allow only letters, commas, periods, and slashes
        processed_text = re.sub(r'[^a-zA-Z,./ ]', '', response.text)

        # Append AI response to conversation history
        conversation_history.append(f"AI: {processed_text}")

        return jsonify({'response': processed_text})
    except ValueError as ve:
        # Handle specific validation errors
        print(f"Validation Error in /gemini-conversation: {ve}")
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        # Log the error for debugging
        print(f"Error in /gemini-conversation: {e}")
        return jsonify({'error': 'An internal error occurred. Please try again later.'}), 500

@app.route('/voice-input', methods=['POST'])
def voice_input():
    try:
        # Initialize the recognizer
        recognizer = sr.Recognizer()

        # List available microphones for debugging
        print("Available microphones:", sr.Microphone.list_microphone_names())

        # Use the microphone as the source
        with sr.Microphone() as source:
            print("Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1)  # Adjust for ambient noise

            while True:  # Keep listening until valid audio is detected
                try:
                    print("Listening for voice input...")
                    # Removed or increased phrase_time_limit to allow longer speech
                    audio = recognizer.listen(source, timeout=30)  # Removed phrase_time_limit

                    # Recognize speech using Google Web Speech API
                    text = recognizer.recognize_google(audio)
                    print(f"User said: {text}")  # Print the recognized text to the console

                    # Return the recognized text as JSON
                    return jsonify({'text': text})
                except sr.UnknownValueError:
                    print("No audio detected, continuing to listen...")
                    continue  # Keep listening if no valid audio is detected
                except sr.RequestError as e:
                    print(f"Error: Could not request results from Google Speech Recognition service; {e}")
                    return jsonify({'error': f'Could not request results; {e}'}), 500

    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/process-user-data', methods=['POST'])
def process_user_data():
    try:
        data = request.get_json()
        name = data.get('name', '')
        age = data.get('age', '')
        issues = data.get('issues', '')
        goals = data.get('goals', '')

        if not name or not age or not issues:
            return jsonify({'error': 'All fields are required'}), 400

        # Save user data in session
        session['user_data'] = {'name': name, 'age': age, 'issues': issues}

        print(f"User data saved in session: {session['user_data']}")

        # Example response
        return jsonify({'message': 'User data processed and saved successfully'})
    except Exception as e:
        print(f"Error processing user data: {e}")
        return jsonify({'error': 'An error occurred while processing the data'}), 500

@app.route('/get-user-data', methods=['GET'])
def get_user_data():
    try:
        # Retrieve user data and additional stats from session
        user_data = session.get('user_data', {})
        issues = session.get('issues', 50)  # Default to 50 if not set
        goals = session.get('goals', 50)  # Default to 50 if not set
        parent_feedback = session.get('parentfeedback', "No parent feedback available.")
        general_feedback = session.get('generalfeedback', "No general feedback available.")

        # Combine all data into a single response
        response_data = {
            'user_data': user_data,
            'issues': issues,
            'goals': goals,
            'parentfeedback': parent_feedback,
            'generalfeedback': general_feedback
        }

        return jsonify(response_data)
    except Exception as e:
        print(f"Error retrieving user data: {e}")
        return jsonify({'error': 'An error occurred while retrieving the data'}), 500

@app.route('/get-last-response', methods=['GET'])
def get_last_response():
    global conversation_history
    
    # Find the last AI response in the conversation history
    last_response = None
    for message in reversed(conversation_history):
        if message.startswith("AI:"):
            last_response = message[4:].strip()  # Remove "AI: " prefix
            break

    if last_response:
        return jsonify({'response': last_response})
    else:
        return jsonify({'error': 'No AI response found'}), 404

@app.route('/get-conversation-history', methods=['GET'])
def get_conversation_history():
    try:
        # Retrieve conversation history from session
        conversation_history = session.get('conversation_history', [])
        return jsonify({'conversation_history': conversation_history})
    except Exception as e:
        print(f"Error retrieving conversation history: {e}")
        return jsonify({'error': 'An error occurred while retrieving the conversation history'}), 500

@app.route('/dashboard')
def dashboard():
    # Check if user data exists in the session
    if 'user_data' not in session:
        return redirect(url_for('user_input'))  # Redirect to the user input page if no user data
    return render_template('dashboard.html')

@app.route('/language-learning-page')
def language_learning_page():
    return render_template('language_learning.html')

@app.route('/clear-cookies', methods=['POST'])
def clear_cookies():
    try:
        session.clear()  # Clear the session
        return jsonify({'message': 'Session cleared successfully'})
    except Exception as e:
        print(f"Error clearing session: {e}")
        return jsonify({'error': 'An error occurred while clearing the session'}), 500

if __name__ == '__main__':
    app.run(debug=True)
