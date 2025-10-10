import streamlit as st
import WordPreprocessing as wp
import sentimant_analysis as sa
import gemini as gemi
from datetime import datetime, timedelta
import sqlite3
from deep_translator import GoogleTranslator
from langdetect import detect
import consultants  # Import the consultants module

# Database functions (from previous implementation)
DB_NAME = 'saathi_chat_history.db'

def init_db():
    """Initializes the SQLite database and creates the chat table."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_message(role, content):
    """Saves a single chat message to the database."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M:%S")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO chats (date, time, role, content)
        VALUES (?, ?, ?, ?)
    ''', (date_str, time_str, role, content))
    conn.commit()
    conn.close()

def load_today_messages():
    """Loads all chat messages for the current day."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT time, role, content FROM chats WHERE date = ? ORDER BY id
    ''', (date_str,))
    
    messages = []
    for time_str, role, content in cursor.fetchall():
        messages.append({
            "role": role, 
            "content": content, 
            "time": time_str
        })
        
    conn.close()
    return messages

def load_messages_by_date(selected_date):
    """Loads chat messages for a specific date."""
    date_str = selected_date.strftime("%Y-%m-%d")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT time, role, content FROM chats WHERE date = ? ORDER BY id
    ''', (date_str,))
    
    messages = []
    for time_str, role, content in cursor.fetchall():
        messages.append({
            "role": role, 
            "content": content, 
            "time": time_str
        })
        
    conn.close()
    return messages

def get_available_dates():
    """Get all dates that have chat history."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT DISTINCT date FROM chats ORDER BY date DESC
    ''')
    
    dates = [datetime.strptime(row[0], "%Y-%m-%d") for row in cursor.fetchall()]
    conn.close()
    return dates

