# question_service.py
import json
import random
from pathlib import Path
from services.exam_data_loader import ExamDataLoader
from services.azure_ai_client import AzureAIClient
from prompts.prompts import * 
import os


class QuestionService:
    def __init__(self, exam_data_loader: ExamDataLoader, ai_client: AzureAIClient):
        self.exam_data_loader = exam_data_loader
        self.ai_client = ai_client
        self.files_dir = Path("files") # Defines the files directory
        self.demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"

    def _generate_questions_live(self, selected_exam_code, num_yes_no, num_qualitative):
        """Original live question generation using Azure OpenAI"""
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
            questions_data["exam_code"] = selected_exam_code

            output_file = self.files_dir / f"questions_{selected_exam_code}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(questions_data, f, indent=2)
            print(f"Successfully generated and saved questions to {output_file}")

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from API response during question generation: {e}")
            print(f"Raw response content: {response_content}")
        except Exception as e:
            print(f"An unexpected error occurred during question generation: {e}.")
     
    def _load_precomputed_questions(self, selected_exam_code, num_yes_no, num_qualitative):
        """Load precomputed questions from content_updated.json (relevant for DEMO mode only)"""
        print(f"Generating diagnostic questions for {selected_exam_code} (Yes/No: {num_yes_no}, Qualitative: {num_qualitative})...")
        
        # Load content data
        content_file = Path("content/content_updated.json")
        if not content_file.exists():
            print("Error: content_updated.json not found. Cannot load precomputed questions.")
            return
            
        with open(content_file, 'r', encoding='utf-8') as f:
            content_data = json.load(f)
        
        if selected_exam_code not in content_data:
            print(f"Error: Exam {selected_exam_code} not found in content data.")
            return
        
        # Extract precomputed questions
        all_precomputed = []
        exam_data = content_data[selected_exam_code]
        
        for skill in exam_data["skills_measured"]:
            skill_area = skill["skill_area"]
            for subtopic in skill["subtopics"]:
                details = subtopic.get("details", [])
                for detail in details:
                    if isinstance(detail, dict) and detail.get("question_text"):
                        all_precomputed.append({
                            "type": "yes_no",
                            "skill_area": skill_area,
                            "question": detail["question_text"],
                            "expected_answer": detail["expected_answer"],
                            "purpose": "Binary Assessment"
                        })
        
        if len(all_precomputed) < (num_yes_no + num_qualitative):
            print(f"Warning: Only {len(all_precomputed)} precomputed questions available. Adjusting request.")
            num_yes_no = min(num_yes_no, len(all_precomputed))
            num_qualitative = 0  # Demo mode only has yes/no questions
        
        # Randomly sample questions
        selected_questions = random.sample(all_precomputed, min(num_yes_no, len(all_precomputed)))
        
        # Add some qualitative questions if requested (generate basic ones)
        qualitative_questions = []
        if num_qualitative > 0:
            skill_areas = list(set([q["skill_area"] for q in selected_questions]))
            for i, skill_area in enumerate(skill_areas[:num_qualitative]):
                qualitative_questions.append({
                    "type": "qualitative",
                    "skill_area": skill_area,
                    "question": f"Explain the key concepts and benefits of {skill_area.lower()}.",
                    "purpose": "Scaled Assessment",
                    "scoring_criteria": [
                        "Demonstrates understanding of core concepts",
                        "Explains practical applications", 
                        "Mentions key benefits or features",
                        "Uses appropriate technical terminology",
                        "Provides clear and organized explanation"
                    ]
                })
        
        # Combine and save
        questions_data = {
            "exam_code": selected_exam_code,
            "questions": selected_questions + qualitative_questions
        }
        
        output_file = self.files_dir / f"questions_{selected_exam_code}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(questions_data, f, indent=2)
        
        print(f"Successfully loaded and saved {len(questions_data['questions'])} questions to {output_file}")
    
    def generate_diagnostic_questions(self, selected_exam_code, num_yes_no=3, num_qualitative=3):
        """
        Generates diagnostic questions for the selected exam.
        In demo mode, loads precomputed questions. In live mode, uses Azure OpenAI.
        """
        if self.demo_mode:
            self._load_precomputed_questions(selected_exam_code, num_yes_no, num_qualitative)
        else:
            self._generate_questions_live(selected_exam_code, num_yes_no, num_qualitative)
    