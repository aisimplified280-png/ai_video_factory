"""Test edge-tts voices"""
import edge_tts
import asyncio

text = "What if the secret to artificial intelligence wasn't smarter code, but simply feeding a furnace infinite data?"

voices = [
    'en-US-JennyNeural',
    'en-US-GuyNeural', 
    'en-US-SarahNeural',
    'en-US-AriaNeural',
    'en-US-EmilyNeural',
]

for voice in voices:
    try:
        communicate = edge_tts.Communicate(text, voice)
        asyncio.run(communicate.save('test_voice.mp3'))
        print(f'{voice}: OK')
    except Exception as e:
        print(f'{voice}: FAILED - {e}')