import re
import spacy
from nltk.corpus import stopwords
from spellchecker import SpellChecker
import sentimant_analysis as sa




# --- Setup ---
# Initialize necessary tools once at the start of your program for efficiency
# (Ensure 'en_core_web_sm' is downloaded: python -m spacy download en_core_web_sm)
nlp = spacy.load("en_core_web_sm")
spell = SpellChecker()
# stop_words = set(stopwords.words('english'))

def is_known(word):
    """Checks if a word is in the known vocabulary (using spellchecker's dictionary)."""
    # The 'in' operator checks the word frequency dictionary
    return word in spell

def segment_word(text):
    """
    Splits a run-together word into its most likely correct sequence of words 
    using a dynamic programming approach based on known word frequency.
    """
    n = len(text)
    memo = {}  # Memoization cache

    def find_splits(i):
        # Base case: if we are at the end of the string
        if i == n:
            return []
        
        if i in memo:
            return memo[i]

        best_split = None
        
        # Iterate through all possible end points (j) for the first word
        for j in range(i + 1, n + 1):
            word = text[i:j]
            
            # 1. Check if the segment is a known word
            if is_known(word):
                # 2. Recursively find the best split for the rest of the string
                rest_split = find_splits(j)
                
                if rest_split is not None:
                    current_split = [word] + rest_split
                    
                    # Prioritize the split that results in the fewest tokens (fewer words run together)
                    if best_split is None or len(current_split) < len(best_split):
                         best_split = current_split
            
        memo[i] = best_split
        return best_split

    result = find_splits(0)
    # If successful split, return the list; otherwise, return the original text as a single item
    return result if result else [text]

def preprocess_text(text):
    # 1. Cleaning and Case Conversion
    text = text.lower()
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'[^\w\s]', '', text) # Remove punctuation
    text = re.sub(r'\s+', ' ', text).strip() # Remove extra whitespace

    # 2. Initial Tokenization
    tokens = text.split() 
    
    # 3. Spell Check (Handles misspelled words)
    corrected_tokens = []
    misspelled = spell.unknown(tokens)
    
    for word in tokens:
        if word in misspelled:
            correction = spell.correction(word)
            corrected_tokens.append(correction if correction else word)
        else:
            corrected_tokens.append(word)

    # 4. Word Segmentation (NEW STEP: Handles run-together words like 'youknow')
    segmented_tokens = []
    for token in corrected_tokens:
        # Check tokens that are likely run-together (i.e., not known words, and length suggests a split)
        if not is_known(token) and len(token) > 4: 
             splits = segment_word(token)
             segmented_tokens.extend(splits)
        else:
            segmented_tokens.append(token)

# """
#     # 5. Stop Word Removal
#     filtered_tokens = [word for word in segmented_tokens if word not in stop_words]
# """

    # 6. Lemmatization (Language-Specific Normalization)
    text_for_spacy = " ".join(segmented_tokens)
    doc = nlp(text_for_spacy)

    # Get the lemma (base form) of each token, filtering numbers, etc.
    lemmas = [
        token.lemma_ 
        for token in doc 
        if not token.is_punct and not token.is_space and not token.like_num
    ]

    return lemmas

while True:
    # Note: You need to run this code in an environment where 'input()' is supported (like a console or terminal)
    sample_text = input("Enter Something: ")

    final_tokens = preprocess_text(sample_text)

    print(f"\nOriginal Text: {sample_text}")
    print("-" * 50)
    print(f"Final Processed Tokens (Corrected, Segmented, Lemmatized): \n{final_tokens}")


    # Convert the list of tokens back into a single string

    string_text = " ".join(final_tokens)
    print(f"String Texts: {string_text}")
    sa.analyse(string_text)