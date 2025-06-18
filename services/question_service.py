# question_service.py
import json
from pathlib import Path
from services.exam_data_loader import ExamDataLoader
from services.azure_ai_client import AzureAIClient
from prompts.prompts import * 


class QuestionService:
    def __init__(self, exam_data_loader: ExamDataLoader, ai_client: AzureAIClient):
        self.exam_data_loader = exam_data_loader
        self.ai_client = ai_client
        self.files_dir = Path("files") # Define the files directory

    def generate_diagnostic_questions(self, selected_exam_code, num_yes_no=3, num_qualitative=3):
        """
        Generates diagnostic questions for the selected exam using Azure OpenAI.
        Questions are saved to 'files/questions_{exam_code}.json'.

        Args:
            selected_exam_code (str): The code of the exam for which to generate questions.
            num_yes_no (int): The desired number of Yes/No type questions.
            num_qualitative (int): The desired number of Qualitative type questions.
        """
        print(f"Generating diagnostic questions for {selected_exam_code} (Yes/No: {num_yes_no}, Qualitative: {num_qualitative})...")

        context = self.exam_data_loader.prepare_context(detail_level="full", exam_codes=[selected_exam_code])

        if not context:
            print(f"Error: Could not prepare context for exam {selected_exam_code}. Aborting question generation.")
            return

        question_generation_instructions = QUESTION_GENERATION_INSTRUCTIONS.format(
            num_yes_no=num_yes_no, num_qualitative=num_qualitative
        )

        messages = [
            {
                "role": "system",
                "content": "You are an expert on Microsoft Azure certification exams and a question generator. Your task is to create diagnostic questions in a precise JSON format based on provided exam content. You MUST include the 'skill_area' for each generated question."
            },
            {
                "role": "user",
                "content": f"{question_generation_instructions}\n\nExam Data for {selected_exam_code}:\n{context}"
            }
        ]

        try:
            response_content = self.ai_client.call_chat_completion(
                messages=messages,
                max_tokens=8192,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            if response_content is None:
                print("API call failed or returned empty content.")
                return

            questions_data = json.loads(response_content)

            questions_data["exam_code"] = selected_exam_code # Ensure exam_code is set

            # Save to the 'files' subdirectory
            output_file = self.files_dir / f"questions_{selected_exam_code}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(questions_data, f, indent=2)
            print(f"Successfully generated and saved questions to {output_file}")

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from API response during question generation: {e}")
            print(f"Raw response content: {response_content}")
        except Exception as e:
            print(f"An unexpected error occurred during question generation: {e}.")
    