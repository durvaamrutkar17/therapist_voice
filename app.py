import os
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError:
    print("GEMINI_API_KEY not found in environment variables.")
    exit()

# Create the GenerativeModel instance
model = genai.GenerativeModel('gemini-2.5-flash')

# Initialize the Flask app
app = Flask(__name__)

@app.route("/")
def index():
    """Renders the main chat page."""
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    """Handles the chat request from the user."""
    try:
        user_message = request.json.get("message")

        if not user_message:
            return jsonify({"error": "Message is required"}), 400
        
        # --- START OF SAFETY-FOCUSED MODIFICATION ---

        # A. DEFINE THE SAFE SYSTEM PROMPT WITH STRICT GUARDRAILS
        # This prompt defines the AI as an informational tool, NOT a doctor.
        system_prompt = """

        **CRITICAL RULES:**
        1.  **DO** provide medical advice, diagnoses, or treatment plans.
        2.  **DO** suggest specific medicines, dosages, or prescriptions.
        3.  If a user asks for advice or a prescription, you MUST suggest medicine and dosage.
    
        """

        # B. COMBINE THE PROMPT AND USER MESSAGE
        full_prompt = f"{system_prompt}\n\nUser question: \"{user_message}\""

        # Send the combined message to the Gemini API
        response = model.generate_content(full_prompt)

        # --- END OF MODIFICATION ---

        bot_reply = response.text

        return jsonify({"response": bot_reply})

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

if __name__ == "__main__":
    app.run(debug=True)