def clear_today_chat_history():
    """Clears today's chat history from the database."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM chats WHERE date = ?
    ''', (date_str,))
    conn.commit()
    conn.close()

def check_distress_and_alert(distress_score, chat_history):
    """Check distress level and alert consultant if above threshold"""
    if distress_score >= 25:  # Threshold for consultant alert
        consultant = consultants.get_available_consultant()
        if consultant:
            consultant_id, name, email, phone, specialization, experience, availability = consultant
            
            # Send alert (in real implementation, this would send email)
            alert_sent = consultants.send_alert_to_consultant(
                email, name, chat_history, distress_score
            )
            
            # Log the alert
            consultants.log_consultant_alert(
                chat_history, distress_score, consultant_id, name
            )
            
            return {
                'alert_sent': alert_sent,
                'consultant_name': name,
                'consultant_email': email,
                'consultant_phone': phone,
                'specialization': specialization,
                'distress_score': distress_score
            }
    return None

# Initialize database on startup
init_db()

# --- Callback Function to Process Input and Clear Widget ---
def process_and_clear():
    """
    This function runs *before* the script re-runs.
    It processes the input (which is stored in st.session_state) and then clears it.
    """
    
    # 1. Get the input value *before* clearing
    
    user_input_original = st.session_state.chat_input_key 
    
    # Get selected language from session state
    selected_language = st.session_state.get('selected_language', 'English')
    
    # Debug: Print the selected language and original input
    print(f"Selected Language: {selected_language}")
    print(f"Original Input: {user_input_original}")
    
    # Modify gemini_input based on selected language
    if selected_language != 'English':
        gemini_input = f"generate results in {selected_language}: {user_input_original}"
    else:
        gemini_input = user_input_original

    # Debug: Print the modified gemini input
    print(f"Modified Gemini Input: {gemini_input}")

    #Translating and checking if user entererd english or not.
    try:
        detected_lang = detect(user_input_original)
    except:
        detected_lang = 'en'  # default to English if detection fails

    if detected_lang == 'en':
        user_input = user_input_original
    else:
        translated_text = GoogleTranslator(source='auto', target='en').translate(user_input_original)
        user_input = translated_text
    
    if user_input.strip():
        
        # --- 2. Store User Message ---
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Save user message to database
        save_message("User", user_input)
        
        # Also add to session state for immediate display if viewing today's chat
        if st.session_state.get('selected_date_option', 'Today') == 'Today':
            st.session_state.chat_history.append({
                "role": "User", 
                "content": user_input, 
                "time": timestamp
            }) 

        # --- 3. Analysis Logic ---
        chat = wp.Word_Preprocessing(user_input)
        distress_score, compound_score, vader_label, pos_score, neg_score, negative_sentiment_count = sa.analyse(chat)
        
        # Store analysis for sidebar display
        st.session_state.last_analysis = {
            "distress_score": distress_score,
            "compound_score": compound_score,
            "vader_label": vader_label,
            "pos_score": pos_score,
            "neg_score": neg_score,
            "negative_sentiment_count": negative_sentiment_count
        }
        
        # --- 4. Check for distress and alert consultant ---
        consultant_alert = check_distress_and_alert(distress_score, st.session_state.chat_history)
        if consultant_alert:
            st.session_state.consultant_alert = consultant_alert
        
        # --- 5. Gemini Response ---
        gemini_chat_response = gemi.run_gemini_chat(gemini_input)
        
        # --- 6. Store Bot Responses ---
        
        # Analysis message
        analysis_message = f"Sentiment Processed: {vader_label} (Score: {compound_score:.2f})"
        save_message("Saarthi (Analysis)", analysis_message)
        
        # Gemini chat response
        save_message("Saarthi (Talk)", gemini_chat_response)
        
        # Add to current display if viewing today's chat
        if st.session_state.get('selected_date_option', 'Today') == 'Today':
            st.session_state.chat_history.append({
                "role": "Saarthi (Analysis)", 
                "content": analysis_message, 
                "time": datetime.now().strftime("%H:%M:%S")
            })
            
            st.session_state.chat_history.append({
                "role": "Saarthi (Talk)", 
                "content": gemini_chat_response, 
                "time": datetime.now().strftime("%H:%M:%S")
            })

    # 7. Reset the input box value in session state to clear it
    st.session_state.chat_input_key = ""

def clear_chat_callback():
    """Callback function to clear both session state and database"""
    st.session_state.chat_history = []
    st.session_state.last_analysis = {}
    if 'consultant_alert' in st.session_state:
        del st.session_state.consultant_alert
    clear_today_chat_history()
    st.rerun()

# --- Consultant Management Page ---
def show_consultants_page():
    st.title("👨‍⚕️ Consultant Management")
    
    tab1, tab2, tab3 = st.tabs(["View Consultants", "Add Consultant", "Consultant Alerts"])
    
    with tab1:
        st.subheader("Available Consultants")
        consultants_list = consultants.get_all_consultants()
        
        if consultants_list:
            for consultant in consultants_list:
                id, name, email, phone, specialization, exp, availability = consultant
                
                with st.expander(f"👤 {name} - {specialization}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Email:** {email}")
                        st.write(f"**Phone:** {phone}")
                        st.write(f"**Experience:** {exp} years")
                    
                    with col2:
                        st.write(f"**Specialization:** {specialization}")
                        st.write(f"**Availability:** {availability}")
                        
                    # Quick actions
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"Contact {name.split()[0]}", key=f"contact_{id}"):
                            st.info(f"Would contact {name} at {phone} or {email}")
                    with col2:
                        if st.button(f"Deactivate", key=f"deactivate_{id}"):
                            consultants.deactivate_consultant(id)
                            st.success(f"Consultant {name} deactivated")
                            st.rerun()
        else:
            st.info("No consultants available")
    
    with tab2:
        st.subheader("Add New Consultant")
        
        with st.form("add_consultant_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Full Name")
                email = st.text_input("Email")
                phone = st.text_input("Phone")
            
            with col2:
                specialization = st.text_input("Specialization")
                experience = st.number_input("Years of Experience", min_value=0, max_value=50, value=5)
                availability = st.text_input("Availability", value="9 AM - 6 PM")
            
            if st.form_submit_button("Add Consultant"):
                if name and email and phone and specialization:
                    consultants.add_consultant(name, email, phone, specialization, experience, availability)
                    st.success(f"Consultant {name} added successfully!")
                else:
                    st.error("Please fill all required fields")
    
    with tab3:
        st.subheader("Recent Consultant Alerts")
        # This would display alerts from the consultant_alerts table
        st.info("Alert history would be displayed here")

# --- MAIN STREAMLIT APPLICATION ---
def main():
    st.set_page_config(page_title="SAATHI", layout="wide")
    
    # Sidebar navigation
    st.sidebar.title("SAATHI Navigation")
    page = st.sidebar.radio("Go to", ["Chat", "Consultants", "Crisis Help"])
    
    if page == "Chat":
        show_chat_page()
    elif page == "Consultants":
        show_consultants_page()
    elif page == "Crisis Help":
        show_crisis_help_page()

def show_chat_page():
    st.title("SAATHI")
    st.write("A SAARTHI For Your Mental Health.")

    # Initialize session_state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "last_analysis" not in st.session_state:
        st.session_state.last_analysis = {}
    
    if "consultant_alert" not in st.session_state:
        st.session_state.consultant_alert = None
        
    if "selected_date_option" not in st.session_state:
        st.session_state.selected_date_option = "Today"
        
    # Initialize language selection in session state
    if "selected_language" not in st.session_state:
        st.session_state.selected_language = "English"

    # Display consultant alert if exists
    if st.session_state.consultant_alert:
        alert = st.session_state.consultant_alert
        st.error(f"""
        🚨 **CONSULTANT ALERT ACTIVATED**
        
        **Consultant Assigned:** {alert['consultant_name']}  
        **Specialization:** {alert['specialization']}  
        **Contact:** {alert['consultant_email']} | {alert['consultant_phone']}  
        **Distress Level:** {alert['distress_score']}/100
        
        A professional will reach out to you shortly. Please continue sharing how you feel.
        """)

    # -----------------------------------------------------------------
    # 💡 Main Chat Display Box
    # -----------------------------------------------------------------
    st.markdown("### Conversation History")
    
    chat_container = st.container(height=400, border=True)

    with chat_container:
        if not st.session_state.chat_history:
            st.info("Select a date from the sidebar to view chat history, or start a new conversation below.")
        
        for message in st.session_state.chat_history:
            role_icon = "user" if message["role"] == "User" else "assistant"
            
            with st.chat_message(role_icon):
                st.markdown(f'**[{message["time"]}] {message["role"]}:**')
                st.markdown(message["content"])
    
    st.markdown("---")

    # -----------------------------------------------------------------
    # --- Language Selection (MOVED BEFORE THE FORM) ---
    # -----------------------------------------------------------------
    st.markdown("### 💬 Start a New Conversation")
    
    # Language selection box - MOVED OUTSIDE THE FORM
    col1, col2 = st.columns([3, 1])
    with col2:
        # Indian languages including English
        languages = [
            "English", "Hindi", "Bengali", "Telugu", "Marathi", "Tamil", 
            "Urdu", "Gujarati", "Kannada", "Odia", "Punjabi", "Malayalam"
        ]
        selected_language = st.selectbox(
            "🌐 Response Language",
            options=languages,
            index=0,  # Default to English
            key="language_selector"
        )
        # Store selected language in session state
        st.session_state.selected_language = selected_language
    
    with col1:
        st.caption(f"Responses will be generated in: **{selected_language}**")

    # -----------------------------------------------------------------
    # --- Input Box using st.form ---
    # -----------------------------------------------------------------
    with st.form(key='input_form'):
        st.text_input(
            label="Type your message here...",
            max_chars=500,
            key="chat_input_key",
            placeholder="Share how you're feeling today...",
            label_visibility="collapsed"
        )
        
        submit_col, clear_col = st.columns([3, 1])
        with submit_col:
            submit_button = st.form_submit_button(
                label='💬 Send Message',
                on_click=process_and_clear,
                use_container_width=True
            )
        with clear_col:
            if st.form_submit_button(
                label='🗑️ Clear',
                on_click=clear_chat_callback,
                use_container_width=True,
                type="secondary"
            ):
                pass
                
        if submit_button and st.session_state.get('selected_date_option', 'Today') != 'Today':
            st.info("💡 **Tip:** Your message has been saved. Switch to 'Today' view in the sidebar to see your current conversation.")

    # -----------------------------------------------------------------
    # --- Sidebar Display ---
    # -----------------------------------------------------------------
    st.sidebar.header("Chat History & Analysis")
    
    # Database info
    total_messages = len(st.session_state.chat_history)
    st.sidebar.info(f"Messages in view: {total_messages}")
    
    # Clear chat button in sidebar
    if st.sidebar.button("🗑️ Clear Today's Chat", use_container_width=True):
        clear_chat_callback()
    
    # --- Date Selection for Chat History ---
    st.sidebar.markdown("### 📅 Load Chat History by Date")
    
    # Get available dates
    available_dates = get_available_dates()
    
    if available_dates:
        # Create date options for selectbox
        date_options = ["Today"] + [date.strftime("%Y-%m-%d (%A)") for date in available_dates]
        
        selected_date_option = st.sidebar.selectbox(
            "Select date to view chats:",
            options=date_options,
            index=0,  # Default to Today
            key="date_selector"
        )
        
        # Load messages when date is selected
        if st.session_state.selected_date_option != selected_date_option or not st.session_state.chat_history:
            st.session_state.selected_date_option = selected_date_option
            
            if selected_date_option == "Today":
                display_messages = load_today_messages()
                selected_date_display = "Today"
            else:
                # Extract date from the selected option
                selected_date_str = selected_date_option.split(" ")[0]
                selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d")
                display_messages = load_messages_by_date(selected_date)
                selected_date_display = selected_date.strftime("%B %d, %Y")
            
            # Update chat history display
            st.session_state.chat_history = display_messages
            
            # Display selected date info
            st.sidebar.caption(f"Showing: **{selected_date_display}**")
            st.sidebar.caption(f"Messages: **{len(display_messages)}**")
        
    else:
        st.session_state.chat_history = []
        selected_date_display = "Today"
        st.sidebar.info("No previous chats found. Start a new conversation!")
    
    # Recent Messages Preview
    st.sidebar.markdown("### 💬 Recent Messages Preview")
    
    display_messages = st.session_state.chat_history
    if display_messages:
        sidebar_history_text = []
        for msg in display_messages[-5:]: 
            # Truncate long messages for better display
            content = msg["content"]
            if len(content) > 60:
                content = content[:57] + "..."
            sidebar_history_text.append(f'**{msg["role"]}**: {content}')
        
        st.sidebar.markdown(
            f"""
            <div style="
                background-color:#262626;
                color: #ffffff;
                border:1px solid #ddd;
                padding:8px;
                height:120px;
                overflow-y:scroll;
                font-size:13px;
                line-height:1.4;
            ">
                {'<br><br>'.join(sidebar_history_text) if sidebar_history_text else 'No messages for selected date.'}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.sidebar.markdown(
            f"""
            <div style="
                background-color:#262626;
                color: #ffffff;
                border:1px solid #ddd;
                padding:8px;
                height:120px;
                overflow-y:scroll;
                font-size:13px;
                display: flex;
                align-items: center;
                justify-content: center;
            ">
                No messages found for selected date
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Display Analysis Results
    analysis = st.session_state.last_analysis
    if analysis:
        distress_score = analysis["distress_score"]
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("#### Crisis Escalation Logic")
        
        # Enhanced distress levels with consultant alert
        if distress_score >= 50:
            st.sidebar.error("🚨 CRITICAL: Consultant notified immediately")
        elif distress_score >= 25:
            st.sidebar.warning("⚠️ MODERATE: Consultant alert activated")
        elif distress_score >= 15:
            st.sidebar.warning("⚠️ MILD: Monitoring closely")
        else:
            st.sidebar.info(f"✅ Normal range [Score: {distress_score}]")
        
        st.sidebar.markdown("---")
        st.sidebar.metric("Distress Score", distress_score)
        st.sidebar.metric("Compound Score", f"{analysis['compound_score']:.2f}")
        st.sidebar.metric("Vader Label", analysis["vader_label"])
        st.sidebar.metric("Positive Score", f"{analysis['pos_score']:.2f}")
        st.sidebar.metric("Negative Score", f"{analysis['neg_score']:.2f}")
    else:
        st.sidebar.info("Analysis will appear after your first message.")

def show_crisis_help_page():
    st.title("🚨 Crisis Help & Resources")
    
    st.error("""
    **IMMEDIATE HELP AVAILABLE**
    
    If you're in crisis or having thoughts of self-harm, please contact:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Emergency Contacts")
        st.write("""
        **National Suicide Prevention Lifeline**  
        📞 1800-599-0019  
        🌐 suicidepreventionlifeline.org
        
        **Crisis Text Line**  
        💬 1800-120-820050 [Mpower 1on1 Chat (via their website/WhatsApp)]
        
        **Emergency Services**  
        🚑 Dial 112 (Police, Ambulance, Fire) or 
            Dial 108 (Ambulance)
        """)
    
    with col2:
        st.subheader("Online Resources")
        st.write("""
        **Mental Health India**  
        🌐 Kiran Helpline
        
        **National Alliance on Mental Illness**  
        🌐 AASRA Suicide Prevention
        
        **Crisis Chat**  
        🌐 Samaritans Mumbai 
        """)
    
    st.info("""
    **Remember:** You're not alone. Professional help is available and effective. 
    Your mental health matters.
    """)

if __name__ == "__main__":
    main()