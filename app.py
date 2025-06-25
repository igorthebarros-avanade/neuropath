import streamlit as st
from pathlib import Path
import os
from dotenv import load_dotenv
import json
import pandas as pd
import altair as alt

from services.exam_data_loader import ExamDataLoader
from services.azure_ai_client import AzureAIClient
from services.question_service import QuestionService
from services.simulation_web_service import SimulationWebService
from services.feedback_web_service import FeedbackWebService

st.set_page_config(
    page_title="Azure Certification Buddy",
    page_icon="💡",
    layout="centered"
)

# --- Initial Setup and Service Loading ---
@st.cache_resource
def initialize_services():

    load_dotenv()

    try:
        exam_data_path = os.getenv("EXAM_DATA_JSON_PATH")
        if not exam_data_path:
            st.error("Error: 'EXAM_DATA_JSON_PATH' environment variable not configured.")
            st.stop() 

        exam_data_loader = ExamDataLoader(json_file_path=exam_data_path)

        azure_ai_config = {
            "endpoint_text_audio_whisper": os.getenv("AZURE_OPENAI_ENDPOINT_TEXT_AUDIO_WHISPER"),
            "api_key_text_audio_whisper": os.getenv("AZURE_OPENAI_API_KEY_TEXT_AUDIO_WHISPER"),
            "endpoint_image": os.getenv("AZURE_OPENAI_ENDPOINT_IMAGE"),
            "api_key_image": os.getenv("AZURE_OPENAI_API_KEY_IMAGE"),
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
            "deployment_text": os.getenv("AZURE_OPENAI_DEPLOYMENT_TEXT"),
            "deployment_image": os.getenv("AZURE_OPENAI_DEPLOYMENT_IMAGE"),
            "deployment_audio": os.getenv("AZURE_OPENAI_DEPLOYMENT_AUDIO"),
            "deployment_whisper": os.getenv("AZURE_OPENAI_DEPLOYMENT_WHISPER"),
        }

        if not all(azure_ai_config.values()):
            st.warning("Warning: Some Azure AI environment variables are not configured. Related functionalities may not operate correctly.")

        ai_client = AzureAIClient(**azure_ai_config)

        return {
            "exam_data_loader": exam_data_loader,
            "ai_client": ai_client
        }

    except Exception as e:
        st.error(f"An error occurred during service initialization: {e}")
        st.stop() 

services = initialize_services()
exam_data_loader = services["exam_data_loader"]
ai_client = services["ai_client"]

# --- Functions for each page/functionality ---

def home_page():
    """Displays the home page of the application."""
    st.write("Welcome to Avanade's Azure Buddy. Use the navigation menu to select an option.")
    image_path = Path(__file__).parent / 'utils' / 'assets' / 'avanade_buddy.png'
    if image_path.exists():
        st.image(str(image_path), caption="Azure Certification Coach", use_container_width=True)
    else:
        st.warning(f"Image not found at: {image_path}. Please check the path.")

def generate_diagnostic_questions_page():
    """Logic for the Diagnostic Question Generation page."""
    st.header("Generate Diagnostic Questions")
    try:
        available_exams = exam_data_loader.get_available_exams()
        if available_exams:
            exam_options = {f"{code} - {name}": code for code, name in available_exams}
            selected_exam = st.selectbox("Select an Azure Certification Exam:", list(exam_options.keys()))

            # Input for number of questions with validation
            num_yes_no = st.number_input("Number of Yes/No questions:", min_value=1, max_value=100, value=30, step=1)
            
            # Check demo mode for qualitative questions
            demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
            if demo_mode:
                num_qualitative = 0
                st.info("Demo mode only supports Yes/No questions. Qualitative questions disabled.")
            else:
                num_qualitative = st.number_input("Number of Qualitative questions:", min_value=1, max_value=100, value=30, step=1)

            if st.button("Generate Questions"):
                if not selected_exam:
                    st.warning("Please select an exam.")
                    return

                selected_exam_code = exam_options[selected_exam]
                question_service = QuestionService(exam_data_loader, ai_client)

                with st.spinner(f"Generating {num_yes_no + num_qualitative} questions for {selected_exam_code}..."):
                    question_service.generate_diagnostic_questions(selected_exam_code, num_yes_no, num_qualitative)
                st.success(f"Successfully generated {num_yes_no + num_qualitative} questions for {selected_exam_code}!")
        else:
            st.error("No exam data loaded. Please check the 'content.json' path or its content.")
    except Exception as e:
        st.error(f"Error generating diagnostic questions: {e}")

