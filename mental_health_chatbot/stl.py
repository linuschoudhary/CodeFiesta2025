import streamlit as st
import pandas as pd
import numpy as np

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Hackathon NLP Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. SIDEBAR (CONTROLS AND INPUT) ---
with st.sidebar:
    st.title("⚙️ Dashboard Controls")
    st.markdown("---")

    # The Primary Input Box for the NLP Pipeline
    user_input = st.text_area(
        "Enter Text for Processing (try: 'the code is grreat ihopeyouknow')",
        "The quick brwn fox jumpps over the lazy doggs.",
        height=150
    )
    
    # Example control options
    analysis_type = st.selectbox(
        "Select Analysis Type:",
        ["Sentiment Detection", "Entity Recognition", "Topic Modeling"]
    )
    
    process_button = st.button("Run NLP Pipeline", type="primary")

    st.markdown("---")
    st.info("Dashboard created using Streamlit.")


# --- 3. MAIN DASHBOARD CONTENT ---

st.header("📊 Real-time NLP Analytics Dashboard")
st.markdown("A structured view for interactive data and model outputs.")

# --- Row 1: Key Metrics & Primary Output ---

col1, col2, col3 = st.columns([1, 1, 4]) # 4-column layout

# Placeholder data for demonstration
total_data_points = 582
average_sentiment = "Positive (0.78)"

with col1:
    st.metric(label="Total Data Points", value=f"{total_data_points}")

with col2:
    st.metric(label="Average Sentiment", value=average_sentiment)

with col3:
    # --- DEDICATED OUTPUT BOX (The requested separate box) ---
    st.subheader("Final Processed Output")
    
    # Use st.container(border=True) to create a clear, separate box
    with st.container(border=True):
        if process_button:
            # Simulate the NLP processing result using the input
            # In a real app, you'd call your preprocess_text(user_input) here
            processed_text = user_input.replace('brwn', 'brown').replace('jumpps', 'jumps').replace('ihopeyouknow', 'i hope you know')
            
            st.markdown(f"**Analysis Type:** `{analysis_type}`")
            st.markdown("---")
            st.code(f"Cleaned String: {processed_text}", language='text')
            
            # Show a mock result based on the analysis type
            if analysis_type == "Sentiment Detection":
                st.success("Result: Detected Strong Positive Sentiment.")
            else:
                st.info("Result: Check the Token/Entity Map below.")
        else:
            st.warning("Click 'Run NLP Pipeline' in the sidebar to process the text.")


# --- Row 2: Visualizations (Charts & Tables) ---

st.markdown("---")
st.subheader("Data Distribution & Visualization")

chart_col, data_col = st.columns(2)

# Sample DataFrame
data = {
    'Category': ['Joy', 'Anger', 'Sadness', 'Neutral', 'Surprise'],
    'Count': np.random.randint(50, 300, 5)
}
df = pd.DataFrame(data)

with chart_col:
    st.markdown("#### Emotion Distribution Chart")
    st.bar_chart(df.set_index('Category'))

with data_col:
    st.markdown("#### Sample Entity Table")
    # Generate some mock token/entity data
    entity_data = {
        'Token': ['fox', 'code', 'dashboard', 'hackathon'],
        'Entity_Type': ['Animal', 'Technology', 'UI', 'Event']
    }
    df_entities = pd.DataFrame(entity_data)
    st.dataframe(df_entities, use_container_width=True)