from deep_translator import GoogleTranslator

def translate_to_english(text):
    translated = GoogleTranslator(source='auto', target='en').translate(text)
    print("Translated Text (English):", translated)
    return translated

# Example
translate_to_english("Je suis fatigué aujourd'hui.")
