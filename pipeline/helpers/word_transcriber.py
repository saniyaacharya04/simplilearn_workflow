import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from helpers.transcribe import transcribe_audio, transcribe_directory
except ImportError:
    try:
        from transcribe import transcribe_audio, transcribe_directory
    except ImportError:
        # Fallback import if transcribe.py is in helpers or root
        import importlib.util
        _trans_file = Path(__file__).resolve().parent / "transcribe.py"
        if not _trans_file.exists():
            _trans_file = _ROOT / "transcribe.py"
        if _trans_file.exists():
            spec = importlib.util.spec_from_file_location("transcribe", str(_trans_file))
            trans_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(trans_mod)
            transcribe_audio = trans_mod.transcribe_audio
            transcribe_directory = trans_mod.transcribe_directory
        else:
            transcribe_audio = None
            transcribe_directory = None


def find_group_audio_file(base_folder: str, group_id: Union[str, int]) -> Optional[Path]:
    """Finds the primary audio file for a given group in the topic folder."""
    gid = str(group_id)
    base_p = Path(base_folder)

    search_dirs = [
        base_p / "audio_elements",
        base_p / "audio_concat_dir",
        _ROOT / "merged_audio",
        base_p,
    ]

    for s_dir in search_dirs:
        if not s_dir.exists():
            continue
        # Direct pattern match
        patterns = [
            f"group_{gid}_pair_1_statement1.wav",
            f"group_{gid}_pair_*_statement*.wav",
            f"merged_g{gid}.wav",
            f"merged_group_{gid}.wav",
            f"scene_{gid}.wav",
            f"scene_{gid}_combined.wav",
            f"group_{gid}_final.wav",
            f"group_{gid}.wav",
        ]
        for pat in patterns:
            matches = sorted(list(s_dir.glob(pat)))
            if matches:
                return matches[0]

    return None


def get_or_create_word_transcript(
    base_folder: str,
    group_id: Union[str, int],
    force: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Returns word-level and segment-level transcript for a group.
    If transcript does not exist on disk, runs transcribe_audio using Groq Whisper.
    """
    gid = str(group_id)
    base_p = Path(base_folder)
    transcripts_dir = base_p / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)

    target_json = transcripts_dir / f"group_{gid}_word_level.json"

    # Also check existing candidates
    candidate_jsons = [
        target_json,
        transcripts_dir / f"group_{gid}_pair_1_statement1_word_level.json",
        transcripts_dir / f"group_{gid}_pair_*_word_level.json",
        transcripts_dir / f"merged_g{gid}_word_level.json",
        base_p / "metadata_blueprints" / f"group_{gid}_words.json",
    ]

    if not force:
        for cand in candidate_jsons:
            if cand.exists() and cand.stat().st_size > 10:
                try:
                    with open(cand, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if data.get("words"):
                        return data
                except Exception:
                    pass

    # Find audio file to transcribe
    audio_file = find_group_audio_file(base_folder, group_id)
    if not audio_file or not audio_file.exists():
        print(f"[WordTranscriber] No audio file found for group {gid} in {base_folder}")
        return None

    if transcribe_audio is None:
        print("[WordTranscriber] transcribe_audio function not available")
        return None

    try:
        print(f"[WordTranscriber] Transcribing group {gid} audio: {audio_file.name}...")
        data = transcribe_audio(str(audio_file), str(target_json))
        return data
    except Exception as e:
        print(f"[WordTranscriber] Failed to transcribe group {gid}: {e}")
        return None


def find_keyword_spoken_time(
    transcript: Dict[str, Any],
    keyword_or_phrase: str,
    start_search_time: float = 0.0
) -> Optional[float]:
    """
    Finds the exact start time in seconds when a word or phrase is spoken.
    """
    if not transcript or not transcript.get("words"):
        return None

    phrase_words = [w.lower().strip(",.?!;:\"'") for w in keyword_or_phrase.split() if w.strip()]
    if not phrase_words:
        return None

    words_list = transcript["words"]
    n_phrase = len(phrase_words)

    for i in range(len(words_list) - n_phrase + 1):
        w_start = float(words_list[i].get("start", 0.0))
        if w_start < start_search_time - 0.2:
            continue

        match = True
        for j in range(n_phrase):
            actual_w = words_list[i + j].get("word", "").lower().strip(",.?!;:\"'")
            if actual_w != phrase_words[j] and phrase_words[j] not in actual_w:
                match = False
                break

        if match:
            return round(w_start, 3)

    return None


def extract_key_spoken_anchors(
    transcript: Dict[str, Any],
    min_word_len: int = 4
) -> List[Tuple[float, str]]:
    """
    Extracts high-signal anchors (timestamp, phrase/word) from transcript
    for injection into LLM prompts.
    """
    if not transcript or not transcript.get("words"):
        return []

    anchors = []
    stopwords = {
        "this", "that", "these", "those", "with", "from", "have", "they",
        "will", "what", "when", "where", "which", "there", "their", "about",
        "would", "could", "should", "some", "other", "into", "more", "also"
    }

    words = transcript["words"]
    for w in words:
        clean = w.get("word", "").strip(",.?!;:\"'").lower()
        if len(clean) >= min_word_len and clean not in stopwords:
            anchors.append((float(w.get("start", 0.0)), w.get("word", "").strip()))

    return anchors
