"""Concatenate narration audio files."""
import subprocess
from pathlib import Path

# Concatenate all 6 narration audio files
audio_files = [
    'projects/proj_3e27bd7a/audio/narration_scene_01.mp3',
    'projects/proj_3e27bd7a/audio/narration_scene_02.mp3',
    'projects/proj_3e27bd7a/audio/narration_scene_03.mp3',
    'projects/proj_3e27bd7a/audio/narration_scene_05.mp3',
    'projects/proj_3e27bd7a/audio/narration_scene_06.mp3',
]

# Wait, I had scene_05 twice and missed scene_05 properly. Let me fix:
audio_files = [
    'projects/proj_3e27bd7a/audio/narration_scene_01.mp3',
    'projects/proj_3e27bd7a/audio/narration_scene_02.mp3',
    'projects/proj_3e27bd7a/audio/narration_scene_03.mp3',
    'projects/proj_3e27bd7a/audio/narration_scene_04.mp3',
    'projects/proj_3e27bd7a/audio/narration_scene_05.mp3',
    'projects/proj_3e27bd7a/audio/narration_scene_06.mp3',
]

# Create a concat file
concat_file = Path('projects/proj_3e27bd7a/audio/concat.txt')
with open(concat_file, 'w') as f:
    for af in audio_files:
        f.write('file ' + af + '\n')

# Use ffmpeg to concatenate
cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat_file),
       '-c', 'copy', str(Path('projects/proj_3e27bd7a/audio/all_narration.mp3'))]
result = subprocess.run(cmd, capture_output=True, text=True)
print('Return code:', result.returncode)
print('Stderr:', result.stderr[:200] if result.stderr else 'None')

# Check the concatenated file
concat_path = Path('projects/proj_3e27bd7a/audio/all_narration.mp3')
if concat_path.exists():
    print('Concatenated file size:', concat_path.stat().st_size)
    # Check duration
    result2 = subprocess.run(['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', str(concat_path)], capture_output=True, text=True)
    fmt = json.loads(result2.stdout).get('format', {})
    print('Duration:', fmt.get('duration'))
"