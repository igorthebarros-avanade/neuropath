# concept_extractor.py
import json

class ConceptExtractor:
    def __init__(self):
        pass

    def extract_concepts_from_targeted_questions(self, targeted_questions_data: dict) -> list:
        """
        Extracts key concepts from the AI-generated targeted questions data.
        This focuses on the 'skill_area' and the core idea of the 'question' itself.

        Args:
            targeted_questions_data (dict): The dictionary containing "exam_code" and "questions" (list of targeted questions).

        Returns:
            list: A list of unique concept strings.
        """
        concepts = set() # Use a set to store unique concepts
        if not targeted_questions_data or not targeted_questions_data.get("questions"):
            return []

        for q in targeted_questions_data["questions"]:
            skill_area = q.get("skill_area")
            question_text = q.get("question")

            if skill_area:
                concepts.add(skill_area.strip())
            
            # Attempt to extract a concise concept from the question itself
            if question_text:
                # Simple heuristic: take the first part of the question if it's about a specific thing
                # e.g., "Does Azure Blob Storage..." -> "Azure Blob Storage"
                # "Explain the key differences between X and Y" -> "X and Y differences"
                if "explain" in question_text.lower() and "between" in question_text.lower():
                    parts = question_text.lower().split("between", 1)
                    if len(parts) > 1:
                        concept_part = parts[1].split("including")[0].split("and")
                        concepts.update([c.strip().replace("?", "").replace(".", "") for c in concept_part if c.strip()])
                elif "what is" in question_text.lower():
                    concept_part = question_text.lower().split("what is", 1)[-1].strip().replace("?", "").replace(".", "")
                    if concept_part:
                        concepts.add(concept_part)
                elif "does" in question_text.lower():
                    concept_part = question_text.lower().split("does", 1)[-1].strip().split(" ", 1)[0].replace("?", "").replace(".", "")
                    if concept_part:
                        concepts.add(concept_part)
                else:
                    # Fallback: just add the first few words or the skill area if no specific extraction
                    first_words = " ".join(question_text.split()[:5]).strip().replace("?", "").replace(".", "")
                    if first_words and first_words not in concepts: # Avoid duplicating skill area if it's already there
                        concepts.add(first_words)

        return sorted(list(concepts)) # Return a sorted list of unique concepts
