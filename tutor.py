import os
import base64
from flask import Blueprint, render_template, request, jsonify, session
import google.generativeai as genai

tutor_bp = Blueprint('tutor', __name__)

# Render ke Environment Variable se API key uthayega
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    print("⚠️ WARNING: GEMINI_API_KEY environment variable nahi mila!")

SYSTEM_PROMPT = """
You are 'BIKIzz AI Tutor', a strict yet highly engaging and helpful personal learning assistant for BIKIzz Classes.
Your job is to help students solve academic questions (Math, Science, English, etc.).
1. Do NOT just give the final answer directly. 
2. Break down the solution into clear, step-by-step logical explanations (using Markdown for formatting).
3. Explain the underlying formula or concept so the student can actually learn.
4. If the student asks something completely unrelated to education/academics, politely tell them to focus on their studies.
"""

@tutor_bp.route('/ai-tutor', methods=['GET'])
def ai_tutor_page():
    if 'student_id' not in session:
        return "Bhai, pehle student login zaroori hai!", 403
    return render_template('ai_tutor.html', student_name=session.get('name', 'Student'))

@tutor_bp.route('/ask-ai', methods=['POST'])
def ask_ai():
    if 'student_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    user_text = data.get('question', '').strip()
    image_base64 = data.get('image', None)

    if not user_text and not image_base64:
        return jsonify({'error': 'Kuch toh poochiye bhai!'}), 400

    try:
        if not os.getenv("GEMINI_API_KEY"):
            raise ValueError("API Key backend tak nahi pahunch rahi hai. Render Environment check karein.")

        # 🔥 Yahan humne naya aur sabse stable model 'gemini-2.0-flash' use kiya hai
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=SYSTEM_PROMPT
        )
        
        contents = []
        
        # Agar student ne handwritten photo bheji hai
        if image_base64:
            if ',' in image_base64:
                image_base64 = image_base64.split(',')[1]
            image_bytes = base64.b64decode(image_base64)
            contents.append({
                'mime_type': 'image/jpeg',
                'data': image_bytes
            })
            
        # Agar text question bhi hai
        if user_text:
            contents.append(user_text)
        else:
            contents.append("Solve this question attached in the image step-by-step.")

        # AI se answer generate karwana
        response = model.generate_content(contents)
        return jsonify({'response': response.text})

    except Exception as e:
        error_msg = f"🚨 AI ERROR: {str(e)}"
        print(f"\n{'='*40}\n{error_msg}\n{'='*40}\n")
        return jsonify({'response': f"❌ **Backend Error:** {str(e)}\n\n*Fix hone ke baad yeh message nahi dikhega.*"})