import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# nltk.download('vader_lexicon')  # Run once

analyzer = SentimentIntensityAnalyzer()

# Global trackers
negative_sentiment_count = 0
distress_score = 0


def analyse(text):
    global distress_score, negative_sentiment_count

    vs = analyzer.polarity_scores(text)
    pos_score = vs['pos']
    neg_score = vs['neg']
    compound_score = vs['compound']

    # Dynamic distress update (increase or decrease)
    change = (neg_score - pos_score) * 10  # negative → increase, positive → decrease
    distress_score += change

    # Clamp distress score between 0 and 30 (optional cap)
    distress_score = max(0, min(distress_score, 30))

    # Update negative sentiment count
    if compound_score <= -0.5:
        negative_sentiment_count += 1
    elif compound_score >= 0.2:
        # Reduce distress faster if multiple positives appear
        negative_sentiment_count = 0
        distress_score = max(0, distress_score - 5)
    else:
        negative_sentiment_count = 0

    # Crisis escalation logic
    if distress_score >= 25:
        print("🚨 Alert: Consultant allocated (High distress).")
    elif distress_score >= 15:
        print("⚠️ Suggest counseling resources (Moderate distress).")

    if negative_sentiment_count == 3:
        print("🚑 You are in a critical situation. Your chat is being sent to a consultant.")

    # Display summary
    vader_label = "Positive" if compound_score >= 0.05 else ("Negative" if compound_score <= -0.05 else "Neutral")
    print(f"\nMessage: {text}")
    print(f"Scores → Pos: {pos_score}, Neg: {neg_score}, Compound: {compound_score:.2f}")
    print(f"Label: {vader_label}")
    print(f"Distress Score: {distress_score:.2f}")
    print(f"Negative Count: {negative_sentiment_count}")
    print("-" * 60)
