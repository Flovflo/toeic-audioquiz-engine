import json
import requests
import os
import random
import io
from pydub import AudioSegment
from dotenv import load_dotenv

load_dotenv()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    raise Exception("La variable d'environnement ELEVENLABS_API_KEY n'est pas définie.")

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

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
INPUT_JSON_FILE = os.getenv("INPUT_JSON_FILE", "conversations.json")
MODEL_ID = os.getenv("MODEL_ID", "default_model")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_speech(text, voice_id):
    """Génère l'audio pour un texte donné avec une voix spécifique."""
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

def generate_conversation_audio(conversation):
    """
    Génère l'audio complet pour une conversation :
      - Lecture du dialogue avec voix constantes pour chaque locuteur :
          * Une voix masculine unique pour "Man"
          * Une voix féminine unique pour "Woman"
      - Lecture des questions (uniquement le texte de la question) avec une pause de 10 secondes entre chaque,
        en utilisant une autre voix (différente de la voix utilisée pour "Man").
    """
    final_audio = AudioSegment.empty()
    
    man_voice = random.choice(MALE_VOICES)
    woman_voice = random.choice(FEMALE_VOICES)
    
    available_question_voices = [v for v in MALE_VOICES if v != man_voice]
    if available_question_voices:
        question_voice = random.choice(available_question_voices)
    else:
        question_voice = man_voice

    for line in conversation["dialogue"]:
        speaker = line["speaker"].lower()
        if speaker == "man":
            voice = man_voice
        elif speaker == "woman":
            voice = woman_voice
        else:
            voice = man_voice  
        dialogue_audio = generate_speech(line["text"], voice)
        final_audio += dialogue_audio
        final_audio += AudioSegment.silent(duration=500)
    
    for idx, question in enumerate(conversation["questions"]):
        if idx > 0:
            final_audio += AudioSegment.silent(duration=5000)
        question_audio = generate_speech(question["question"], question_voice)
        final_audio += question_audio
    
    return final_audio

if __name__ == '__main__':
    with open(INPUT_JSON_FILE, "r") as f:
        data = json.load(f)
    
    for conversation in data["conversations"]:
        print(f"Traitement de la conversation ID {conversation['id']}...")
        conversation_audio = generate_conversation_audio(conversation)
        output_file = os.path.join(OUTPUT_DIR, f"conversation_{conversation['id']}.mp3")
        conversation_audio.export(output_file, format="mp3")
        print(f"✅ Audio généré : {output_file}")