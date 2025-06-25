import json
import csv
from pathlib import Path
from datetime import datetime
import pandas as pd

# from services.exam_data_loader import ExamDataLoader
from services.azure_ai_client import AzureAIClient

from prompts.prompts import *
from utils.utils import *
from tabulate import tabulate

class FeedbackService:
    def __init__(self, ai_client: AzureAIClient):
        self.ai_client = ai_client
        self.files_dir = Path("files")
        self.feedback_csv = self.files_dir / "consolidated_feedback.csv"

    def _save_feedback_to_csv(self, analysis_data: dict, exam_code: str, timestamp: str):
        """Save feedback data to consolidated CSV file."""
        
        def parse_score(score_value):
            """Parse score value, handling both string percentages and numeric values."""
            if isinstance(score_value, str):
                # Remove % symbol and convert to float
                return float(score_value.replace('%', '')) if score_value.replace('%', '').replace('.', '').isdigit() else 0
            return float(score_value) if score_value is not None else 0
        
        # Prepare row data
        overall_score = 0
        total_questions = len(analysis_data.get("scored_questions", []))
        
        if total_questions > 0:
            total_score = sum(parse_score(q.get("score", 0)) for q in analysis_data.get("scored_questions", []))
            overall_score = total_score / total_questions
        
        # Skill area performance
        skill_performance = {}
        for perf in analysis_data.get("performance_by_category", []):
            skill_area = perf.get("skill_area", "Unknown")
            score = perf.get("average_score_percent", 0)
            skill_performance[skill_area] = score
        
        # Base row data
        row_data = {
            "timestamp": timestamp,
            "exam_code": exam_code,
            "total_questions": total_questions,
            "overall_score_percent": round(overall_score, 2),
            "yes_no_questions": len([q for q in analysis_data.get("scored_questions", []) if q.get("type") == "yes_no"]),
            "qualitative_questions": len([q for q in analysis_data.get("scored_questions", []) if q.get("type") == "qualitative"]),
        }
        
        # Add skill area scores as separate columns
        for skill_area, score in skill_performance.items():
            # Clean skill area name for column header
            clean_skill = skill_area.replace(" ", "_").replace("-", "_").lower()
            row_data[f"skill_{clean_skill}_percent"] = score
        
        # Check if CSV exists and load existing data
        df_existing = pd.DataFrame()
        if self.feedback_csv.exists():
            try:
                df_existing = pd.read_csv(self.feedback_csv)
            except Exception as e:
                print(f"Warning: Could not read existing CSV: {e}")
        
        # Create new row DataFrame
        df_new = pd.DataFrame([row_data])
        
        # Combine with existing data
        if not df_existing.empty:
            # Align columns
            all_columns = set(df_existing.columns) | set(df_new.columns)
            for col in all_columns:
                if col not in df_existing.columns:
                    df_existing[col] = None
                if col not in df_new.columns:
                    df_new[col] = None
            
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_combined = df_new
        
        # Save to CSV
        df_combined.to_csv(self.feedback_csv, index=False)
        print(f"Feedback data appended to {self.feedback_csv}")

    def provide_feedback_and_new_questions(self, selected_exam_code, results_file_suffix="results.json", output_file_suffix="targeted_questions.json"):
        """
        Provides performance feedback with a bar chart, generates new questions, and saves to CSV.
        """
        # Construct results and output file paths
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
        timestamp = latest_results.get("timestamp", datetime.now().isoformat())

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
                max_tokens=32768,
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
                max_width=40
            )
            print(bar_chart)

            # Save to CSV
            self._save_feedback_to_csv(analysis_data, exam_code, timestamp)

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

    def get_feedback_summary(self) -> pd.DataFrame:
        """Get consolidated feedback summary from CSV."""
        if self.feedback_csv.exists():
            return pd.read_csv(self.feedback_csv)
        return pd.DataFrame()