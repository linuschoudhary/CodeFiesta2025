from flask import Flask, render_template, request, jsonify, session
import WordPreprocessing as wp
import sentimant_analysis as sa
import gemini as gemi
from datetime import datetime
import secrets
import os

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Debug function to check if modules are available
def check_dependencies():
    dependencies = {
        'WordPreprocessing': False,
        'sentimant_analysis': False,
        'gemini': False
    }
    
    try:
        import WordPreprocessing as wp
        dependencies['WordPreprocessing'] = True
    except ImportError as e:
        print(f"WordPreprocessing import error: {e}")
    
    try:
        import sentimant_analysis as sa
        dependencies['sentimant_analysis'] = True
    except ImportError as e:
        print(f"sentimant_analysis import error: {e}")
    
    try:
        import gemini as gemi
        dependencies['gemini'] = True
    except ImportError as e:
        print(f"gemini import error: {e}")
    
    return dependencies

# Initialize session data
def init_session():
    if 'chat_history' not in session:
        session['chat_history'] = []
    if 'last_analysis' not in session:
        session['last_analysis'] = {}
    if 'chat_number' not in session:
        session['chat_number'] = 1

@app.route('/')
def index():
    print("🔍 Index route accessed")  # Debug print
    init_session()
    
    # Check dependencies
    deps = check_dependencies()
    print(f"📦 Dependencies status: {deps}")
    
    try:
        return render_template('index.html', 
                             chat_history=session.get('chat_history', []),
                             last_analysis=session.get('last_analysis', {}))
    except Exception as e:
        print(f"❌ Template rendering error: {e}")
        return f"Template error: {e}", 500

@app.route('/send_message', methods=['POST'])
def send_message():
    print("📨 Send message route accessed")  # Debug print
    init_session()
    
    try:
        user_input = request.json.get('message', '').strip()
        print(f"📝 User input: {user_input}")  # Debug print
        
        if not user_input:
            return jsonify({'error': 'Empty message'}), 400
        
        # Store user message
        timestamp = datetime.now().strftime("%H:%M:%S")
        session['chat_history'].append({
            "role": "User", 
            "content": user_input, 
            "time": timestamp
        })
        
        # Analysis Logic (with error handling)
        try:
            chat = wp.Word_Preprocessing(user_input)
            distress_score, compound_score, vader_label, pos_score, neg_score, negative_sentiment_count = sa.analyse(chat)
            
            # Store analysis
            session['last_analysis'] = {
                "distress_score": distress_score,
                "compound_score": compound_score,
                "vader_label": vader_label,
                "pos_score": pos_score,
                "neg_score": neg_score,
                "negative_sentiment_count": negative_sentiment_count
            }
            
            print(f"📊 Analysis completed - Distress: {distress_score}")  # Debug print
            
        except Exception as e:
            print(f"❌ Analysis error: {e}")
            # Provide default analysis values if analysis fails
            session['last_analysis'] = {
                "distress_score": 0,
                "compound_score": 0.0,
                "vader_label": "neutral",
                "pos_score": 0.0,
                "neg_score": 0.0,
                "negative_sentiment_count": 0
            }
        
        # Gemini Response (with error handling)
        try:
            gemini_chat_response = gemi.run_gemini_chat(user_input)
            print(f"🤖 Gemini response received")  # Debug print
        except Exception as e:
            print(f"❌ Gemini error: {e}")
            gemini_chat_response = "I'm here to listen. Please tell me more about how you're feeling."
        
        # Store bot responses
        session['chat_history'].append({
            "role": "Saarthi (Analysis)", 
            "content": f"Sentiment Processed: {session['last_analysis']['vader_label']} (Score: {session['last_analysis']['compound_score']:.2f})", 
            "time": datetime.now().strftime("%H:%M:%S")
        })

        session['chat_history'].append({
            "role": "Saarthi (Talk)", 
            "content": gemini_chat_response, 
            "time": datetime.now().strftime("%H:%M:%S")
        })
        
        session['chat_number'] += 1
        session.modified = True
        
        return jsonify({
            'success': True,
            'chat_history': session['chat_history'],
            'analysis': session['last_analysis']
        })
        
    except Exception as e:
        print(f"❌ Send message error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    print("🗑️ Clear chat route accessed")  # Debug print
    session['chat_history'] = []
    session['last_analysis'] = {}
    session['chat_number'] = 1
    session.modified = True
    return jsonify({'success': True})

@app.route('/crisis')
def crisis_page():
    print("🚨 Crisis page accessed")  # Debug print
    return render_template('crisis.html')

@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'templates_available': os.path.exists('templates'),
        'static_available': os.path.exists('static')
    })

if __name__ == '__main__':
    print("🚀 Starting Flask application...")
    print(f"📁 Current directory: {os.getcwd()}")
    print(f"📁 Templates exists: {os.path.exists('templates')}")
    print(f"📁 Static exists: {os.path.exists('static')}")
    
    # Check if templates directory exists and list files
    if os.path.exists('templates'):
        template_files = os.listdir('templates')
        print(f"📄 Template files: {template_files}")
    else:
        print("❌ Templates directory not found!")
    
    app.run(debug=True, host='0.0.0.0', port=5000)