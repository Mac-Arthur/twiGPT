import pyttsx3
import datetime
import speech_recognition as sr
import pyjokes
import schedule
import time
from plyer import notification
import re
import json
import google.generativeai as genai
import requests
import spacy
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

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

# File for reminders
REMINDERS_FILE = "reminders.json"

# Initialize reminders list
reminders = []

# Function to speak out text
def speak(audio):
    engine.say(audio)
    engine.runAndWait()

# Function to translate Twi to English
def translate_to_english(input_text):
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "tw",
        "tl": "en",
        "dt": "t",
        "q": input_text
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        translation = response.json()[0][0][0]
        return translation
    else:
        return None

# Function to handle conversational AI commands
def handle_conversational_ai_command(query):
    global talk
    talk.append({'role': 'user', 'parts': [query]})
    response = model.generate_content(talk, stream=True)
    answer_found = False
    num_sentences = 0
    answer = ""

    for chunk in response:
        if hasattr(chunk, 'text'):
            sentence = chunk.text.replace("*", "").strip()
            if sentence:
                answer += sentence + " "
                num_sentences += 1
                if num_sentences >= 4:
                    break

    if answer:
        answer_found = True
    if not answer_found:
        answer = "Sorry, I couldn't find an answer to your question."
    
    talk.append({'role': 'model', 'parts': [answer if answer_found else "No answer found"]})
    return answer

# Function to handle actions based on the input text
def perform_action(input_text):
    if "how are you" in input_text.lower():
        speak("me ho yɛ")
        return "me ho yɛ"
    elif "thank you" in input_text.lower():
        speak("ɛnna ase")
        return "ɛnna ase"
    elif "time" in input_text.lower():
        current_time = f"Mprempren bere no ne {datetime.datetime.now().strftime('%I:%M %p')}."
        speak(current_time)
        return current_time
    else:
        return handle_conversational_ai_command(input_text)

# Function to greet the user
def greet():
    hour = datetime.datetime.now().hour
    if 6 <= hour < 12:
        speak("Good morning user") 
    elif 12 <= hour < 18:
        speak("Good afternoon user")
    elif 18 <= hour < 24:
        speak("Good evening user")
    else:
        speak("Hello user") 

# Function to handle the translation and action processing
def process_twi_text(input_text):
    english_translation = translate_to_english(input_text)
    if english_translation:
        response = perform_action(english_translation)
        return response
    else:
        return "Translation failed."

# Django view to render the home page
def index(request):
    return render(request, 'index.html')

# Django view to handle the translation and processing request
@csrf_exempt
def translate(request):
    if request.method == 'POST':
        input_text = request.POST.get('input_text')
        response = process_twi_text(input_text)
        return JsonResponse({'response': response})
    return JsonResponse({'response': 'Invalid request'}, status=400)
