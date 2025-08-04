# api_server.py
import shutil
from flask import Flask, request, jsonify
from flask_cors import CORS
import face_recognition
import tempfile
import os
from datetime import datetime
import numpy as np
import re

app = Flask(__name__)
# Enhanced CORS configuration
CORS(app,
     resources={r"/*": {"origins": "*"}},
     supports_credentials=False,
     allow_headers=["Content-Type", "ngrok-skip-browser-warning"],
     methods=["GET", "POST", "OPTIONS"]
)
# In-memory storage for known faces (replace with database in production)
known_faces = {}  # format: {'user1': encoding, 'user2': encoding}
known_names = []

# Directory to store known faces
KNOWN_FACES_DIR = 'user_images'

# Confidence threshold (adjust as needed)
CONFIDENCE_THRESHOLD = 0.5

def load_known_faces():
    """Load known faces from a directory and populates the in-memory lists."""
    global known_faces, known_names
    
    print("Loading known faces...")
    if not os.path.exists(KNOWN_FACES_DIR):
        os.makedirs(KNOWN_FACES_DIR)
        return
    
    for filename in os.listdir(KNOWN_FACES_DIR):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            try:
                # Sanitize the name from filename
                name = os.path.splitext(filename)[0]
                if name in known_names: continue # Skip if already loaded

                image_path = os.path.join(KNOWN_FACES_DIR, filename)
                image = face_recognition.load_image_file(image_path)
                encodings = face_recognition.face_encodings(image)
                
                if encodings:
                    known_faces[name] = encodings[0]
                    known_names.append(name)
                    print(f"Loaded face for {name}")
                else:
                    print(f"Warning: No face found in {filename}")
            except Exception as e:
                print(f"Error loading {filename}: {str(e)}")

# Load known faces at startup
load_known_faces()
@app.route('/register', methods=['OPTIONS'])
def register_options():
    return jsonify({}), 200

@app.route('/process_attendance', methods=['OPTIONS'])
def attendance_options():
    return jsonify({}), 200
@app.route('/register', methods=['POST'])
def register():
    """Registers a new user by saving their face."""
    if 'file' not in request.files or 'name' not in request.form:
        return jsonify({'error': 'Missing name or file in request'}), 400
    
    file = request.files['file']
    name = request.form['name']

    if not name:
        return jsonify({'error': 'Name cannot be empty'}), 400
    
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    if safe_name in known_names:
        return jsonify({'error': f'User "{safe_name}" already exists'}), 400

    # Create a temporary file to work with
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
    try:
        file.save(temp_file.name)
        
        # IMPORTANT: Close the file handle here before processing
        temp_file.close()

        # Load the image and find faces
        new_image = face_recognition.load_image_file(temp_file.name)
        new_encodings = face_recognition.face_encodings(new_image)

        if not new_encodings:
            return jsonify({'error': 'No face found in the provided image. Please try again.'}), 400
        
        if len(new_encodings) > 1:
            return jsonify({'error': 'Multiple faces detected. Please provide an image with only one face.'}), 400

        # Save the file permanently
        filename = f"{safe_name}.jpg"
        permanent_path = os.path.join(KNOWN_FACES_DIR, filename)
        shutil.move(temp_file.name, permanent_path) # Using shutil.move is more robust

        # Update the in-memory known faces
        known_faces[safe_name] = new_encodings[0]
        known_names.append(safe_name)
        
        print(f"Successfully registered new user: {safe_name}")
        return jsonify({
            'status': 'success', 
            'message': f'User "{safe_name}" registered successfully.'
        })

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    finally:
        # Now, this cleanup will reliably work because the handle is closed.
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

@app.route('/process_attendance', methods=['POST'])
def process_attendance():
    load_known_faces()  # Refresh known faces before processing
    print(f"Debug: Loaded {len(known_names)} users: {known_names}")  # Debug
    if 'file' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['file']
    
    # Create a temporary file to work with
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
    try:
        file.save(temp_file.name)
        
        # IMPORTANT: Close the file handle here before processing
        temp_file.close()

        # Load the uploaded image
        unknown_image = face_recognition.load_image_file(temp_file.name)
        face_locations = face_recognition.face_locations(unknown_image)
        
        if not face_locations:
            return jsonify({'results': []})
        
        face_encodings = face_recognition.face_encodings(unknown_image, face_locations)
        
        results = []
        if not known_names:
             for _ in face_encodings:
                results.append({'name': 'Unknown', 'time': '', 'status': 'not_recognized'})
             return jsonify({'results': results})

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(
                list(known_faces.values()), 
                face_encoding,
                tolerance=CONFIDENCE_THRESHOLD
            )
            
            name = "Unknown"
            status = "not_recognized"
            time_str = ""
            
            face_distances = face_recognition.face_distance(list(known_faces.values()), face_encoding)
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_names[best_match_index]
                    status = "recognized"
                    time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            results.append({
                'name': name,
                'time': time_str,
                'status': status
            })
        
        return jsonify({'results': results})
        
    except Exception as e:
        return jsonify({'error': f'Error processing image: {str(e)}'}), 500
        
    finally:
        # Now, this cleanup will reliably work because the handle is closed
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)