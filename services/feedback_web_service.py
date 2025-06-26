import json
from pathlib import Path
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional

from services.azure_ai_client import AzureAIClient
from prompts.prompts import *
from utils.utils import *

class FeedbackWebService:
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
                st.warning(f"Could not read existing CSV: {e}")
        
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
        st.success(f"Feedback data saved to {feedback_csv}")

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
        """Display formatted feedback report using Streamlit components."""
        st.subheader(f"Performance Report for {exam_code}")
        
        # Detailed Question Review
        st.write("### Detailed Question Review:")
        headers = ["Question Type", "Question", "User Answer", "Evaluation/Score", "Notes"]
        table_data = []
        for q_scored in analysis_data.get("scored_questions", []):
            q_type = q_scored.get("type", "N/A").replace('_', ' ').title()
            question_text = q_scored.get("question", "N/A")
            user_ans = q_scored.get("user_answer", "N/A")
            score = q_scored.get("score", "N/A")
            notes = q_scored.get("notes", "N/A")
            table_data.append([q_type, question_text, user_ans, score, notes])
        
        df = pd.DataFrame(table_data, columns=headers)
        st.dataframe(df, hide_index=True)

        # Performance by Category
        st.write("### Performance by Exam Category:")
        performance_data = analysis_data.get("performance_by_category", [])
        formatted_performance_data = []
        for data in performance_data:
            formatted_performance_data.append({
                "Skill Area": data.get("skill_area"), 
                "Average Score": f"{data.get('average_score_percent')}%"
            })
        df_perf = pd.DataFrame(formatted_performance_data)
        st.dataframe(df_perf, hide_index=True)

    def write_feedback_and_new_questions(self, selected_exam_code: str, 
                                       results_suffix: str = "results.json", 
                                       questions_suffix: str = "targeted_questions.json"):
        """Provide performance feedback with analysis and generate new questions."""
        
        # Construct file paths
        results_file = construct_file_path(self.files_dir, selected_exam_code, results_suffix)
        new_questions_output_file = construct_file_path(self.files_dir, selected_exam_code, questions_suffix)

        # Load simulation results
        all_results = load_json_file(results_file)
        if not all_results:
            if not results_file.exists():
                st.error(f"Results file '{results_file}' not found. Please run a simulation first.")
            else:
                st.error(f"Could not decode JSON from '{results_file}'. File might be corrupted.")
            return

        latest_results = all_results[-1] 
        exam_code = latest_results.get("exam_code", "Unknown Exam")
        timestamp = latest_results.get("timestamp", datetime.now().isoformat())
        results_context = json.dumps(latest_results, indent=2)

        try:
            with st.spinner("Analyzing performance and generating feedback..."):
                response_content = self._call_feedback_api(exam_code, results_context)
            
            if response_content is None:
                st.error("API call failed or returned empty content.")
                return

            analysis_data = json.loads(response_content)

            # Display feedback report
            self._display_feedback_report(analysis_data, exam_code)
            
            # Save to CSV
            self._save_feedback_to_csv(analysis_data, exam_code, timestamp)

            # Display CSV summary
            feedback_csv = self.files_dir / f"{exam_code}_feedback.csv"
            if feedback_csv.exists():
                st.write("### Historical Performance Summary:")
                st.write("##### (*) Last 10 simulation results")
                df_history = pd.read_csv(feedback_csv).drop_duplicates(subset=["timestamp"], keep='last')
                st.dataframe(df_history.tail(10), hide_index=True)  # last 10 simulation results

            # Save new targeted questions
            if analysis_data.get("new_questions_for_weak_areas"):
                if save_json_file(analysis_data["new_questions_for_weak_areas"], new_questions_output_file):
                    st.success(f"New targeted questions saved to '{new_questions_output_file}'.")
                else:
                    st.error(f"Failed to save targeted questions to '{new_questions_output_file}'.")
            else:
                st.warning("No new targeted questions were generated.")

        except json.JSONDecodeError as e:
            st.error(f"Error decoding JSON from API response: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")