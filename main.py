# main.py
import sys
from pathlib import Path
import os
import json

# TODO: Remove after adding poetry as default environment manager
from dotenv import load_dotenv

# Adjust the path to import the new service classes
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

# Import the new classes
from services.exam_data_loader import ExamDataLoader
from services.azure_ai_client import AzureAIClient
from services.question_service import QuestionService
from services.simulation_service import SimulationService
from services.feedback_service import FeedbackService
from services.flashcard_export_service import FlashcardExportService
from services.concept_extractor import ConceptExtractor
from services.image_generation_service import ImageGenerationService
from services.podcast_generation_service import PodcastGenerationService


def display_menu():
    print("\nAzure Certification Coach Menu:")
    print("1. Generate Diagnostic Questions for an Exam")
    print("2. Conduct a Simulation (Answer Questions)")
    print("3. Get Feedback and Concept Reinforcement Options")
    print("4. Ask a General Question about Azure Certifications")
    print("5. Exit")

def display_reinforcement_menu():
    print("\nConcept Reinforcement Options:")
    print("1. Export Flashcards (CSV from original content)")
    print("2. Generate Coloring Images")
    print("3. Generate Podcast")
    print("4. Generate Podcast + Coloring Images")
    print("5. Back to Main Menu")

def display_image_styles_menu():
    print("\nSelect a Coloring Image Style:")
    print("1. Simple Line Art")
    print("2. Architectural Blueprint")
    print("3. Nature/Everyday Analogy")
    print("4. Character/Mascot-Driven")
    print("5. Abstract Geometric/Flowchart")
    print("6. Back to Reinforcement Options")

