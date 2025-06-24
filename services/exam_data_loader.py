# exam_data_loader.py
import json
import pandas as pd
from pathlib import Path
import os # Import os for environment variables

class ExamDataLoader:
    def __init__(self, json_file_path=None):
        # Use environment variable if json_file_path is not provided
        self.json_path = json_file_path if json_file_path else os.getenv("EXAM_DATA_JSON_PATH")
        if not self.json_path:
            raise ValueError("EXAM_DATA_JSON_PATH not set in .env or provided to ExamDataLoader.")
        self.df = None
        self._load_data()

    def _load_data(self):
        """Loads exam data from the specified JSON file."""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.df = pd.DataFrame(data).transpose()
        except FileNotFoundError:
            print(f"Error: Exam data file not found at {self.json_path}")
            self.df = pd.DataFrame() # Initialize empty DataFrame to prevent further errors
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {self.json_path}. File might be corrupted.")
            self.df = pd.DataFrame()

    def prepare_context(self, detail_level="full", exam_codes=None):
        """
        Prepares the context string based on desired detail level and specific exam certifications,
        handling the updated 'topic' and 'details' structure within subtopics.
        This is primarily for AI consumption.

        Args:
            detail_level (str): Controls the verbosity of the subtopics.
                                "full": Includes all nested details (dictionaries and strings).
                                "summary": Includes only the main topic string from subtopic dictionaries.
            exam_codes (list): A list of exam codes (e.g., ["AZ-900", "AI-900"]) to filter the context.
                                If None, all exams in the loaded data will be included.
        Returns:
            str: The prepared context string.
        """
        context_lines = []
        
        filtered_df = self.df
        if exam_codes:
            valid_exam_codes = [code for code in exam_codes if code in self.df.index]
            if not valid_exam_codes:
                print(f"Warning: No valid exam codes found in {exam_codes}. Context will be empty.")
                return ""
            filtered_df = self.df.loc[valid_exam_codes]

        for exam_code, details in filtered_df.iterrows():
            name = details.get("name", "")
            skills = details.get("skills_measured", [])

            skill_text_lines = []
            for skill_area_details in skills:
                skill_area = skill_area_details.get("skill_area", "")
                percentage = skill_area_details.get("percentage", "")
                subtopics = skill_area_details.get("subtopics", [])

                formatted_subtopics = []
                for sub_item in subtopics:
                    if isinstance(sub_item, dict):
                        topic_name = sub_item.get("topic", "N/A")
                        details_list = sub_item.get("details", [])

                        if detail_level == "full":
                            formatted_subtopics.append(f"{topic_name}:")
                            for detail_line in details_list:
                                formatted_subtopics.append(f"    - {detail_line}")
                        elif detail_level == "summary":
                            formatted_subtopics.append(topic_name)
                    elif isinstance(sub_item, str):
                        formatted_subtopics.append(sub_item)

                first_part = f"  - {skill_area} ({percentage}):"
                second_part = '\n'.join(formatted_subtopics)
                skill_text_lines.append(f"{first_part}\n{second_part}")
            
            context_lines.append(f"{exam_code}: {name}\n" + "\n".join(skill_text_lines))
        
        return "\n\n".join(context_lines)

    def get_available_exams(self):
        """Returns a list of available exam codes and their names."""
        if self.df.empty:
            return []
        return [(code, self.df.loc[code]['name']) for code in self.df.index]

    def get_structured_exam_content(self, exam_codes=None):
        """
        Returns structured exam content (skill areas and subtopics) as a list of dictionaries.
        Updated to handle both legacy (string) and new (object) detail formats.
        """
        structured_content = []
        
        filtered_df = self.df
        if exam_codes:
            valid_exam_codes = [code for code in exam_codes if code in self.df.index]
            if not valid_exam_codes:
                print(f"Warning: No valid exam codes found in {exam_codes}. Structured content will be empty.")
                return []
            filtered_df = self.df.loc[valid_exam_codes]

        for exam_code, details in filtered_df.iterrows():
            skills = details.get("skills_measured", [])

            for skill_area_details in skills:
                skill_area = skill_area_details.get("skill_area", "")
                subtopics = skill_area_details.get("subtopics", [])

                # Add the main skill area as a flashcard
                if skill_area:
                    # Extract subtopic names for overview
                    subtopic_names = []
                    for s in subtopics:
                        if isinstance(s, dict):
                            subtopic_names.append(s.get('topic', 'Unknown'))
                        else:
                            subtopic_names.append(str(s))
                    
                    structured_content.append({
                        "question": f"What is '{skill_area}' in Azure?",
                        "answer": f"This skill area covers: {', '.join(subtopic_names)}"
                    })

                for sub_item in subtopics:
                    if isinstance(sub_item, dict):
                        topic_name = sub_item.get("topic", "N/A")
                        details_list = sub_item.get("details", [])
                        
                        if topic_name != "N/A":
                            # Handle both string and object detail formats
                            detail_descriptions = []
                            for detail in details_list:
                                if isinstance(detail, dict):
                                    # New format - extract description
                                    detail_descriptions.append(detail.get("description", ""))
                                else:
                                    # Legacy format - use as string
                                    detail_descriptions.append(str(detail))
                            
                            structured_content.append({
                                "question": f"Explain '{topic_name}' in Azure.",
                                "answer": "\n".join(detail_descriptions) if detail_descriptions else "No specific details provided."
                            })
                    elif isinstance(sub_item, str):
                        # For simple string subtopics, use them as questions
                        structured_content.append({
                            "question": f"What is '{sub_item}' in Azure?",
                            "answer": f"This refers to the concept of '{sub_item}' under '{skill_area}'."
                        })
        return structured_content

