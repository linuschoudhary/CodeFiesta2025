import streamlit as st
import WordPreprocessing as wp
import sentimant_analysis as sa
import gemini as gemi
from datetime import datetime

# --- Callback Function to Process Input and Clear Widget ---
def process_and_clear():
    """
    This function runs *before* the script re-runs.
    It processes the input (which is stored in st.session_state) and then clears it.
    """
    
    # 1. Get the input value *before* clearing
    user_input = st.session_state.chat_input_key 
    
    if user_input.strip():
        
        # --- 2. Store User Message ---
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.chat_history.append({"role": "User", "content": user_input, "time": timestamp}) 

        # --- 3. Analysis Logic ---
        chat = wp.Word_Preprocessing(user_input)
        # Assuming wp and sa are defined and callable
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
        
        # --- 4. Gemini Response ---
        # Call the Gemini API function and store the result
        gemini_chat_response = gemi.run_gemini_chat(user_input)
        
        # --- 5. Store Bot Responses ---
        
        # Store the Sentiment Analysis message
        st.session_state.chat_history.append({
            "role": "Saarthi (Analysis)", 
            "content": f"Sentiment Processed: {vader_label} (Score: {compound_score:.2f})", 
            "time": datetime.now().strftime("%H:%M:%S")
        })

        # Store the Gemini chat response
        st.session_state.chat_history.append({
            "role": "Saarthi (Talk)", 
            "content": gemini_chat_response, 
            "time": datetime.now().strftime("%H:%M:%S")
        })

    # 6. CRITICAL: Reset the input box value in session state to clear it
    st.session_state.chat_input_key = ""

# --- MAIN STREAMLIT APPLICATION ---
def main():
    st.set_page_config(page_title="SAATHI", layout="wide")
    st.title("SAATHI: Mental Health Chat Bot")
    st.write("Your Wellness Assistant")

    # Initialize session_state
    if "chat_history" not in st.session_state:
        # Changed history structure to store role, content, and time for better display
        st.session_state.chat_history = [] 
    if "last_analysis" not in st.session_state:
        st.session_state.last_analysis = {}

    # -----------------------------------------------------------------
    # 💡 Main Chat Display Box
    # -----------------------------------------------------------------
    st.markdown("### Conversation History")
    
    # Use a container for the chat box with fixed height and scrolling
    chat_container = st.container(height=400, border=True)

    # Display all messages in the container
    with chat_container:
        if not st.session_state.chat_history:
            st.info("Start the chat by typing a message below.")
        
        for message in st.session_state.chat_history:
            # Using st.chat_message for modern, role-based display
            # Note: We use the role "assistant" for the chat icon, 
            # but display the custom role string in the content.
            role_icon = "user" if message["role"] == "User" else "assistant"
            
            with st.chat_message(role_icon):
                # Display the custom role and content from the history object
                st.markdown(f'**[{message["time"]}] {message["role"]}:**')
                st.markdown(message["content"]) # Display the response text
    
    st.markdown("---") # Separator between chat and input

    # -----------------------------------------------------------------
    # --- Sidebar Display (No functional changes needed here) ---
    # -----------------------------------------------------------------
    st.sidebar.header("Sentiment Analysis Data.")
    
    # 💬 Scrollable Chat History in the Sidebar (Updated to use new history structure)
    st.sidebar.markdown("### 💬 Recent Messages")
    # Using the same history but displayed differently in the sidebar
    sidebar_history_text = []
    # Show last 5 unique messages (to avoid double-counting user/bot entries)
    for msg in st.session_state.chat_history[-5:]: 
        sidebar_history_text.append(f'**{msg["role"]}**: {msg["content"]}')
    
    st.sidebar.markdown(
        f"""
        <div style="
            background-color:#262626; /* Dark background for visibility */
            color: #ffffff;
            border:1px solid #ddd;
            padding:8px;
            height:120px;
            overflow-y:scroll;
            font-size:13px;
        ">
            {'<br>'.join(sidebar_history_text) if sidebar_history_text else 'No chats yet.'}
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Display Analysis Results
    analysis = st.session_state.last_analysis
    if analysis:
        # ... (Rest of your sidebar logic remains the same)
        distress_score = analysis["distress_score"]
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("#### Crisis Escalation Logic")
        
        if distress_score >= 50:
            st.sidebar.error("🚨 Alert: Consultant allocated (High distress).")
        elif distress_score >= 15:
            st.sidebar.warning("⚠️ Suggest counseling resources (Moderate distress).")
        else:
            st.sidebar.info(f"Right now you are normal. [current score: {distress_score}]")
        
        st.sidebar.markdown("---")
        st.sidebar.metric("Compound Score", analysis["compound_score"])
        st.sidebar.metric("Vader Label", analysis["vader_label"])
        st.sidebar.metric("Positive Score", analysis["pos_score"])
        st.sidebar.metric("Negative Score", analysis["neg_score"])
        st.sidebar.metric("Negative Chat Count", analysis["negative_sentiment_count"])
    else:
        st.sidebar.info("Analysis will appear after the first message.")

    # -----------------------------------------------------------------
    # --- Input Box using st.form (at the bottom) ---
    # -----------------------------------------------------------------
    # st.header("Text Input")
    
    # Use st.form to capture input and submission event
    with st.form(key='input_form'):
        st.text_input(
            label=f"Start Chat! (Press Enter or Analyze)",
            max_chars=500, # Increased max chars for proper chat
            # CRITICAL: Use a new unique key for the input box
            key="chat_input_key" 
        )
        
        # st.form_submit_button runs the callback function when pressed (or Enter is hit)
        st.form_submit_button(
            label='Analyze',
            on_click=process_and_clear
        )

if __name__ == "__main__":
    main()