def conduct_simulation_page():
    st.header("Conduct Simulation", anchor=False)
    
    # Check demo mode
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    
    # Initializes the service (use session_state for persistence)
    if 'simulation_service' not in st.session_state:
        st.session_state.simulation_service = SimulationWebService()

    sim_service = st.session_state.simulation_service
    
    # Step 1: Question file selection
    if 'simulation_loaded' not in st.session_state:
        st.session_state.simulation_loaded = False
    
    if not st.session_state.simulation_loaded:
        
        # Special handling for demo mode
        if demo_mode:
            st.info("Demo mode: Using curated yes/no questions from fundamentals exam content.")
            
            available_exams = exam_data_loader.get_available_exams()
            fundamentals_exams = [(code, name) for code, name in available_exams 
                                if code in ["AZ-900", "AI-900", "DP-900"]]
            
            if not fundamentals_exams:
                st.warning("No fundamentals exam data available.")
                return
            
            exam_options = {f"{code} - {name}": code for code, name in fundamentals_exams}
            selected_exam = st.selectbox(
                "Select an Azure Fundamentals Certification:",
                list(exam_options.keys()),
                help="Demo mode uses curated yes/no questions only"
            )
            
            num_questions = st.number_input(
                "Number of questions for simulation:", 
                min_value=1, 
                max_value=15, # lower max value 
                value=5, 
                step=1
            )
            
            if st.button("🚀 Load Questions", type="primary"):
                selected_exam_code = exam_options[selected_exam]
                
                # Check if exam exists in content data
                if selected_exam_code not in exam_data_loader.df.index:
                    st.error(f"Exam {selected_exam_code} not found in content data.")
                    return
                
                # Extract existing yes/no questions from content structure
                demo_questions = []
                exam_data = exam_data_loader.df.loc[selected_exam_code].to_dict()
                
                for skill_area in exam_data["skills_measured"]:
                    for subtopic in skill_area["subtopics"]:
                        for detail in subtopic.get("details", []):
                            if isinstance(detail, dict) and detail.get("question_text") and detail.get("expected_answer"):
                                # Only include if it's already a yes/no question
                                if detail.get("expected_answer") in ["Yes", "No"]:
                                    demo_questions.append({
                                        "type": "yes_no",
                                        "skill_area": skill_area["skill_area"],
                                        "question": detail["question_text"],
                                        "expected_answer": detail["expected_answer"]
                                    })
                
                if not demo_questions:
                    st.warning(f"No yes/no questions found in {selected_exam_code} content.")
                    return
                
                # Create demo question data structure
                demo_question_data = {
                    "exam_code": selected_exam_code,
                    "questions": demo_questions[:num_questions]  # Use user input
                }
                
                # Save temp file and load into simulation service
                temp_file = Path('files') / f"demo_{selected_exam_code}.json"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(demo_question_data, f, indent=2)
                
                success, message = sim_service.load_questions(temp_file)
                
                # Clean up temp file
                if temp_file.exists():
                    temp_file.unlink()
                
                if success:
                    st.success(f"Loaded {len(demo_questions[:num_questions])} demo questions for {selected_exam_code}")
                    st.session_state.simulation_loaded = True
                    st.rerun()
                else:
                    st.error(message)
        
        # Normal mode: Use generated question files
        else:
            question_files = sim_service.get_available_question_files()
            
            if not question_files:
                st.warning("No question files found. Please generate questions first.")
                return
            
            file_mapping = {}
            for file in question_files:
                if file.name.startswith("questions_") and file.name.endswith(".json"):
                    exam_code = file.name.replace("questions_", "").replace(".json", "")
                    
                    exam_descriptions = {
                        "AI-900": "AI-900 - Azure AI Fundamentals",
                        "AZ-900": "AZ-900 - Azure Fundamentals", 
                        "DP-900": "DP-900 - Azure Data Fundamentals",
                        "AZ-104": "AZ-104 - Azure Administrator Associate",
                        "AZ-204": "AZ-204 - Azure Developer Associate",
                        "AZ-305": "AZ-305 - Azure Solutions Architect Expert"
                    }
                    
                    friendly_name = exam_descriptions.get(exam_code, f"{exam_code} - Azure Certification")
                    file_mapping[friendly_name] = file
                else:
                    file_mapping[file.name] = file
            
            selected_friendly_name = st.selectbox(
                "Available Exams Question Files:", 
                list(file_mapping.keys()),
                help="Select an exam to load questions for simulation"
            )
            
            selected_file = file_mapping[selected_friendly_name]
            st.info(f"📁 Selected file: `{selected_file.name}`")
            
            if st.button("🚀 Load Questions", type="primary"):
                success, message = sim_service.load_questions(selected_file)
                
                if success:
                    st.success(message)
                    st.session_state.simulation_loaded = True
                    st.rerun()
                else:
                    st.error(message)
    
    # Step 2: Conducting the simulation
    else:
        progress = sim_service.get_simulation_progress()
        
        # Shows progress
        st.progress(
            progress["current_question"] / progress["total_questions"] if not progress["is_complete"] else 1.0
        )
        st.write(f"**Exam:** {progress['exam_code']}")

        if progress["is_complete"]:
            st.write(f"**Progress:** {progress['current_question'] - 1}/{progress['total_questions']}")
        else:
            st.write(f"**Progress:** {progress['current_question']}/{progress['total_questions']}")

        # Simulation complete
        if progress["is_complete"]:
            st.success("🎉 Simulation Complete!")
            
            if 'results_saved' not in st.session_state:
                st.session_state.results_saved = False
            
            if not st.session_state.results_saved:
                # Save Results and New Simulation buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    save_clicked = st.button(
                        "💾 Save Results", 
                        type="primary",
                        help="Save your simulation results for future analysis",
                        use_container_width=True
                    )
                
                with col2:
                    new_sim_clicked = st.button(
                        "🔄 New Simulation", 
                        type="secondary",
                        help="Start a fresh simulation with new questions",
                        use_container_width=True
                    )
                
                if save_clicked:
                    success, message = sim_service.save_simulation_results()
                    if success:
                        st.session_state.results_saved = True
                        st.success(f"✅ {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                
                if new_sim_clicked:
                    sim_service.reset_simulation()
                    st.session_state.simulation_loaded = False
                    st.session_state.results_saved = False
                    st.rerun()
            
            else:
                # Show View Summary and New Simulation buttons after save
                col1, col2 = st.columns(2)
                
                with col1:
                    view_results_clicked = st.button(
                        "📊 Get Feedback and Reinforcement", 
                        type="primary", 
                        help="Feature coming soon! View your results summary and get feedback",
                        use_container_width=True,
                        disabled=True
                    )
                
                with col2:
                    new_sim_clicked = st.button(
                        "🔄 New Simulation", 
                        type="secondary",
                        help="Start a fresh simulation with new questions",
                        use_container_width=True
                    )
                
                if view_results_clicked:
                    st.info("📈 Results summary will be displayed here")
                
                if new_sim_clicked:
                    sim_service.reset_simulation()
                    st.session_state.simulation_loaded = False
                    st.session_state.results_saved = False
                    st.rerun()
        
        # Current question
        else:
            current_question = sim_service.get_current_question()
            if current_question:
                with st.container(border=True):
                    st.subheader(f"Question {progress['current_question']}", anchor=False)

                    # Display question information
                    col1, col2, col3 = st.columns([6, 1, 1])
                    with col1:
                        st.badge(f"Area: {current_question.skill_area}")
                    with col3:
                        st.badge(current_question.type.replace('_', ' ').title())

                    # Display the question
                    st.write(current_question.question)
                    
                    # Answer input
                    answer_key = f"answer_{progress['current_question']}"
                    answer_selected_key = f"answer_selected_{progress['current_question']}"

                    if answer_selected_key not in st.session_state:
                        st.session_state[answer_selected_key] = False

                    def on_radio_change():
                        """Callback to track when user makes a selection"""
                        st.session_state[answer_selected_key] = True

                    if current_question.type == "yes_no":
                        user_answer = st.radio(
                            "Your answer:", 
                            ["Yes", "No"], 
                            key=answer_key,
                            horizontal=True,
                            index=None,
                            on_change=on_radio_change
                        )
                        has_answer = user_answer is not None
                    else:   
                        user_answer = st.text_area(
                            "Your answer:", 
                            key=answer_key,
                            height=100,
                            max_chars=3000
                        )
                        has_answer = user_answer.strip() if user_answer else False

                    col1, col2, col3 = st.columns([1, 1, 1])

                    # Submit button
                    with col1:
                        if st.button(
                            "✅ Submit Answer", 
                            type="primary", 
                            disabled=not has_answer,
                            use_container_width=True,
                        ):
                            if sim_service.submit_answer(user_answer):
                                # Reset the selection state for next question
                                st.session_state[answer_selected_key] = False
                                st.success("Answer submitted!")
                                st.rerun()
                            else:
                                st.error("Error submitting answer")
                            
                    # Go back to previous question button
                    with col2:
                        if st.button(
                            "🔙 Go Back", 
                            type="secondary", 
                            disabled=progress['current_question'] == 1, 
                            use_container_width=True
                        ):
                            sim_service.go_back_one_question()
                            st.session_state.simulation_loaded = True  
                            st.rerun()

                    # Reset Simulation button
                    with col3:
                        if st.button(
                            "❌ Reset Simulation",  
                            type="tertiary",
                            use_container_width=True,
                            help="Reset the current simulation and start over",
                        ):
                            sim_service.reset_simulation()
                            st.session_state.simulation_loaded = False
                            st.session_state.results_saved = False  
                            st.rerun()

def feedback_page():
    """Feedback dashboard with interactive charts and improved UX."""
    st.header("Feedback")
    try:
        result_files = list(Path('files').glob('*_results.json'))
        if not result_files:
            st.error("No simulation results found in the 'files' folder. Please conduct a simulation first.")
            return

        display_files = {file.name: file for file in result_files}
        selected_result_name = st.selectbox("Select a results file to analyze:", list(display_files.keys()))
        selected_exam_code = selected_result_name.split("_results.json")[0]

        if st.button("Analyze Results"):
            # Use the FeedbackWebService to get feedback data
            feedback_service = FeedbackWebService(ai_client)
            # The function will return the analysis data (dict) instead of rendering directly
            analysis_data = feedback_service.get_feedback_data(selected_exam_code)

            if not analysis_data:
                st.error("No feedback data available.")
                return

            # --- Layout: Use columns for a clean dashboard ---
            with st.container():
                st.subheader("Performance by Exam Category")
                perf_data = analysis_data.get("performance_by_category", [])
                if perf_data:
                    perf_df = pd.DataFrame(perf_data)
                    # Convert score to numeric for charting
                    perf_df["average_score_percent"] = perf_df["average_score_percent"].astype(float)
                    # Bar chart with Altair for better customization
                    bar_chart = alt.Chart(perf_df).mark_bar(size=35, cornerRadiusTopLeft=8, cornerRadiusTopRight=8).encode(
                        x=alt.X("average_score_percent:Q", title="Average Score (%)", scale=alt.Scale(domain=[0, 100])),
                        y=alt.Y("skill_area:N", title="Skill Area", sort='-x'),
                        color=alt.Color("average_score_percent:Q", scale=alt.Scale(scheme='blues'), legend=None),
                        tooltip=["skill_area", "average_score_percent"]
                    ).properties(height=300)
                    st.altair_chart(bar_chart, use_container_width=True)
                else:
                    st.info("No category performance data available.")

            st.markdown("---")

            with st.container():
                st.subheader("Detailed Question Review")
                scored_questions = analysis_data.get("scored_questions", [])
                if scored_questions:
                    q_df = pd.DataFrame(scored_questions)
                    
                    # Fix: handle both numeric and percentage string values for score
                    def parse_score(val):
                        if isinstance(val, str) and val.strip().endswith('%'):
                            try:
                                return float(val.strip().replace('%', ''))
                            except Exception:
                                return 0.0
                        try:
                            return float(val)
                        except Exception:
                            return 0.0
                    q_df["score"] = q_df["score"].apply(parse_score)
                    q_df["Correct"] = q_df["score"] > 0
                    cards_per_row = 3
                    card_min_height = 220  # px, adjust as needed
                    # Add custom CSS for tooltip and icon
                    st.markdown(
                        '''<style>
                        .card-tooltip-container { position: relative; display: flex; flex-direction: column; justify-content: space-between; height: ''' + str(card_min_height) + '''px; }
                        .info-icon {
                            position: absolute;
                            right: 18px;
                            bottom: 18px;
                            width: 28px;
                            height: 28px;
                            background: #fff;
                            border-radius: 50%;
                            border: 2px solid #888;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-size: 1.2em;
                            color: #388e3c;
                            cursor: pointer;
                            box-shadow: 0 2px 8px #0001;
                            z-index: 2;
                        }
                        .info-icon.incorrect { color: #c62828; border-color: #c62828; }
                        .card-tooltip {
                            visibility: hidden;
                            opacity: 0;
                            width: 320px;
                            background: #fff;
                            color: #222;
                            text-align: left;
                            border-radius: 8px;
                            border: 1.5px solid #888;
                            box-shadow: 0 4px 16px #0002;
                            padding: 1em 1.2em 1em 1.2em;
                            position: absolute;
                            bottom: 38px;
                            right: 0;
                            z-index: 10;
                            transition: opacity 0.2s;
                        }
                        .info-icon:hover + .card-tooltip, .info-icon:focus + .card-tooltip {
                            visibility: visible;
                            opacity: 1;
                        }
                        .card-tooltip strong { color: #222; }
                        .card-tooltip .score {
                            background: #f1f8e9;
                            border-radius: 6px;
                            padding: 0.4em 0.8em;
                            margin: 0.5em 0 0.5em 0;
                            display: inline-block;
                            font-weight: bold;
                        }
                        .card-tooltip .notes {
                            background: #fff3cd;
                            border-radius: 6px;
                            padding: 0.7em 1em;
                            margin-top: 0.7em;
                            margin-bottom: 0.2em;
                            display: block;
                        }
                        </style>''', unsafe_allow_html=True
                    )
                    for i in range(0, len(q_df), cards_per_row):
                        cols = st.columns(cards_per_row)
                        for j, row in enumerate(q_df.iloc[i:i+cards_per_row].itertuples()):
                            color = "#d0f5dd" if row.Correct else "#ffebee"
                            border_color = "#388e3c" if row.Correct else "#c62828"
                            icon_class = "info-icon" + (" incorrect" if not row.Correct else "")
                            tooltip_html = f'''
                                <div class="{icon_class}" tabindex="0" title="Show details">&#9432;</div>
                                <div class="card-tooltip">
                                    <div><strong>Type:</strong> {row.type}</div>
                                    <div><strong>Your Answer:</strong> {row.user_answer}</div>
                                    <div class="score">Score: {row.score}</div>
                                    <div class="notes"><strong>Notes:</strong> {row.notes}</div>
                                </div>
                            '''

                            with cols[j]:
                                st.markdown(
                                    f"""
                                    <div class='card-tooltip-container' style='background-color:{color};border:2px solid {border_color};padding:1em 1em 0.5em 1em;border-radius:10px;margin-bottom:16px;box-shadow:0 2px 8px #0001;position:relative;'>
                                        <div style='font-size:1.1em;font-weight:bold;margin-bottom:0.5em;'>Q{i+j+1}: {row.question}</div>
                                        <div style='flex:1'></div>
                                    </div>
                                        {tooltip_html}
                                    """, unsafe_allow_html=True
                                )
                else:
                    st.info("No detailed question data available.")

    except Exception as e:
        st.error(f"Error processing feedback and reinforcement: {e}")

def ask_question_page():
    """Logic for the General Questions page."""
    st.header("Ask about Azure Certifications")
    question = st.text_area("What would you like to know about Azure Certifications?", height=100) # Use text_area for longer questions
    if st.button("Submit Question"):
        if not question.strip():
            st.warning("Please type your question before submitting.")
            return

        messages = [
            {"role": "system", "content": "You are an expert on Microsoft Azure certification exams. Provide concise and accurate answers."},
            {"role": "user", "content": question}
        ]
        with st.spinner("Fetching response..."):
            try:
                response = ai_client.call_chat_completion(messages=messages, max_tokens=4096, temperature=0.7)
                if response:
                    st.markdown(f"**AI Assistant:** {response}") # Use markdown to format the response
                else:
                    st.error("Could not get a response from the AI assistant. Please try again.")
            except Exception as e:
                st.error(f"Error communicating with the AI assistant: {e}")

def exit_page():
    """Displays the exit message."""
    st.write("Thank you for using Avanade's Azure Certification Buddy. Goodbye!")
    # Optional: Add a button to restart or close the app
    if st.button("Restart Application"):
        st.experimental_rerun()


# --- Main Streamlit Application Layout ---

st.title("Hello, traveler!", anchor=False)

# Sidebar navigation
st.sidebar.title("Navigation")
menu_options = {
    "Home": home_page,
    "Generate Diagnostic Questions": generate_diagnostic_questions_page,
    "Conduct Simulation": conduct_simulation_page,
    "Feedback": feedback_page,
    "Ask a Question": ask_question_page,
    "Exit": exit_page,
}

selected_menu = st.sidebar.radio("Go to", list(menu_options.keys()))

# Render the selected page
if selected_menu:
    menu_options[selected_menu]()
else:
    home_page() # Defaults to home page on first load or if nothing is selected