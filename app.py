import streamlit as st
from pathlib import Path
import os
from dotenv import load_dotenv
import json

# Import your service classes
from services.exam_data_loader import ExamDataLoader
from services.azure_ai_client import AzureAIClient
from services.question_service import QuestionService
from services.simulation_service import SimulationService
from services.feedback_service import FeedbackService
from services.flashcard_export_service import FlashcardExportService
from services.concept_extractor import ConceptExtractor
from services.image_generation_service import ImageGenerationService
from services.podcast_generation_service import PodcastGenerationService
from pathlib import Path

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

st.title("Hello, traveler!")

# Sidebar navigation
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to", ["Home", "Generate Diagnostic Questions", "Conduct Simulation", "Feedback and Reinforcement", "Ask a Question", "Exit"])

# Home Page
if menu == "Home":
    st.write("Welcome to the Avanade's Azure Buddy. Use the navigation menu to select an option.")
    image_path = Path(__file__).parent / 'utils' / 'assets' / 'avanade_buddy.png'
    st.image(image_path, caption="Azure Certification Coach", use_container_width=True)

# Generate Diagnostic Questions
elif menu == "Generate Diagnostic Questions":
    available_exams = exam_data_loader.get_available_exams()
    if available_exams:
        exam_options = {f"{code} - {name}": code for code, name in available_exams}
        selected_exam = st.selectbox("Select an Azure Certification Exam:", list(exam_options.keys()))
        num_yes_no = st.number_input("Number of Yes/No questions:", min_value=1, value=30)
        num_qualitative = st.number_input("Number of Qualitative questions:", min_value=1, value=30)
        if st.button("Generate Questions"):
            selected_exam_code = exam_options[selected_exam]
            question_service = QuestionService(exam_data_loader, ai_client)
            question_service.generate_diagnostic_questions(selected_exam_code, num_yes_no, num_qualitative)
            st.success(f"Generated {num_yes_no + num_qualitative} questions for {selected_exam_code}.")
    else:
        st.error("No exam data loaded. Please check the content.json path or its content.")

# Conduct Simulation
elif menu == "Conduct Simulation":
    simulation_service = SimulationService()
    simulation_service.conduct_simulation()
    st.success("Simulation conducted successfully.")

# Feedback and Reinforcement
elif menu == "Feedback and Reinforcement":
    result_files = list(Path('files').glob('*_results.json'))
    if result_files:
        result_file = st.selectbox("Select a results file to analyze:", [file.name for file in result_files])
        if st.button("Analyze Results"):
            selected_result_file_path = Path('files') / result_file
            exam_code_for_feedback = selected_result_file_path.stem.split('_')[0]
            feedback_service = FeedbackService(ai_client)
            feedback_service.provide_feedback_and_new_questions(exam_code_for_feedback)
            st.success(f"Feedback and new questions provided for {exam_code_for_feedback}.")
    else:
        st.error("No simulation results found. Please conduct a simulation first.")

# Ask a General Question
elif menu == "Ask a Question":
    question = st.text_input("What would you like to know about Azure Certifications?")
    if st.button("Submit"):
        messages = [
            {"role": "system", "content": "You are an expert on Microsoft Azure certification exams."},
            {"role": "user", "content": question}
        ]
        response = ai_client.call_chat_completion(messages=messages, max_tokens=4096, temperature=0.7)
        if response:
            st.write(f"**AI Assistant:** {response}")
        else:
            st.error("Could not get a response from the AI assistant.")

# Exit
elif menu == "Exit":
    st.write("Thank you for using the Avanade's Azure Certification Buddy. Goodbye!")