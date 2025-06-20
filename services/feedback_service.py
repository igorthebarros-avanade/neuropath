# feedback_service.py
import json
from pathlib import Path

from services.exam_data_loader import ExamDataLoader
from services.azure_ai_client import AzureAIClient

from prompts.prompts import *
from utils.utils import *
from tabulate import tabulate

class FeedbackService:
    def __init__(self, ai_client: AzureAIClient):
        self.ai_client = ai_client
        self.files_dir = Path("files") # Define the files directory

    def provide_feedback_and_new_questions(self, selected_exam_code, results_file_suffix="results.json", output_file_suffix="targeted_questions.json"):
        """
        Provides performance feedback with a bar chart and generates new questions based on weak areas.
        
        Args:
            selected_exam_code (str): The code of the exam for which feedback is being provided.
            results_file_suffix (str): The suffix for the results file (e.g., "results.json").
            output_file_suffix (str): The suffix for the targeted questions file (e.g., "targeted_questions.json").
        """
        # Construct results and output file paths within the 'files' directory
        results_file = self.files_dir / f"{selected_exam_code}_{results_file_suffix}"
        new_questions_output_file = self.files_dir / f"{selected_exam_code}_{output_file_suffix}"

        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                all_results = json.load(f)
            if not all_results:
                print(f"No simulation results found in '{results_file}'. Please run a simulation first.")
                return
            latest_results = all_results[-1] 
            results_context = json.dumps(latest_results, indent=2)

        except FileNotFoundError:
            print(f"Error: Results file '{results_file}' not found. Please run a simulation first.")
            return
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from '{results_file}'. File might be corrupted.")
            return

        exam_code = latest_results.get("exam_code", "Unknown Exam")

        print(f"\n--- Analyzing Performance for Exam: {exam_code} ---")

        feedback_and_questions_instructions = FEEDBACK_AND_QUESTIONS_INSTRUCTIONS.format(
            exam_code=exam_code
        )

        messages = [
            {
                "role": "system",
                "content": "You are a comprehensive examiner and question generator for Azure certification exams. Provide detailed performance feedback, including a score for each question and per-category performance, and generate targeted new questions."
            },
            {
                "role": "user",
                "content": f"{feedback_and_questions_instructions}\n\nUser's Simulation Results:\n{results_context}"
            }
        ]

        try:
            response_content = self.ai_client.call_chat_completion(
                messages=messages,
                max_tokens=32768, # Further increased token limit for feedback generation
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            if response_content is None:
                print("API call failed or returned empty content.")
                return

            analysis_data = json.loads(response_content)

            print(f"\n--- Performance Report for Exam: {exam_code} ---")
            
            # Detailed Question Review using tabulate
            print("\n### Detailed Question Review:")
            headers = ["Question Type", "Question", "User Answer", "Evaluation/Score", "Notes"]
            table_data = []
            for q_scored in analysis_data.get("scored_questions", []):
                q_type = q_scored.get("type", "N/A").replace('_', ' ').title()
                question_text = wrap_text(q_scored.get("question", "N/A"), width=40)
                user_ans = wrap_text(q_scored.get("user_answer", "N/A"), width=40)
                score = q_scored.get("score", "N/A")
                notes = wrap_text(q_scored.get("notes", "N/A"), width=50)
                table_data.append([q_type, question_text, user_ans, score, notes])
            
            print(tabulate(table_data, headers=headers, tablefmt="grid"))


            # Performance by Category Bar Chart
            print("\n### Performance by Exam Category:")
            performance_data = analysis_data.get("performance_by_category", [])
            bar_chart = generate_text_bar_chart(
                performance_data,
                label_key="skill_area",
                value_key="average_score_percent",
                max_width=40 # Adjust width for better display
            )
            print(bar_chart)


            # Save new targeted questions
            if analysis_data.get("new_questions_for_weak_areas"):
                with open(new_questions_output_file, 'w', encoding='utf-8') as f:
                    json.dump(analysis_data["new_questions_for_weak_areas"], f, indent=2)
                print(f"\nNew targeted questions based on weak areas saved to '{new_questions_output_file}'.")
            else:
                print("\nNo new targeted questions were generated.")

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from API response during feedback generation: {e}")
            print(f"Raw response content: {response_content}")
        except Exception as e:
            print(f"An unexpected error occurred during feedback and question generation: {e}")
