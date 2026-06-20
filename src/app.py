import os
import re
import sys
import subprocess
from flask import Flask, request, jsonify, send_from_directory

# Add src folder to system path to ensure easy imports
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.append(src_dir)

from llm_client import generate_manim_code, extract_python_code
from pipeline import find_manim_class_name

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='')

# Absolute paths to key directories
PROJECT_ROOT = os.path.abspath(os.path.join(src_dir, '..'))
MEDIA_DIR = os.path.join(PROJECT_ROOT, 'media')

@app.route('/')
def index():
    """Serves the main application page."""
    return app.send_static_file('index.html')

@app.route('/media/<path:filename>')
def serve_media(filename):
    """Serves the generated video files directly from Manim's media folder."""
    return send_from_directory(MEDIA_DIR, filename)

def scan_for_video(class_name):
    """
    Helper to search the media directory for the compiled video file.
    Provides a fallback mechanism in case directories differ from the expected structure.
    """
    videos_dir = os.path.join(MEDIA_DIR, "videos", "generated_scene")
    if not os.path.exists(videos_dir):
        return None
        
    # Standard path we expect
    expected_rel = f"videos/generated_scene/480p15/{class_name}.mp4"
    if os.path.exists(os.path.join(MEDIA_DIR, expected_rel)):
        return expected_rel

    # Fallback walk search
    for root, dirs, files in os.walk(videos_dir):
        for file in files:
            if file.endswith('.mp4'):
                # Prioritize file matching the class name
                if class_name.lower() in file.lower():
                    abs_path = os.path.join(root, file)
                    return os.path.relpath(abs_path, MEDIA_DIR).replace('\\', '/')
                    
    # Return first mp4 found in generated_scene as last resort
    for root, dirs, files in os.walk(videos_dir):
        for file in files:
            if file.endswith('.mp4'):
                abs_path = os.path.join(root, file)
                return os.path.relpath(abs_path, MEDIA_DIR).replace('\\', '/')
                
    return None

@app.route('/api/generate', methods=['POST'])
def generate():
    """Endpoint that handles the animation concept submission, compilation, and video resolution."""
    data = request.json
    if not data or 'prompt' not in data:
        return jsonify({'error': 'Missing prompt parameter'}), 400
        
    prompt = data['prompt']
    print(f"\n[API] Received prompt: '{prompt}'")
    
    try:
        # 1. Call Gemini to generate the animation code
        print("[API] Requesting Manim code from Gemini...")
        raw_response = generate_manim_code(prompt)
        if not raw_response:
            return jsonify({'error': 'Failed to obtain code from Gemini API. Check API keys and network.'}), 500
            
        # 2. Extract clean Python code
        clean_code = extract_python_code(raw_response)
        
        # 3. Write code to generated_scene.py
        scene_file = os.path.join(PROJECT_ROOT, "generated_scene.py")
        try:
            with open(scene_file, "w", encoding="utf-8") as f:
                f.write(clean_code)
        except IOError as e:
            return jsonify({'error': f'Failed to write scene file: {str(e)}'}), 500
            
        # 4. Extract generated Scene class name
        class_name = find_manim_class_name(clean_code)
        print(f"[API] Parsed Scene class name: '{class_name}'")
        
        # 5. Compile the scene using Manim subprocess
        manim_executable = os.path.join(PROJECT_ROOT, "venv", "Scripts", "manim")
        if not os.path.exists(manim_executable + ".exe") and not os.path.exists(manim_executable):
            manim_executable = "manim"
            
        command = [
            manim_executable,
            "-ql",
            "--media_dir", MEDIA_DIR,
            scene_file,
            class_name
        ]
        
        print(f"[API] Compiling scene via subprocess: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, cwd=PROJECT_ROOT)
        
        if result.returncode != 0:
            print("[API Error] Manim compilation failed.")
            print(result.stderr)
            return jsonify({
                'error': 'Manim compilation failed',
                'details': result.stderr or result.stdout
            }), 500
            
        # 6. Locate the video file path
        video_rel_path = scan_for_video(class_name)
        if not video_rel_path:
            return jsonify({'error': 'Compilation reported success, but the resulting video file could not be located'}), 500
            
        video_url = f"/media/{video_rel_path}"
        print(f"[API Success] Video generated successfully: {video_url}")
        
        return jsonify({
            'success': True,
            'class_name': class_name,
            'video_url': video_url,
            'code': clean_code
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Internal Server Error: {str(e)}'}), 500

if __name__ == '__main__':
    print("==========================================================")
    print("          AI ANIMATION WEB PLATFORM LOCAL SERVER          ")
    print("==========================================================")
    print("Serving UI at: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
