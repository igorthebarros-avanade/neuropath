import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from typing import Dict, List, Optional

from services.azure_ai_client import AzureAIClient
from prompts.prompts import *
from utils.utils import *
from tabulate import tabulate

class FeedbackService:
    def __init__(self, ai_client: AzureAIClient):
        self.ai_client = ai_client
        self.files_dir = Path("files")

    def _calculate_overall_score(self, scored_questions: List[Dict]) -> float:
        """Calculate overall score from scored questions."""
        if not scored_questions:
            return 0.0
        
        total_score = sum(parse_score(q.get("score", 0)) for q in scored_questions)
        return total_score / len(scored_questions)

    def _extract_skill_performance(self, performance_data: List[Dict]) -> Dict[str, float]:
        """Extract skill area performance mapping."""
        skill_performance = {}
        for perf in performance_data:
            skill_area = perf.get("skill_area", "Unknown")
            score = perf.get("average_score_percent", 0)
            skill_performance[skill_area] = score
        return skill_performance

    def _create_csv_row(self, analysis_data: Dict, exam_code: str, timestamp: str) -> Dict:
        """Create a single CSV row from analysis data."""
        scored_questions = analysis_data.get("scored_questions", [])
        overall_score = self._calculate_overall_score(scored_questions)
        skill_performance = self._extract_skill_performance(analysis_data.get("performance_by_category", []))
        
        row_data = {
            "timestamp": timestamp,
            "exam_code": exam_code,
            "total_questions": len(scored_questions),
            "overall_score_percent": round(overall_score, 2),
            "yes_no_questions": len([q for q in scored_questions if q.get("type") == "yes_no"]),
            "qualitative_questions": len([q for q in scored_questions if q.get("type") == "qualitative"]),
        }
        
        # Add skill area scores as separate columns
        for skill_area, score in skill_performance.items():
            clean_skill = skill_area.replace(" ", "_").replace("-", "_").lower()
            row_data[f"skill_{clean_skill}_percent"] = score
        
        return row_data

    def _save_feedback_to_csv(self, analysis_data: Dict, exam_code: str, timestamp: str):
        """Save feedback data to exam-specific CSV file."""
        feedback_csv = self.files_dir / f"{exam_code}_feedback.csv"
        row_data = self._create_csv_row(analysis_data, exam_code, timestamp)
        
        # Load existing data
        df_existing = pd.DataFrame()
        if feedback_csv.exists():
            try:
                df_existing = pd.read_csv(feedback_csv)
            except Exception as e:
                print(f"Warning: Could not read existing CSV: {e}")
        
        # Create and combine DataFrames
        df_new = pd.DataFrame([row_data])
        
        if len(df_existing) > 0:
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
        df_combined.to_csv(feedback_csv, index=False)
        print(f"Feedback data appended to {feedback_csv}")

    def _call_feedback_api(self, exam_code: str, results_context: str) -> Optional[str]:
        """Make API call for feedback analysis."""
        feedback_instructions = FEEDBACK_AND_QUESTIONS_INSTRUCTIONS.format(exam_code=exam_code)
        
        messages = [
            {
                "role": "system",
                "content": "You are a comprehensive examiner and question generator for Azure certification exams. Provide detailed performance feedback, including a score for each question and per-category performance, and generate targeted new questions."
            },
            {
                "role": "user",
                "content": f"{feedback_instructions}\n\nUser's Simulation Results:\n{results_context}"
            }
        ]

        return self.ai_client.call_chat_completion(
            messages=messages,
            max_tokens=32768,
            temperature=0.7,
            response_format={"type": "json_object"}
        )

    def _display_feedback_report(self, analysis_data: Dict, exam_code: str):
        """Display formatted feedback report."""
        print(f"\n--- Performance Report for Exam: {exam_code} ---")
        
        # Detailed Question Review
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

        return {"questionsFeedback": table_data, "performanceForSkill": performance_data}

    def provide_feedback_and_new_questions(self, selected_exam_code: str, 
                                         results_file_suffix: str = "results.json", 
                                         output_file_suffix: str = "targeted_questions.json",
                                         frontend_results = []):
        """Provide performance feedback with analysis and generate new questions."""
        
        # Construct file paths
        results_file = construct_file_path(self.files_dir, selected_exam_code, results_file_suffix)
        new_questions_output_file = construct_file_path(self.files_dir, selected_exam_code, output_file_suffix)

        # Load simulation results
        all_results = None
        if len(frontend_results) == 0:
            all_results = load_json_file(results_file)
        else:
            all_results = frontend_results

        if not all_results:
            print("Please run a simulation first.")
            return

        latest_results = all_results[-1]
        exam_code = latest_results.get("exam_code", "Unknown Exam")
        timestamp = latest_results.get("timestamp", datetime.now().isoformat())
        results_context = json.dumps(latest_results, indent=2)

        print(f"\n--- Analyzing Performance for Exam: {exam_code} ---")

        # Call API for feedback analysis
        response_content = self._call_feedback_api(exam_code, results_context)
        if response_content is None:
            print("API call failed or returned empty content.")
            return

        try:
            analysis_data = json.loads(response_content)
            
            # Display feedback report
            feedbackReport = self._display_feedback_report(analysis_data, exam_code)
            
            # Save to CSV
            self._save_feedback_to_csv(analysis_data, exam_code, timestamp)

            targetedQuestions = analysis_data.get("new_questions_for_weak_areas")
            # Save new targeted questions
            if targetedQuestions:
                if save_json_file(analysis_data["new_questions_for_weak_areas"], new_questions_output_file):
                    print(f"\nNew targeted questions saved to '{new_questions_output_file}'.")
            else:
                print("\nNo new targeted questions were generated.")

            return {"feedbackReport": feedbackReport, "targetedQuestions": targetedQuestions.get("questions")}
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from API response: {e}")
            print(f"Raw response content: {response_content}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def get_feedback_summary(self, exam_code: str) -> pd.DataFrame:
        """Get feedback summary for a specific exam from CSV."""
        feedback_csv = self.files_dir / f"{exam_code}_feedback.csv"
        if feedback_csv.exists():
            return pd.read_csv(feedback_csv)
        return pd.DataFrame()