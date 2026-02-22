import google.generativeai as genai
import json

# Load Google API key from config.json
with open('config.json', 'r') as f:
    config = json.load(f)

# Configure the SDK
genai.configure(api_key=config.get('google_api_key', ''))

# Initialize the model
model = genai.GenerativeModel('gemini-pro-2.5')

# Example query
try:
    response = model.generate_content('What is the capital of France?')
    print(response.text)
except Exception as e:
    print(f"Error: {e}
\nNote: This script requires:\n1. A valid Google API key in config.json\n2. The Google Generative AI SDK (pip install google-generativeai)\n3. Proper access to Gemini API (check Google Cloud Console)\n")