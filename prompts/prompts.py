# prompts.py

QUESTION_GENERATION_INSTRUCTIONS = """
Generate a set of diagnostic questions based on the provided Azure exam data.
The questions should be structured in JSON format.
Include two types of questions: "yes_no" and "qualitative".

Generate exactly {num_yes_no} "yes_no" type questions:
-   Purpose: To determine if the user fully understands a specific concept.
-   Format: Clear, direct question expecting a "Yes" or "No" answer.
-   Include an "expected_answer" field ("Yes" or "No").
-   Include a "purpose" field: "Binary Assessment".

Generate exactly {num_qualitative} "qualitative" type questions:
-   Purpose: To gauge the depth and nuance of the user's understanding.
-   Format: Open-ended questions that require explanation.
-   Include a "purpose" field: "Scaled Assessment".
-   Include a "scoring_criteria" field which is a list of 5 concise bullet points outlining what a good answer should cover to achieve full marks.

For each question, ensure it's derived from a specific "skill_area" in the provided exam data. You must identify and include this "skill_area" name within the question's JSON object.

The overall JSON structure should be:
{{
  "exam_code": "YOUR_EXAM_CODE",
  "questions": [
    {{
      "type": "yes_no",
      "skill_area": "Describe core architectural components of Azure",
      "question": "Does Azure Blob Storage primarily store relational data?",
      "expected_answer": "No",
      "purpose": "Binary Assessment"
    }},
    {{
      "type": "qualitative",
      "skill_area": "Describe Azure compute and networking services",
      "question": "Explain the key differences between Azure Functions and Azure App Services, including their ideal use cases.",
      "purpose": "Scaled Assessment",
      "scoring_criteria": [
        "Mention serverless nature of Functions.",
        "Mention PaaS nature of App Services.",
        "Discuss billing models (consumption vs. plan).",
        "Discuss typical workload sizes (short-lived tasks vs. web apps).",
        "Provide relevant use cases for each."
      ]
    }}
    // ... more questions
  ]
}}
Ensure the JSON is well-formed and valid.
"""

FEEDBACK_AND_QUESTIONS_INSTRUCTIONS = """
You are an expert examiner and question generator for Azure certifications.
Analyze the provided JSON of a user's latest simulation results for exam {exam_code}.

Your task is to:
1.  **Evaluate Questions and Score Performance:**
    -   For each "yes_no" question: Assign a score of 100% if `user_answer` matches `expected_answer` (case-insensitive, allowing for "yes", "y", "no", "n"), otherwise 0%. Provide a brief note.
    -   For each "qualitative" question: Evaluate the `user_answer` against the `scoring_criteria`. Assign a score (e.g., "0%", "20%", "40%", "60%", "80%", "100%") based on how many criteria points are met. Provide concise notes on why the score was assigned (e.g., "Missing key point X", "Excellent explanation", "Partially correct on Y").
    -   For each scored question, include the original "skill_area" it belongs to.

2.  **Summarize Performance by Category:** Calculate the average percentage score for each `skill_area` present in the simulation results.

3.  **Generate New Questions for Weak Areas:** Based on the evaluation and identified weak areas (skill areas with lower scores, e.g., below 70%), generate a new set of diagnostic questions (3-5 "yes_no" and 3-5 "qualitative") specifically targeting these weak areas.
    -   Follow the exact JSON format for diagnostic questions as provided in the `generate_diagnostic_questions` function's instructions (including "type", "skill_area", "question", "expected_answer" for yes_no, and "purpose", "scoring_criteria" for qualitative).
    
Combine all this information into a single JSON object with the following structure:
{{
  "exam_code": "{exam_code}",
  "scored_questions": [
    {{
      "type": "yes_no",
      "skill_area": "Describe cloud concepts",
      "question": "Does Azure Blob Storage primarily store relational data?",
      "user_answer": "No",
      "expected_answer": "No",
      "score": "100%",
      "notes": "Correctly identified the non-relational nature."
    }},
    {{
      "type": "qualitative",
      "skill_area": "Describe Azure compute and networking services",
      "question": "Explain the key differences between Azure Functions and Azure App Services, including their ideal use cases.",
      "user_answer": "Functions are serverless, App Services are PaaS. Functions for short tasks, App Services for web apps.",
      "scoring_criteria": [ /* original criteria */ ],
      "score": "80%",
      "notes": "Good, but could have elaborated on billing models."
    }}
    // ... all questions from the simulation, now scored
  ],
  "performance_by_category": [
    {{
      "skill_area": "Describe cloud concepts",
      "average_score_percent": 75
    }},
    {{
      "skill_area": "Describe Azure compute and networking services",
      "average_score_percent": 60
    }}
    // ... all categories with their average scores
  ],
  "new_questions_for_weak_areas": {{
    "exam_code": "{exam_code}",
    "questions": [
      // ... new diagnostic questions based on weak areas
    ]
  }}
}}
Ensure the entire response is a single, valid JSON object.
"""

# NEW: Prompt for generating image descriptions from concepts
IMAGE_DESCRIPTION_PROMPT = """
Based on the following Azure certification concept(s), generate a concise, clear, and simple description suitable for a line-art coloring book image. The description should focus on the core visual representation of the concept, avoiding excessive detail. It should be easy to understand for someone coloring it.

Concepts:
{concepts_text}

Example Output (for "Virtual Machine"): "A simple drawing of a rectangular server rack with a cloud symbol above it, representing a virtual machine."
Example Output (for "Load Balancer"): "A simple drawing of a scale balancing two stacks of servers, representing a load balancer distributing traffic."
Example Output (for "Azure Storage Blob"): "A simple drawing of a large, abstract blob shape with data flowing into it, representing cloud storage."

Provide only the image description string.
"""

# NEW: Prompt for generating podcast script from concepts
PODCAST_SCRIPT_PROMPT = """
Generate a short, engaging, and easy-to-understand podcast script (around 1-2 minutes per concept) explaining the following Azure certification concepts. The script should be conversational, clear, and focus on the main idea and practical application of each concept.

Concepts:
{concepts_text}

Format the output as a plain text script. For each concept, start with "Concept: [Concept Name]" followed by the explanation.

Example for "Virtual Machine":
Concept: Virtual Machine
Hey there, Azure learners! Today, let's talk about Virtual Machines, or VMs. Think of a VM as a computer within a computer. It's like having a separate operating system and applications running on the same physical hardware as other VMs, but completely isolated. This is super flexible because you can quickly create, scale, or delete these virtual computers in the cloud without buying new physical hardware. You're basically renting computing power from Azure, letting you run your applications and services just as you would on a traditional server, but with all the benefits of the cloud, like scalability and high availability.

Example for "Azure Blob Storage":
Concept: Azure Blob Storage
Next up, Azure Blob Storage! If you've ever wondered where to put all your unstructured data in the cloud – like images, videos, documents, or backups – Blob Storage is your answer. "Blob" stands for Binary Large Object, and it's perfect for storing massive amounts of data that doesn't fit neatly into rows and columns. It's incredibly scalable and cost-effective, making it ideal for things like media streaming, data archiving, or even hosting static websites. You can access your data from anywhere, making it a super versatile storage solution in Azure.

Provide the plain text script for the concepts.
"""
  