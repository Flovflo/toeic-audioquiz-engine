#!/usr/bin/env python3
"""
Script to generate or append TOEIC Part 4 blocks via DeepSeek V3 Chat API.
Supports loading an existing JSON file with wrapper, interactive appending,
and strict JSON parsing, preserving wrapper metadata.
"""
import os
import sys
import json
import requests
import argparse
from typing import List, Dict, Any, Tuple

# Try to load .env for environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# === CLI arguments ===
parser = argparse.ArgumentParser(
    description="Generate or append TOEIC Part 4 JSON blocks using DeepSeek V3 chat API"
)
parser.add_argument(
    '-i', '--input-file', default='toeic_part4.json',
    help="Existing JSON file to load and append (default: toeic_part4.json)"
)
parser.add_argument(
    '-o', '--output-file', default=None,
    help="Output file path (default: same as input file)"
)
parser.add_argument(
    '-u', '--api-url', default=None,
    help="DeepSeek API base URL if different from default"
)
args = parser.parse_args()

INPUT_FILE = args.input_file
OUTPUT_FILE = args.output_file or INPUT_FILE
DEESEEK_API_URL = args.api_url or os.getenv(
    "DEESEEK_API_URL", "https://api.deepseek.com/chat/completions"
)
API_KEY = os.getenv("DEESEEK_API_KEY")

if not API_KEY:
    sys.exit("Error: Please set the DEESEEK_API_KEY environment variable or define it in a .env file.")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

SYSTEM_PROMPT = "You are an expert TOEIC exam writer. Generate one TOEIC Part 4 block in strict JSON format."
USER_PROMPT_TEMPLATE = (
    "Create a TOEIC Part 4 block with talkId {talk_id}, including: context, audioText, and 3 questions. "
    "Questions should cover meetings, planning, IT, HR, projects, etc., realistic traps, mixed difficulty. "
    "Output exactly one valid JSON object (no array, no wrapper)."
)


def generate_talk(talk_id: int) -> Dict[str, Any]:
    """
    Generate one TOEIC Part 4 block via DeepSeek V3 chat API.
    """
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(talk_id=talk_id)}
        ],
        "stream": False,
        "response_format": {"type": "json_object"}
    }
    try:
        resp = requests.post(DEESEEK_API_URL, headers=HEADERS, json=payload, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"API request failed: {e}")

    data = resp.json()
    # Extract the assistant's content
    choices = data.get("choices")
    if not choices or not isinstance(choices, list):
        raise ValueError(f"No choices in API response: {data}")
    content = choices[0].get("message", {}).get("content", "")

    try:
        block = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in API response: {e}\nContent was: {content}")

    # Ensure talkId is set
    if 'talkId' not in block:
        block['talkId'] = talk_id
    return block


def load_existing(path: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Load existing JSON wrapper file. Return (talks_list, wrapper_meta).
    If file missing or invalid, return ([], default_meta).
    """
    default_meta = {"part": 4, "type": "short_talks"}
    if not os.path.isfile(path):
        return [], default_meta
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict) and 'talks' in data and isinstance(data['talks'], list):
            meta = {k: data[k] for k in data if k != 'talks'}
            return data['talks'], meta
        else:
            # legacy list format
            if isinstance(data, list):
                return data, default_meta
    except Exception as e:
        print(f"Warning: could not load '{path}': {e}", file=sys.stderr)
    return [], default_meta


def save_all(path: str, blocks: List[Dict[str, Any]], meta: Dict[str, Any]) -> None:
    """
    Save blocks into JSON file using wrapper meta.
    """
    wrapper = dict(meta)
    wrapper['talks'] = blocks
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(wrapper, f, ensure_ascii=False, indent=2)


def main():
    # Load existing blocks and metadata
    all_blocks, meta = load_existing(INPUT_FILE)
    existing_ids = [blk.get('talkId', 0) for blk in all_blocks if isinstance(blk, dict)]
    next_id = max(existing_ids, default=0) + 1

    # Ask user how many blocks to generate
    try:
        count = int(input("Combien de blocs voulez-vous ajouter ? "))
    except ValueError:
        sys.exit("Entrée invalide : veuillez saisir un nombre entier.")

    added = 0
    for _ in range(count):
        try:
            block = generate_talk(talk_id=next_id)
            all_blocks.append(block)
            print(f"[+] Bloc {next_id} généré", file=sys.stderr)
            next_id += 1
            added += 1
        except Exception as e:
            print(f"[-] Erreur génération bloc {next_id}: {e}", file=sys.stderr)

    if added > 0:
        try:
            save_all(OUTPUT_FILE, all_blocks, meta)
            print(f"[+] Ajouté {added} bloc(s). Sauvegardé {len(all_blocks)} bloc(s) dans '{OUTPUT_FILE}'")
        except Exception as e:
            print(f"[-] Impossible d'écrire dans '{OUTPUT_FILE}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Aucun bloc généré; le fichier n'a pas été modifié.")


if __name__ == "__main__":
    main()