def main():
    load_dotenv()
    
    # Display demo mode status
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    mode_text = "DEMO MODE" if demo_mode else "LIVE MODE"
    print(f"\n=== Welcome to Avanade's Azure Certification Buddy (Neuropath) [{mode_text}] ===")
        
    files_dir = Path("files")
    files_dir.mkdir(parents=True, exist_ok=True)
    (files_dir / "images").mkdir(parents=True, exist_ok=True)
    (files_dir / "podcasts").mkdir(parents=True, exist_ok=True)
    print(f"Ensured '{files_dir}' and its subdirectories exist for file storage.")

    try:
        exam_data_loader = ExamDataLoader(json_file_path=os.getenv("EXAM_DATA_JSON_PATH"))
        # Pass distinct endpoint and API key variables
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
    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("Please ensure all necessary variables are set in your .env file.")
        return

    question_service = QuestionService(exam_data_loader, ai_client)
    simulation_service = SimulationService()
    feedback_service = FeedbackService(ai_client)
    flashcard_export_service = FlashcardExportService()
    concept_extractor = ConceptExtractor()
    image_generation_service = ImageGenerationService(ai_client)
    podcast_generation_service = PodcastGenerationService(ai_client)

    while True:
        display_menu()
        choice = input("Enter your choice: ")

        if choice == '1':
            available_exams = exam_data_loader.get_available_exams()
            if not available_exams:
                print("No exam data loaded. Please check content.json path or its content.")
                continue

            print("Available Azure Certification Exams:")
            for i, (code, name) in enumerate(available_exams):
                print(f"{i + 1}. {code} - {name}")

            selected_exam_code = None
            while True:
                try:
                    exam_choice = input("Enter the number of the exam you want to select: ")
                    selected_index = int(exam_choice) - 1
                    if 0 <= selected_index < len(available_exams):
                        selected_exam_code = available_exams[selected_index][0]
                        print(f"You selected: {selected_exam_code}")
                        break
                    else:
                        print("Invalid number. Please try again.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
            
            if selected_exam_code:
                try:
                    # Check if we're in demo mode
                    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
                    num_yes_no = int(input("Enter number of Yes/No questions (e.g., 30): "))
                    
                    if demo_mode:
                        # Demo mode only supports yes/no questions
                        num_qualitative = 0
                        print("Note: Demo mode currenlty only supports Yes/No questions. Qualitative questions set to 0.")
                    else:
                        num_qualitative = int(input("Enter number of Qualitative questions (e.g., 30): "))
                    
                    question_service.generate_diagnostic_questions(selected_exam_code, num_yes_no, num_qualitative)
                except ValueError:
                    print("Invalid input for number of questions. Please enter a number.")
            else:
                print("No exam selected for question generation.")

        elif choice == '2':
            simulation_service.conduct_simulation()

        elif choice == '3':
            result_files = list(Path('files').glob('*_results.json'))
            if not result_files:
                print("No simulation results found to provide feedback on. Please conduct a simulation first.")
                continue

            print("\nAvailable Simulation Results for Feedback:")
            for i, file_path in enumerate(result_files):
                print(f"{i + 1}. {file_path.name}")

            selected_result_file_path = None
            while True:
                try:
                    choice_result = input("Enter the number of the results file you want to analyze: ")
                    selected_index_result = int(choice_result) - 1
                    if 0 <= selected_index_result < len(result_files):
                        selected_result_file_path = result_files[selected_index_result]
                        break
                    else:
                        print("Invalid number. Please try again.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
            
            if selected_result_file_path:
                exam_code_for_feedback = selected_result_file_path.name.split('_')[0]
                
                feedback_service.provide_feedback_and_new_questions(exam_code_for_feedback)

                targeted_questions_file = Path("files") / f"{exam_code_for_feedback}_targeted_questions.json"
                
                targeted_questions_data = {}
                if targeted_questions_file.exists():
                    try:
                        with open(targeted_questions_file, 'r', encoding='utf-8') as f:
                            targeted_questions_data = json.load(f)
                    except json.JSONDecodeError:
                        print(f"Error: Could not decode JSON from '{targeted_questions_file}'. File might be corrupted.")
                        targeted_questions_data = {}

                concepts_for_reinforcement = []
                if targeted_questions_data and targeted_questions_data.get("questions"):
                    concepts_for_reinforcement = concept_extractor.extract_concepts_from_targeted_questions(targeted_questions_data)
                    if not concepts_for_reinforcement:
                        print("No specific concepts could be extracted from targeted questions. Falling back to general exam concepts.")
                        concepts_for_reinforcement = exam_data_loader.get_structured_exam_content(exam_codes=[exam_code_for_feedback])
                        concepts_for_reinforcement = [item['question'].replace("What is ", "").replace("Explain ", "").replace(" in Azure?", "").replace(".", "").strip() for item in concepts_for_reinforcement]
                        concepts_for_reinforcement = [c for c in concepts_for_reinforcement if c]
                else:
                    print("No targeted questions found. Using general exam concepts for reinforcement.")
                    concepts_for_reinforcement = exam_data_loader.get_structured_exam_content(exam_codes=[exam_code_for_feedback])
                    concepts_for_reinforcement = [item['question'].replace("What is ", "").replace("Explain ", "").replace(" in Azure?", "").replace(".", "").strip() for item in concepts_for_reinforcement]
                    concepts_for_reinforcement = [c for c in concepts_for_reinforcement if c]
                
                if not concepts_for_reinforcement:
                    print("No concepts available for reinforcement. Please ensure exam data is loaded and questions are generated/simulated.")
                    continue


                reinforce_choice = ""
                while reinforce_choice != '5':
                    display_reinforcement_menu()
                    reinforce_choice = input("Enter your reinforcement choice: ")

                    if reinforce_choice == '1':
                        print("\nGenerating Flashcards from original exam content...")
                        structured_content_for_flashcards = exam_data_loader.get_structured_exam_content(exam_codes=[exam_code_for_feedback])
                        if structured_content_for_flashcards:
                            flashcard_filename = f"{exam_code_for_feedback}_flashcards.csv"
                            flashcard_export_service.export_to_csv(structured_content_for_flashcards, flashcard_filename)
                        else:
                            print("No structured content found for flashcard generation.")

                    elif reinforce_choice == '2':
                        image_style_choice = ""
                        selected_style_name = ""
                        while image_style_choice not in ['1', '2', '3', '4', '5']:
                            display_image_styles_menu()
                            image_style_choice = input("Select an image style: ")
                            if image_style_choice == '1': selected_style_name = "Simple Line Art"
                            elif image_style_choice == '2': selected_style_name = "Architectural Blueprint"
                            elif image_style_choice == '3': selected_style_name = "Nature/Everyday Analogy"
                            elif image_style_choice == '4': selected_style_name = "Character/Mascot-Driven"
                            elif image_style_choice == '5': selected_style_name = "Abstract Geometric/Flowchart"
                            elif image_style_choice == '6': break
                            else: print("Invalid style choice.")
                        
                        if selected_style_name:
                            image_generation_service.generate_coloring_images(concepts_for_reinforcement, selected_style_name, exam_code_for_feedback)

                    elif reinforce_choice == '3':
                        podcast_generation_service.generate_podcast(concepts_for_reinforcement, exam_code_for_feedback)

                    elif reinforce_choice == '4':
                        print("\nGenerating Podcast and Coloring Images (combined experience)...")
                        
                        podcast_generation_service.generate_podcast(concepts_for_reinforcement, exam_code_for_feedback)

                        image_style_choice = ""
                        selected_style_name = ""
                        while image_style_choice not in ['1', '2', '3', '4', '5']:
                            display_image_styles_menu()
                            image_style_choice = input("Select an image style for the combined experience: ")
                            if image_style_choice == '1': selected_style_name = "Simple Line Art"
                            elif image_style_choice == '2': selected_style_name = "Architectural Blueprint"
                            elif image_style_choice == '3': selected_style_name = "Nature/Everyday Analogy"
                            elif image_style_choice == '4': selected_style_name = "Character/Mascot-Driven"
                            elif image_style_choice == '5': selected_style_name = "Abstract Geometric/Flowchart"
                            elif image_style_choice == '6': break
                            else: print("Invalid style choice.")
                        
                        if selected_style_name:
                            image_generation_service.generate_coloring_images(concepts_for_reinforcement, selected_style_name, exam_code_for_feedback)
                        else:
                            print("No image style selected for combined experience. Skipping image generation.")

                    elif reinforce_choice == '5':
                        print("Returning to Main Menu.")
                    else:
                        print("Invalid reinforcement choice. Please try again.")

        elif choice == '4':
            question = input("What would you like to know about Azure Certifications? ")
            messages = [
                {"role": "system", "content": "You are an expert on Microsoft Azure certification exams."},
                {"role": "user", "content": question}
            ]
            response = ai_client.call_chat_completion(messages=messages, max_tokens=4096, temperature=0.7)
            if response:
                print(f"\nAI Assistant: {response}")
            else:
                print("Could not get a response from the AI assistant.")

        elif choice == '5':
            print("Exiting Azure Certification Coach. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
