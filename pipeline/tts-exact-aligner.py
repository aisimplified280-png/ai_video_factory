#!/usr/bin/env python3
"""
pipeline/tts-exact-aligner.py

Generate one narration track and exact WordBoundary timings from Edge-TTS.
Offsets are converted from 100-nanosecond ticks to seconds.
"""

import asyncio
import json
import os
import argparse
import edge_tts

TICKS_PER_SECOND = 10_000_000


async def generate_with_exact_timing(
    text: str,
    voice: str,
    rate: str,
    out_audio: str,
    out_words: str,
):
    # Edge-TTS can return either word or sentence boundaries. WordBoundary is
    # required so scene actions and captions share the same timing source.
    communicate = edge_tts.Communicate(
        text,
        voice,
        rate=rate,
        boundary="WordBoundary",
    )

    word_cues = []
    audio_chunks = []

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            start_sec = chunk["offset"] / TICKS_PER_SECOND
            duration_sec = chunk["duration"] / TICKS_PER_SECOND
            word_cues.append({
                "text": chunk["text"],
                "startTime": round(start_sec, 5),
                "endTime": round(start_sec + duration_sec, 5),
                "duration": round(duration_sec, 5),
            })

    if not audio_chunks:
        raise RuntimeError("Edge-TTS returned no audio chunks.")
    if not word_cues:
        raise RuntimeError(
            "Edge-TTS returned no WordBoundary metadata. "
            "Cannot safely align captions and scene choreography."
        )

    os.makedirs(os.path.dirname(os.path.abspath(out_audio)), exist_ok=True)
    with open(out_audio, "wb") as audio_file:
        for chunk in audio_chunks:
            audio_file.write(chunk)

    os.makedirs(os.path.dirname(os.path.abspath(out_words)), exist_ok=True)
    with open(out_words, "w", encoding="utf-8") as timing_file:
        json.dump(word_cues, timing_file, indent=2, ensure_ascii=False)

    print(
        f"[TTS-Aligner] Success: {len(word_cues)} exact word boundaries "
        f"recorded to {out_words}"
    )


def main():
    parser = argparse.ArgumentParser(description="Edge-TTS exact word aligner")
    parser.add_argument("--text", required=True, help="Full narration text")
    parser.add_argument("--voice", default="en-US-ChristopherNeural", help="Voice model")
    parser.add_argument("--rate", default="+4%", help="Speech rate")
    parser.add_argument("--out-audio", required=True, help="Destination MP3 audio file")
    parser.add_argument("--out-words", required=True, help="Destination word timing JSON")
    args = parser.parse_args()

    asyncio.run(
        generate_with_exact_timing(
            args.text,
            args.voice,
            args.rate,
            args.out_audio,
            args.out_words,
        )
    )


if __name__ == "__main__":
    main()
