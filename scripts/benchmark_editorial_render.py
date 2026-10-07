import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from create_short import run_pipeline

TOPICS = [
    ("How Uber Works", "editorial_explainer", 18.0),
    ("How ChatGPT Agents Work", "editorial_explainer", 28.0),
    ("Why AI Models Need More Compute", "editorial_explainer", 30.0),
    ("OpenAI Launches a New AI Model", "editorial_explainer", 25.0),
    ("How ChatGPT Agents Work", "editorial_viral", 20.0),
]

for topic, style, duration in TOPICS:
    print(f"=== RUNNING: {topic} [{style}] ===")
    result = run_pipeline(topic, style=style, duration=duration, music="none", visual_debug=True)
    print(f"OUTPUT: {result}")
