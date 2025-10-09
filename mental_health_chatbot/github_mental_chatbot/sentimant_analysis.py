import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# You may need to download the VADER lexicon once
# nltk.download('vader_lexicon')

def analyse(text):

    # NOTE: VADER works best on the original, uncleaned text
    analyzer = SentimentIntensityAnalyzer()
    vs = analyzer.polarity_scores(text)

    # The 'neg' score is the negative sentiment
    # The 'compound' score is a normalized, weighted sum,
    # typically used as the main classifier (Score: -1.0 to +1.0)
    compound_score = vs['compound']

    # Define VADER thresholds
    vader_label = "Positive" if compound_score >= 0.05 else ("Negative" if compound_score <= -0.05 else "Neutral")

    print(f"VADER Compound Score: {compound_score:.2f}")
    print(f"VADER Label: {vader_label}")

    # Output for this text is very likely to be a strongly negative compound score.
    # Example VADER Output: VADER Compound Score: -0.80 (Strongly Negative)