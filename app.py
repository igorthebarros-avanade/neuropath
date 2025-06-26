import streamlit as st
from pathlib import Path
import os
from dotenv import load_dotenv
import json

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
    """Logic for the Diagnostic Question Generation page with dynamic defaults."""
    st.header("Generate Diagnostic Questions")
    
    try:
        available_exams = exam_data_loader.get_available_exams()
        if available_exams:
            # Filter to fundamentals in demo mode
            demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
            if demo_mode:
                available_exams = [(code, name) for code, name in available_exams 
                                  if code in ["AZ-900", "AI-900", "DP-900"]]
                if not available_exams:
                    st.warning("No fundamental exams available in demo mode.")
                    return
            
            exam_options = {f"{code} - {name}": code for code, name in available_exams}
            
            selected_exam = st.selectbox("Select an Azure Certification Exam:", list(exam_options.keys()))
            
            # Get dynamic defaults based on selected exam
            if selected_exam:
                selected_exam_code = exam_options[selected_exam]
                question_service = QuestionService(exam_data_loader, ai_client)
                defaults = question_service.get_exam_defaults(selected_exam_code)
                
                # Input for number of questions with dynamic defaults
                num_yes_no = st.number_input(
                    "Number of Yes/No questions:", 
                    min_value=1, 
                    max_value=50, # Sensible upper limit for demo purposes
                    value=defaults["yes_no"], 
                    step=1,
                    help=f"Recommended for {selected_exam_code}: {defaults['yes_no']}"  # Recommendsed number of questions based on exam code
                )
                
                # Check demo mode for qualitative questions
                if demo_mode:
                    num_qualitative = 0
                    st.info("Demo mode only supports Yes/No questions. Qualitative questions disabled.")
                else:
                    num_qualitative = st.number_input(
                        "Number of Qualitative questions:", 
                        min_value=1, 
                        max_value=100, 
                        value=defaults["qualitative"], 
                        step=1,
                        help=f"Recommended for {selected_exam_code}: {defaults['qualitative']}"
                    )

                if st.button("Generate Questions"):
                    if not selected_exam:
                        st.warning("Please select an exam.")
                        return

                    with st.spinner(f"Generating {num_yes_no + num_qualitative} questions for {selected_exam_code}..."):
                        question_service.generate_diagnostic_questions(selected_exam_code, num_yes_no, num_qualitative)
                    st.success(f"Successfully generated {num_yes_no + num_qualitative} questions for {selected_exam_code}!")
        else:
            st.error("No exam data loaded. Please check the 'content.json' path or its content.")
    except Exception as e:
        st.error(f"Error generating diagnostic questions: {e}")

def conduct_simulation_page():
    st.header("Conduct Simulation", anchor=False)
        
    # Initialize service
    if 'simulation_service' not in st.session_state:
        st.session_state.simulation_service = SimulationWebService()

    sim_service = st.session_state.simulation_service
    
    # Step 1: Question file selection
    if 'simulation_loaded' not in st.session_state:
        st.session_state.simulation_loaded = False
    
    if not st.session_state.simulation_loaded:
        
        # Special handling for demo mode
        demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        if demo_mode:
            st.info("Demo mode: Using stratified sampling from curated questions.")
            
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
                help="Demo mode ensures questions cover all skill areas proportionally"
            )
            
            # Get dynamic defaults
            if selected_exam:
                selected_exam_code = exam_options[selected_exam]
                question_service = QuestionService(exam_data_loader, ai_client)
                defaults = question_service.get_exam_defaults(selected_exam_code)
                
                num_questions = st.number_input(
                    "Number of questions for simulation:", 
                    min_value=1, 
                    max_value=defaults["yes_no"], 
                    value=min(10, defaults["yes_no"]), 
                    step=1,
                    help=f"Questions will be distributed across all skill areas. Max available: {defaults['yes_no']}"
                )
                
                if st.button("🚀 Load Questions", type="primary"):
                    # Check if exam exists in content data
                    if selected_exam_code not in exam_data_loader.df.index:
                        st.error(f"Exam {selected_exam_code} not found in content data.")
                        return
                    
                    # Use the enhanced simulation service to generate demo questions
                    question_service = QuestionService(exam_data_loader, ai_client)
                    success, message = sim_service.generate_demo_questions(
                        selected_exam_code, num_questions, question_service
                    )
                    
                    if success:
                        st.success(message)
                        st.session_state.simulation_loaded = True
                        
                        # Show skill distribution
                        distribution = sim_service.get_skill_distribution()
                        if distribution:
                            st.write("**Question distribution by skill area:**")
                            for skill, count in distribution.items():
                                st.write(f"• {skill}: {count} questions")
                        
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
                    
                    # Try to read file info for better display
                    try:
                        with open(file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        question_count = len(data.get("questions", []))
                        
                        exam_descriptions = {
                            "AI-900": "AI-900 - Azure AI Fundamentals",
                            "AZ-900": "AZ-900 - Azure Fundamentals", 
                            "DP-900": "DP-900 - Azure Data Fundamentals",
                            "AZ-104": "AZ-104 - Azure Administrator Associate",
                            "AZ-204": "AZ-204 - Azure Developer Associate",
                            "AZ-305": "AZ-305 - Azure Solutions Architect Expert"
                        }
                        
                        friendly_name = exam_descriptions.get(exam_code, f"{exam_code} - Azure Certification")
                        display_name = f"{friendly_name} ({question_count} questions)"
                        file_mapping[display_name] = file
                    except:
                        file_mapping[file.name] = file
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
    
    # Step 2: Conducting the simulation (rest remains the same but add sampling method display)
    else:
        progress = sim_service.get_simulation_progress()
        
        # Show progress with sampling method info
        st.progress(
            progress["current_question"] / progress["total_questions"] if not progress["is_complete"] else 1.0
        )
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Exam:** {progress['exam_code']}")
        with col2:
            sampling_method = progress.get('sampling_method', 'unknown')
            method_display = "Stratified Sampling" if sampling_method == "stratified" else "AI Generated"
            st.write(f"**Method:** {method_display}")

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

def feedback_and_reinforcement_page():
    """Logic for the Feedback and Reinforcement page."""
    st.header("Feedback and Reinforcement")
    try:
        result_files = list(Path('files').glob('*_results.json'))
        if result_files:
            # Ensures file names are readable and selectable
            display_files = {file.name: file for file in result_files}
            selected_result_name = st.selectbox("Select a results file to analyze:", list(display_files.keys()))

            if st.button("Analyze Results"):
                if not selected_result_name:
                    st.warning("Please select a results file.")
                    return

                selected_result_file_path = display_files[selected_result_name]
                # Extracts exam code from the file name
                exam_code_for_feedback = selected_result_file_path.stem.split('_')[0]

                feedback_web_service = FeedbackWebService(ai_client)
                feedback_web_service.write_feedback_and_new_questions(exam_code_for_feedback)
        else:
            st.error("No simulation results found in the 'files' folder. Please conduct a simulation first.")
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
    "Feedback and Reinforcement": feedback_and_reinforcement_page,
    "Ask a Question": ask_question_page,
    "Exit": exit_page,
}

selected_menu = st.sidebar.radio("Go to", list(menu_options.keys()))

# Render the selected page
if selected_menu:
    menu_options[selected_menu]()
else:
    home_page() # Defaults to home page on first load or if nothing is selected