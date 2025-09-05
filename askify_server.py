from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import io
from PIL import Image

# Import your main functions from askify_main.py
from askify_main import (
    ask_gemini,
    search_serper,
    save_history,
    is_live_answer_query,
    take_screenshot_and_process,
    reader
)

app = Flask(__name__)
CORS(app)  # allow extension to talk to server

# --- Endpoints ---

@app.route("/process/query", methods=["POST"])
def process_query():
    """Handle text query"""
    data = request.json
    query = data.get("query", "")
    if not query.strip():
        return jsonify({"error": "Empty query"}), 400

    answer = search_serper(query) if is_live_answer_query(query) else ask_gemini(query)
    save_history(query, answer)
    return jsonify({"answer": answer})


@app.route("/process/ocr", methods=["POST"])
def process_ocr():
    """Handle OCR from screenshot image"""
    data = request.json
    image_b64 = data.get("image")
    if not image_b64:
        return jsonify({"error": "No image provided"}), 400

    try:
        image_bytes = base64.b64decode(image_b64)
        image = Image.open(io.BytesIO(image_bytes))
        results = reader.readtext(np.array(image))
        text = " ".join([res[1] for res in results]).strip()

        if text:
            answer = search_serper(text) if is_live_answer_query(text) else ask_gemini(text)
            save_history(text, answer)
            return jsonify({"answer": answer, "text": text})
        else:
            return jsonify({"error": "No text detected"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/process/dragdrop", methods=["POST"])
def process_dragdrop():
    """Handle drag-drop text"""
    data = request.json
    text = data.get("text", "")
    if not text.strip():
        return jsonify({"error": "Empty drag-drop input"}), 400

    answer = search_serper(text) if is_live_answer_query(text) else ask_gemini(text)
    save_history(text, answer)
    return jsonify({"answer": answer})


@app.route("/process/voice", methods=["POST"])
def process_voice():
    """Handle voice transcription"""
    # (For now, extension sends audio as text; later we can accept audio files)
    data = request.json
    text = data.get("text", "")
    if not text.strip():
        return jsonify({"error": "Empty voice input"}), 400

    answer = search_serper(text) if is_live_answer_query(text) else ask_gemini(text)
    save_history(text, answer)
    return jsonify({"answer": answer})


@app.route("/")
def health_check():
    return jsonify({"status": "Askify server running ✅"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
