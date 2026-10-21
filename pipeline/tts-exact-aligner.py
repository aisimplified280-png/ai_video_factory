#!/usr/bin/env python3
"""
pipeline/tts-exact-aligner.py
Deterministic neural speech generation with exact millisecond sentence boundary timing.
Extracts true audio timestamps directly from the Edge-TTS stream.
"""

import sys
import os
import asyncio
import json
import argparse
import edge_tts

async def generate_with_exact_timing(text: str, voice: str, rate: str, out_audio: str, out_timing: str):
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    
    sentence_cues = []
    audio_chunks = []
    
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])
        elif chunk["type"] == "SentenceBoundary":
            # 1 second = 10,000,000 ticks in Edge-TTS
            start_sec = round(chunk["offset"] / 10_000_000.0, 4)
            dur_sec = round(chunk["duration"] / 10_000_000.0, 4)
            end_sec = round(start_sec + dur_sec, 4)
            
            sentence_cues.append({
                "text": chunk["text"],
                "startTime": start_sec,
                "endTime": end_sec,
                "duration": dur_sec,
            })
            
    # Write audio file
    os.makedirs(os.path.dirname(os.path.abspath(out_audio)), exist_ok=True)
    with open(out_audio, "wb") as f:
        for chunk in audio_chunks:
            f.write(chunk)
            
    # Write timing JSON
    os.makedirs(os.path.dirname(os.path.abspath(out_timing)), exist_ok=True)
    with open(out_timing, "w", encoding="utf-8") as f:
        json.dump(sentence_cues, f, indent=2, ensure_ascii=False)
        
    print(f"[TTS-Aligner] Success: {len(sentence_cues)} exact sentence boundaries recorded to {out_timing}")

def main():
    parser = argparse.ArgumentParser(description="Edge-TTS exact speech aligner")
    parser.add_argument("--text", required=True, help="Full narration text")
    parser.add_argument("--voice", default="en-US-ChristopherNeural", help="Voice model")
    parser.add_argument("--rate", default="+4%", help="Speech rate")
    parser.add_argument("--out-audio", required=True, help="Destination mp3 audio file")
    parser.add_argument("--out-timing", required=True, help="Destination timing JSON file")
    
    args = parser.parse_args()
    asyncio.run(generate_with_exact_timing(args.text, args.voice, args.rate, args.out_audio, args.out_timing))

if __name__ == "__main__":
    main()
