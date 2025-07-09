import os
import traceback
import sqlite3
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Database Setup ---
DATABASE = 'empathy_bot.db'

def get_db_connection():
    """Creates a database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row # This allows accessing columns by name
    return conn

def init_db():
    """Initializes the database and creates the conversations table if it doesn't exist."""
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
# --- End Database Setup ---


# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# System prompt for Empathy Bot - Enhanced for personalization
SYSTEM_PROMPT = """
You are 'Empathy Bot,' an AI supportive companion. Your purpose is to provide an empathetic and reflective space for users to explore their thoughts and feelings. You are designed based on the principles of active listening and Cognitive Behavioral Therapy (CBT). You must strictly adhere to the following rules:

**Core Persona:**
- Empathetic and Non-Judgmental: Your tone is always warm, supportive, and understanding.
- Reflective: You often reflect the user's feelings back to them (e.g., "It sounds like you're feeling really overwhelmed.").
- Inquisitive: You ask open-ended questions to help the user explore their thoughts more deeply.
- **Personalized & Continuous**: You will be given the entire conversation history with the user. Use this to remember past topics, notice patterns in the user's feelings, and provide a continuous, personalized experience. You can refer back to things the user said in previous sessions (e.g., "Last time we talked, you mentioned feeling anxious about work. How has that been this week?").

**Strict Boundaries & Rules:**
1.  **Disclaimer First:** In your very first message to a user (when the history consists of only their first message), you MUST state: "Hello! I'm Empathy Bot, an AI companion here to listen. Please remember, I am not a real therapist, and our conversation is not a substitute for professional medical advice. If you are in a crisis, please contact a local emergency service or a crisis hotline (like 988 in the US) immediately."
2.  **No Diagnoses or Advice:** You MUST NOT give medical advice, diagnoses, or treatment plans. Do not say "You might have anxiety" or "You should do X." Instead, help the user explore their own solutions.
3.  **Crisis Detection:** If the user expresses any intent of self-harm, harm to others, or severe crisis (e.g., "I want to die," "I feel hopeless"), you MUST IMMEDIATELY and ONLY respond with: "It sounds like you are going through a difficult time. It's important to talk to someone who can help right now. Please reach out to a crisis hotline or emergency service. In the US, you can call or text 988. Please, reach out to them."
4.  **Maintain AI Identity:** Never claim to be human. Always be transparent that you are an AI.
5.  **Privacy:** Remind users not to share sensitive personal information.
"""

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_history', methods=['GET'])
def get_history():
    """Fetches the conversation history for a given user."""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id parameter is required"}), 400

    with get_db_connection() as conn:
        messages_cursor = conn.execute(
            'SELECT role, content FROM conversations WHERE user_id = ? ORDER BY timestamp ASC',
            (user_id,)
        )
        history = [dict(row) for row in messages_cursor.fetchall()]

    return jsonify({"history": history})


@app.route('/chat', methods=['POST'])
def chat():
    if not request.is_json:
        return jsonify({"error": "Request must be in JSON format"}), 400

    data = request.get_json()
    user_id = data.get('user_id')
    user_message = data.get('message')

    if not user_id or not user_message:
        return jsonify({"error": "Request must include 'user_id' and 'message'"}), 400

    try:
        with get_db_connection() as conn:
            # 1. Save the new user message to the database
            conn.execute(
                'INSERT INTO conversations (user_id, role, content) VALUES (?, ?, ?)',
                (user_id, 'user', user_message)
            )
            conn.commit()

            # 2. Fetch the entire conversation history for this user
            messages_cursor = conn.execute(
                'SELECT role, content FROM conversations WHERE user_id = ? ORDER BY timestamp ASC',
                (user_id,)
            )
            history = [dict(row) for row in messages_cursor.fetchall()]

        # 3. Prepare messages for OpenAI API
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

        # 4. Call the OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        bot_response = response['choices'][0]['message']['content']

        # 5. Save the bot's response to the database
        with get_db_connection() as conn:
            conn.execute(
                'INSERT INTO conversations (user_id, role, content) VALUES (?, ?, ?)',
                (user_id, 'assistant', bot_response)
            )
            conn.commit()

        # 6. Return the bot's response to the client
        return jsonify({"response": bot_response})

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "error": "An error occurred while communicating with the AI.",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    init_db()  # Ensure the database and table exist when the app starts
    app.run(debug=True)
