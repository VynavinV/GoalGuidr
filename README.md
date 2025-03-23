# GoalGuidr Project

This project is a Flask-based web application that integrates Google GenAI, Cohere, and other tools to provide AI-powered features such as conversation generation, language learning, and multimedia content creation. It helps people all around the world have access to education, social, language, and mental health resources. Designed to help you meet your goals and overcome roadblocks without even realizing. And with our multi-layered moderation systen, parents and educators can feel confident in allowing students to experiement with ai for the first time.

## Features

- **AI-Powered Conversations**: Uses Google GenAI to generate kid-friendly responses, moderated by Cohere for appropriateness.
- **Language Learning**: Provides multilingual responses tailored for children.
- **Speech-to-Text**: Converts voice input into text using Google Speech Recognition.
- **Text-to-Speech and Animation**: Generates speech and animations from user input.
- **Video Generation**: Overlays animations on background videos.
- **User Data Management**: Stores user data and conversation history in server-side sessions.
- **Feedback and Progress Tracking**: Provides feedback and tracks progress on user goals and issues.

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd GoogleGenAI
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file in the project root.
   - Add the following keys:
     ```
     GEMINI_API_KEY=<your-gemini-api-key>
     COHERE_API_KEY=<your-cohere-api-key>
     ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Access the application at `http://127.0.0.1:5000`.

## API Endpoints

- **`/`**: Redirects to the user input page if no user data exists, otherwise renders the index page.
- **`/user-input`**: Renders the user input page.
- **`/generate-video`**: Generates a video with animations and speech from user input.
- **`/generate-frames`**: Generates animation frames and speech from user input, with moderation applied to AI responses.
- **`/language-learning`**: Provides multilingual responses tailored for children.
- **`/gemini-conversation`**: Generates a conversation response using Google GenAI.
- **`/voice-input`**: Converts voice input to text.
- **`/process-user-data`**: Processes and saves user data in the session.
- **`/get-user-data`**: Retrieves user data and additional stats from the session.
- **`/get-last-response`**: Retrieves the last AI response from the conversation history.
- **`/get-conversation-history`**: Retrieves the full conversation history.
- **`/dashboard`**: Renders the dashboard page.
- **`/language-learning-page`**: Renders the language learning page.
- **`/clear-cookies`**: Clears the session data.

## File Structure

```
GoogleGenAI/
├── app.py               # Main application file
├── templates/           # HTML templates
├── static/              # Static files (e.g., CSS, JS, images)
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables
└── README.md            # Project documentation
```

## Dependencies

- Flask
- Google GenAI SDK
- Cohere SDK
- gTTS
- MoviePy
- PyToon
- SpeechRecognition
- Python Dotenv
- Flask-Session
- Pillow

## Acknowledgments

- **Character Images**: This project uses code open-sourced by [lazykh](https://github.com/lazykh). Check out his YouTube channel: [carykh](https://www.youtube.com/c/carykh).
- [Google GenAI](https://cloud.google.com/genai)
- [Cohere](https://cohere.ai)
- [Flask](https://flask.palletsprojects.com)
- [gTTS](https://gtts.readthedocs.io)
- [MoviePy](https://zulko.github.io/moviepy/)

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
