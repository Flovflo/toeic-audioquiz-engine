import json
import os
import random
import io
from pydub import AudioSegment
from dotenv import load_dotenv
import requests

# Charger les variables d'environnement
load_dotenv()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    raise EnvironmentError("La variable d'environnement ELEVENLABS_API_KEY n'est pas définie.")

# Listes d'IDs de voix (masculines et féminines)
MALE_VOICES = [
    "IKne3meq5aSn9XLyUdCD",
    "pNInz6obpgDQGcFmaJgB",
    "aeMZw5mFolEDifP9XfB4",
]
FEMALE_VOICES = [
    "EXAVITQu4vr4xnSDxMaL",
    "pjcYQlDFKMbcOUp6F5GD",
    # Ajoutez d'autres voix si nécessaire
]

# Répertoires et fichiers
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
INPUT_JSON_FILE = os.getenv("INPUT_JSON_FILE", "short_talks_part4.json")
MODEL_ID = os.getenv("MODEL_ID", "default_model")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_speech(text: str, voice_id: str) -> AudioSegment:
    """
    Envoie le texte à l'API ElevenLabs et retourne un AudioSegment.
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    payload = {
        "text": text,
        "model_id": MODEL_ID,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }
    resp = requests.post(url, json=payload, headers=headers)
    if resp.status_code != 200:
        raise RuntimeError(f"Erreur génération audio : {resp.status_code} - {resp.text}")
    return AudioSegment.from_file(io.BytesIO(resp.content), format="mp3")


def generate_talk_audio(talk: dict, main_voice: str, question_voice: str) -> AudioSegment:
    """
    Génère l'audio pour un seul talk.
    """
    audio = AudioSegment.empty()
    # Premier énoncé : audioText
    audio += generate_speech(talk.get("audioText", ""), main_voice)
    # Pause plus longue avant la première question
    audio += AudioSegment.silent(duration=1000)
    # Lecture des questions avec pauses étendues
    for q in talk.get("questions", []):
        audio += generate_speech(q.get("text", ""), question_voice)
        audio += AudioSegment.silent(duration=7000)
    return audio


if __name__ == '__main__':
    # Chargement du JSON
    with open(INPUT_JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Vérifier le type
    if data.get("type") != "short_talks":
        raise ValueError("Le JSON n'est pas de type 'short_talks'.")

    # Sélection aléatoire des voix communes
    main_voice = random.choice(MALE_VOICES + FEMALE_VOICES)
    question_candidates = [v for v in MALE_VOICES + FEMALE_VOICES if v != main_voice]
    question_voice = random.choice(question_candidates) if question_candidates else main_voice

    # Générer et exporter un fichier par talkId
    for talk in data.get("talks", []):
        talk_id = talk.get("talkId")
        print(f"Génération audio pour talkId {talk_id}...")
        audio = generate_talk_audio(talk, main_voice, question_voice)
        output_path = os.path.join(OUTPUT_DIR, f"talk_{talk_id}_part{data.get('part')}.mp3")
        audio.export(output_path, format="mp3")
        print(f"✅ Audio généré : {output_path}")
