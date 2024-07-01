import pyttsx3
import datetime
import requests
import google.generativeai as genai
import spacy
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import concurrent.futures
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Initialize Spacy
nlp = spacy.load("en_core_web_sm")

# Initialize pyttsx3 engine
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)  # Female voice
rate = engine.getProperty('rate')
engine.setProperty('rate', rate - 50)

# Initialize the generative model for conversational AI
model = genai.GenerativeModel('gemini-pro')
talk = []

# List to store old queries
old_queries = []

# Function to speak out text
def speak(audio):
    engine.say(audio)
    engine.runAndWait()

# Function to translate text using Google Translate API
def translate_text(input_text, source_lang, target_lang):
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": source_lang,
        "tl": target_lang,
        "dt": "t",
        "q": input_text
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        translation = response.json()[0][0][0]
        return translation
    except requests.RequestException as e:
        logging.error(f"Translation error: {e}")
        return None

# Function to handle conversational AI commands
def handle_conversational_ai_command(query):
    global talk
    talk.append({'role': 'user', 'parts': [query]})
    response = model.generate_content(talk, stream=True)
    answer_found = False
    num_sentences = 0  # Initialize as an integer
    answer = ""

    for chunk in response:
        if hasattr(chunk, 'text'):
            sentence = chunk.text.replace("*", "").strip()
            if sentence:
                answer += sentence + " "
                num_sentences += 1
                if num_sentences >= 5:
                    break

    if answer:
        answer_found = True
    if not answer_found:
        answer = "Sorry, I couldn't find an answer to your question."
    
    talk.append({'role': 'model', 'parts': [answer if answer_found else "No answer found"]})
    return answer

# Example usage
talk = []
user_query = "What's the weather like today?"
response = handle_conversational_ai_command(user_query)
print(response)

# Function to handle actions based on the input text
def perform_action(input_text):
    return handle_conversational_ai_command(input_text)

# Function to handle the translation and action processing
def process_twi_text(input_text):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_english_translation = executor.submit(translate_text, input_text, "tw", "en")
        english_translation = future_english_translation.result()
        
        if english_translation:
            response = perform_action(english_translation)
            future_twi_translation = executor.submit(translate_text, response, "en", "tw")
            twi_translation = future_twi_translation.result()
            if twi_translation:
                return english_translation, response, twi_translation
            else:
                return english_translation, response, "Twi translation failed."
        else:
            return None, None, "Translation failed."

# Django view to render the home page
def index(request):
    return render(request, 'index.html')

# Django view to handle the translation and processing request
@csrf_exempt
def translate(request):
    if request.method == 'POST':
        input_text = request.POST.get('input_text')
        english_translation, response, twi_translation = process_twi_text(input_text)
        
        if english_translation and response:
            # Store the query and response
            old_queries.append({
                "query": input_text,
                "response": twi_translation
            })

        return JsonResponse({'response': twi_translation})
    return JsonResponse({'response': 'Invalid request'}, status=400)

# Django view to fetch old queries
@csrf_exempt
def get_old_queries(request):
    if request.method == 'GET':
        return JsonResponse(old_queries, safe=False)
    return JsonResponse({'response': 'Invalid request'}, status=400)
