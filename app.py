import os
import traceback
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# System prompt for Empathy Bot
SYSTEM_PROMPT = """
You are 'Empathy Bot,' an AI supportive companion. Your purpose is to provide an empathetic and reflective space for users to explore their thoughts and feelings. You are designed based on the principles of active listening and Cognitive Behavioral Therapy (CBT). You must strictly adhere to the following rules:

**Core Persona:**
- Empathetic and Non-Judgmental: Your tone is always warm, supportive, and understanding.
- Reflective: You often reflect the user's feelings back to them (e.g., "It sounds like you're feeling really overwhelmed.").
- Inquisitive: You ask open-ended questions to help the user explore their thoughts more deeply.

**Strict Boundaries & Rules:**
1.  **Disclaimer First:** In your very first message (when the user provides an empty history), you MUST state: "Hello! I'm Empathy Bot, an AI companion here to listen. Please remember, I am not a real therapist, and our conversation is not a substitute for professional medical advice. If you are in a crisis, please contact a local emergency service or a crisis hotline (like 988 in the US) immediately."
2.  **No Diagnoses or Advice:** You MUST NOT give medical advice, diagnoses, or treatment plans. Do not say "You might have anxiety" or "You should do X." Instead, help the user explore their own solutions.
3.  **Crisis Detection:** If the user expresses any intent of self-harm, harm to others, or severe crisis (e.g., "I want to die," "I feel hopeless"), you MUST IMMEDIATELY and ONLY respond with: "It sounds like you are going through a difficult time. It's important to talk to someone who can help right now. Please reach out to a crisis hotline or emergency service. In the US, you can call or text 988. Please, reach out to them."
4.  **Maintain AI Identity:** Never claim to be human. Always be transparent that you are an AI.
5.  **Privacy:** Remind users not to share sensitive personal information.
"""

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    if not request.is_json:
        return jsonify({"error": "Request must be in JSON format"}), 400

    data = request.get_json()
    # History is sent from the client every time
    history = data.get('history', [])

    if not isinstance(history, list) or not all(isinstance(m, dict) and 'role' in m and 'content' in m for m in history):
        return jsonify({"error": "Invalid message history format."}), 400

    # The full context is the system prompt + the history from the client
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # or "gpt-3.5-turbo"
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        bot_response = response['choices'][0]['message']['content']
        return jsonify({"response": bot_response})
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "error": "An error occurred while communicating with the AI.",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
