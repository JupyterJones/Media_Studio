import random
import nltk
import spacy
from nltk.corpus import stopwords
from pydantic import BaseModel

# Download NLTK data (run these once if not already done)
nltk.download('punkt')
nltk.download('stopwords')

# Load Spacy model
nlp = spacy.load("en_core_web_sm")

# Define the model class using Pydantic BaseModel
class PromptModel(BaseModel):
    text: str
    min_words: int = 40
    max_words: int = 60

    def preprocess_text(self):
        """Tokenizes and filters the text, removing stopwords."""
        stop_words = set(stopwords.words('english'))
        tokens = nltk.word_tokenize(self.text)
        filtered_tokens = [word for word in tokens if word.isalnum() and word.lower() not in stop_words]
        return filtered_tokens

    def extract_key_phrases(self):
        """Extracts key phrases using Spacy."""
        doc = nlp(self.text)
        key_phrases = set(chunk.text for chunk in doc.noun_chunks)
        return list(key_phrases)

    def generate_prompt(self):
        """Generates a prompt with a word count between min_words and max_words."""
        phrases = self.extract_key_phrases()
        selected_phrases = random.sample(phrases, min(len(phrases), 5))
        prompt = ' '.join(selected_phrases)
        
        # Ensure prompt has at least min_words
        if len(prompt.split()) < self.min_words:
            additional_phrases = random.sample(phrases, 2)
            prompt += ' ' + ' '.join(additional_phrases)
        
        # Limit prompt to max_words
        return ' '.join(prompt.split()[:self.max_words])

# Sample text input
TEXT = """Woodstock smoking a pipe, abstract, psychedelic, dream dimension by heinrich kley
many hands coming together in unison, pen and ink, illustrated by hergé, close up face of an old lonely man. Sadness, stunning color scheme, high use of black ink, masterpiece
Futurepunk elderly man interacting with quantum nanotechnology that will change the way we interact with technology. The sci-fi ambiance should be filled with a colorful spectrum that creates an otherworldly feeling. The art style should be inspired by Mattias Adolfsson's work.
Woodstock A man deep in thought, dreaming, abstract, psychedelic, dream dimension by heinrich kley style R Crumb cartoonist Ed Piskor  pen and ink, illustrated by hergé,
graphic novel cover page top text in fancy gold letters: " Thought"
elderly man interacting with quantum nanotechnology that will change the way we interact with technology. The sci-fi ambiance should be filled with a colorful spectrum that creates an otherworldly feeling. The art style should be inspired by Mattias Adolfsson's work.
graphic novel cover page top text in fancy gold letters: "Coding"
old man interacting with quantum neural network that will change the way we interact with technology. The sci-fi ambiance should be filled with a colorful spectrum that creates an otherworldly feeling. The art style should be inspired style R Crumb cartoonist Ed Piskor
bottom text : "Deep Thought" Voynich style
graphic novel cover page top text in fancy gold letters: "AI Coding"
Center: Old man interacting with AI neural network that will change the way we interact with technology. sticker, colorful, illustration, highly detailed, simple, smooth and clean vector, no jagged lines, vector art, smooth for a sticker art by butcher billy
bottom text : "New Frontier" Voynich style
Japanese vintage poster, man head containing all four corners of the universe, monochromatic scheme chequer sky containing, astral realm, dripping love heart dripping onto psychedelic background by maurits cornelis escher
Create a portrait image of a young woman with light brown skin and delicate facial features, wearing a light blue dress with subtle frills. Her hair is medium-length, styled into fine braids tied at the back of her head. She wears long, silver earrings and her makeup is understated with an emphasis on illuminated skin. The background of the image is a solid, warm red color."""

# Instantiate the model
prompt_model = PromptModel(text=TEXT)

# Generate random prompts
for _ in range(5):
    prompt = prompt_model.generate_prompt()
    print(f"Generated Prompt: {prompt}\n")