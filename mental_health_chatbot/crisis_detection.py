# crisis_detection.py
import json

# Load keywords
with open("data/distress_keywords.json", "r") as f:
    distress_words = json.load(f)["keywords"]

def check_crisis(text, emotion, sentiment):
    text_lower = text.lower()
    
    # Keyword-based check
    for word in distress_words:
        if word in text_lower:
            return True
    
    # Emotion + sentiment-based
    if emotion == "sad" and sentiment < -0.6:
        return True
    
    return False
