import os
import shutil
from flask import Flask, request, jsonify, send_from_directory, abort

app = Flask(__name__)

# Ρυθμίσεις
# Στο Render (Free tier) τα αρχεία χάνονται αν επανεκκινήσει ο server,
# αλλά για άμεση μεταφορά (Scan -> Print) μας αρκεί.
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
API_KEY = os.environ.get("API_KEY", "EasyMailSecret123!")  # Default αν δεν οριστεί στο Render

# Δημιουργία φακέλου αν δεν υπάρχει
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def check_auth():
    """Ελέγχει αν το API Key είναι σωστό"""
    key = request.headers.get("X-API-KEY") or request.args.get("key")
    if key != API_KEY:
        abort(401, description="Unauthorized: Wrong API Key")

@app.route('/')
def home():
    return "✅ EasyMail Transfer Server is Running!"

# --- UPLOAD (Ανέβασμα αρχείου) ---
@app.route('/api/upload', methods=['POST'])
def upload_file():
    check_auth()
    
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file part"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "No selected file"}), 400

    if file:
        # Save file
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        return jsonify({
            "success": True, 
            "message": f"File {file.filename} uploaded successfully",
            "size": os.path.getsize(filepath)
        })

# --- LIST (Λίστα αρχείων) ---
@app.route('/api/files', methods=['GET'])
def list_files():
    check_auth()
    try:
        files = os.listdir(UPLOAD_FOLDER)
        return jsonify({"success": True, "files": files})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# --- DOWNLOAD (Κατέβασμα αρχείου) ---
@app.route('/api/files/<filename>', methods=['GET'])
def download_file(filename):
    check_auth()
    try:
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"success": False, "message": "File not found"}), 404

# --- DELETE (Διαγραφή αρχείου) ---
@app.route('/api/files/<filename>', methods=['DELETE'])
def delete_file(filename):
    check_auth()
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({"success": True, "message": "Deleted"})
        else:
            return jsonify({"success": False, "message": "File not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# --- FLUSH (Διαγραφή ΟΛΩΝ - Για καθαρισμό) ---
@app.route('/api/flush', methods=['POST', 'GET'])
def flush_files():
    check_auth()
    try:
        count = 0
        for f in os.listdir(UPLOAD_FOLDER):
            path = os.path.join(UPLOAD_FOLDER, f)
            try:
                if os.path.isfile(path):
                    os.remove(path)
                    count += 1
            except Exception:
                pass
        return jsonify({"success": True, "message": f"Flushed {count} files"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
