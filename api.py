import os
from dotenv import load_dotenv

from flask import Flask, request, jsonify
from flask_cors import CORS

from services.question_service import QuestionService
from services.exam_data_loader import ExamDataLoader
from services.azure_ai_client import AzureAIClient

load_dotenv()
exam_data_loader = ExamDataLoader(json_file_path=os.getenv("EXAM_DATA_JSON_PATH"))
ai_client = AzureAIClient(
    endpoint_text_audio_whisper=os.getenv("AZURE_OPENAI_ENDPOINT_TEXT_AUDIO_WHISPER"),
    api_key_text_audio_whisper=os.getenv("AZURE_OPENAI_API_KEY_TEXT_AUDIO_WHISPER"),
    endpoint_image=os.getenv("AZURE_OPENAI_ENDPOINT_IMAGE"),
    api_key_image=os.getenv("AZURE_OPENAI_API_KEY_IMAGE"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    deployment_text=os.getenv("AZURE_OPENAI_DEPLOYMENT_TEXT"),
    deployment_image=os.getenv("AZURE_OPENAI_DEPLOYMENT_IMAGE"),
    deployment_audio=os.getenv("AZURE_OPENAI_DEPLOYMENT_AUDIO"),
    deployment_whisper=os.getenv("AZURE_OPENAI_DEPLOYMENT_WHISPER")
)

question_service = QuestionService(exam_data_loader, ai_client)

app = Flask(__name__)
CORS(app)

@app.route("/api/questions/<examCode>/<yesNoQuestions>/<qualitativeQuestions>")
def questions(examCode, yesNoQuestions, qualitativeQuestions):
    questions = question_service.generate_diagnostic_questions(examCode, yesNoQuestions, qualitativeQuestions)
    return jsonify(questions), 200

@app.route("/api/feedback", methods=["POST"])
def feedback():
    return jsonify({}), 200

@app.route("/api/ask", methods=["POST"])
def ask():
    body = request.get_json()
    messages = [
        {"role": "system", "content": "You are an expert on Microsoft Azure certification exams."},
        {"role": "user", "content": body.get("question")}
    ]
    response = ai_client.call_chat_completion(messages=messages, max_tokens=4096, temperature=0.7)
    return response, 200

if __name__ == "__main__":
    app.run(debug=True)