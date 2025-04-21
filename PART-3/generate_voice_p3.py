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
      - Choix d'une voix unique pour 'Man' et pour 'Woman', gardées constantes.
      - Lecture du dialogue avec ces voix.
      - Lecture des questions (texte seul) avec une voix tierce.
    """
    final_audio = AudioSegment.empty()

    # 1) Sélection de la voix pour chaque locuteur, une fois pour toute la conversation
    man_voice = random.choice(MALE_VOICES)
    woman_voice = random.choice(FEMALE_VOICES)

    # 2) (Optionnel) voix distincte pour les questions
    question_voice_candidates = [v for v in MALE_VOICES + FEMALE_VOICES if v not in (man_voice, woman_voice)]
    question_voice = random.choice(question_voice_candidates) if question_voice_candidates else man_voice

    # 3) Lecture des utterances dans l'ordre de 'sequence'
    for utt in sorted(conversation["utterances"], key=lambda x: x["sequence"]):
        sp = utt["speaker"].lower()
        if sp == "man":
            voice_id = man_voice
        elif sp == "woman":
            voice_id = woman_voice
        else:
            voice_id = man_voice  # fallback
        speech = generate_speech(utt["text"], voice_id)
        final_audio += speech + AudioSegment.silent(duration=500)

    # 4) Lecture des questions (texte seul), avec pause avant chaque question
    for idx, q in enumerate(conversation.get("questions", [])):
        pause = 5000 if idx > 0 else 1000
        final_audio += AudioSegment.silent(duration=pause)
        question_audio = generate_speech(q["text"], question_voice)
        final_audio += question_audio

    return final_audio

if __name__ == '__main__':
    with open(INPUT_JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for conv in data.get("conversations", []):
        conv_id = conv.get("conversationId")
        print(f"Traitement de la conversation ID {conv_id}…")
        audio = generate_conversation_audio(conv)
        output_path = os.path.join(OUTPUT_DIR, f"conversation_{conv_id}.mp3")
        audio.export(output_path, format="mp3")
        print(f"✅ Audio généré : {output_path}")