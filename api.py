import os

from flask import Flask, request, jsonify

from services.question_service import QuestionService
from services.exam_data_loader import ExamDataLoader
from services.azure_ai_client import AzureAIClient

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

@app.route("/api/questions/<exam>/<yesno>/<qualitative>")
def questions(exam, yesno, qualitative):
    questions = question_service.generate_diagnostic_questions(exam, yesno, qualitative)
    return jsonify(questions), 200

if __name__ == "__main__":
    app.run(debug=True)