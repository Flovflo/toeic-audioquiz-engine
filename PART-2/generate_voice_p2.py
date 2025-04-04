import json
import requests
import os
import random
import io
from pydub import AudioSegment
from dotenv import load_dotenv

load_dotenv()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
MALE_VOICES = [
    "IKne3meq5aSn9XLyUdCD",   
    "pNInz6obpgDQGcFmaJgB",
    "aeMZw5mFolEDifP9XfB4",    
]

FEMALE_VOICES = [
    "IKne3meq5aSn9XLyUdCD",   
    "EXAVITQu4vr4xnSDxMaL",
    "pjcYQlDFKMbcOUp6F5GD",  
]
OUTPUT_DIR = os.getenv("OUTPUT_DIR")
INPUT_JSON_FILE = os.getenv("INPUT_JSON_FILE")
MODEL_ID = os.getenv("MODEL_ID")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_speech(text, voice_id):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }

    data = {
        "text": text,
        "model_id": MODEL_ID,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        return AudioSegment.from_file(io.BytesIO(response.content), format="mp3")
    else:
        raise Exception(f"Erreur génération audio : {response.status_code} - {response.text}")

def generate_question_audio(question_id, prompt, choices):
    print(f"\n🎙️ Traitement de la question ID {question_id}...")

    male_voice = random.choice(MALE_VOICES)
    female_voice = random.choice(FEMALE_VOICES)
    print(f"  ➤ Voix question : {male_voice}")
    print(f"  ➤ Voix choix    : {female_voice}")

    prompt_audio = generate_speech(prompt, male_voice)

    choices_text = "\n".join([f"{key}: {value}" for key, value in choices.items()])
    choices_audio = generate_speech(choices_text, female_voice)

    silence = AudioSegment.silent(duration=500)
    final_audio = prompt_audio + silence + choices_audio

    output_file = os.path.join(OUTPUT_DIR, f"question_{question_id}.mp3")
    final_audio.export(output_file, format="mp3")

    print(f"✅ Audio généré : {output_file}")

with open(INPUT_JSON_FILE, "r") as f:
    data = json.load(f)

for question in data["questions"]:
    generate_question_audio(
        question_id=question["id"],
        prompt=question["audioPrompt"],
        choices=question["choices"]
    )