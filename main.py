import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
import json
import os
from datetime import datetime, timedelta
from dateutil import parser
import pandas as pd
import plotly.express as px
from typing import List, Dict, Any
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

class HealthGenieApp:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.initialize_session_state()

    def initialize_session_state(self):
        """Initialize session state variables"""
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'symptoms_log' not in st.session_state:
            st.session_state.symptoms_log = []
        if 'medications' not in st.session_state:
            st.session_state.medications = []
        if 'appointments' not in st.session_state:
            st.session_state.appointments = []
        if 'user_profile' not in st.session_state:
            st.session_state.user_profile = {
                'age': '',
                'conditions': '',
                'allergies': '',
                'lifestyle': ''
            }
    
    def generate_ai_response(self, prompt: str, context: str = "") -> str:
        """Generate response using Gemini AI"""
        try:
            full_prompt = f"""
            You are HealthGenie, a professional AI healthcare assistant. You provide helpful, accurate, and empathetic health information.
            
            Context: {context}
            
            User Query: {prompt}
            
            Please provide a helpful response. Remember to:
            - Always recommend consulting healthcare professionals for serious concerns
            - Be empathetic and supportive
            - Provide actionable advice when appropriate
            - Keep responses clear and easy to understand
            """
            
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            return f"I apologize, but I'm having trouble processing your request. Please try again. Error: {str(e)}"
    
    def extract_text_from_pdf(self, uploaded_file) -> str:
        """Extract text from uploaded PDF file"""
        try:
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            return f"Error reading PDF: {str(e)}"
    
    def summarize_medical_document(self, text: str) -> str:
        """Summarize medical document using Gemini"""
        prompt = f"""
        Please summarize this medical document in simple, easy-to-understand language. 
        Focus on:
        - Key findings or results
        - Any concerning areas that need attention
        - Recommended actions or follow-ups
        - Important dates or appointments
        
        Medical Document Text:
        {text}
        
        Please provide a clear, patient-friendly summary.
        """
        return self.generate_ai_response(prompt)
    
    def detect_symptom_logging(self, message: str) -> bool:
        """Detect if user is trying to log symptoms"""
        symptom_keywords = ['feel', 'symptom', 'pain', 'ache', 'dizzy', 'nausea', 'tired', 'headache', 'sick', 'hurt']
        return any(keyword in message.lower() for keyword in symptom_keywords)
    
    def log_symptom(self, message: str):
        """Log symptom with timestamp"""
        symptom_entry = {
            'timestamp': datetime.now(),
            'description': message,
            'date': datetime.now().strftime('%Y-%m-%d')
        }
        st.session_state.symptoms_log.append(symptom_entry)
    
    def get_upcoming_reminders(self) -> List[Dict]:
        """Get upcoming medications and appointments"""
        reminders = []
        today = datetime.now().date()
        
        # Add medication reminders
        for med in st.session_state.medications:
            if 'next_dose' in med:
                try:
                    next_dose_date = parser.parse(med['next_dose']).date()
                    if next_dose_date >= today:
                        reminders.append({
                            'type': 'Medication',
                            'title': med['name'],
                            'time': med['next_dose'],
                            'description': f"Take {med['dosage']}"
                        })
                except:
                    pass
        
        # Add appointment reminders
        for apt in st.session_state.appointments:
            if 'date' in apt:
                try:
                    apt_date = parser.parse(apt['date']).date()
                    if apt_date >= today:
                        reminders.append({
                            'type': 'Appointment',
                            'title': apt['title'],
                            'time': apt['date'],
                            'description': apt['description']
                        })
                except:
                    pass
        
        # Sort by time
        reminders.sort(key=lambda x: x['time'])
        return reminders[:5]  # Return next 5 reminders
    
    def generate_health_insights(self) -> str:
        """Generate personalized health insights"""
        profile = st.session_state.user_profile
        recent_symptoms = st.session_state.symptoms_log[-10:] if st.session_state.symptoms_log else []
        
        context = f"""
        User Profile:
        - Age: {profile.get('age', 'Not specified')}
        - Health Conditions: {profile.get('conditions', 'None specified')}
        - Allergies: {profile.get('allergies', 'None specified')}
        - Lifestyle: {profile.get('lifestyle', 'Not specified')}
        
        Recent Symptoms: {[s['description'] for s in recent_symptoms]}
        """
        
        prompt = f"""
        Based on the user's profile and recent symptoms, provide personalized health and wellness tips for:
        1. Nutrition recommendations
        2. Sleep hygiene tips
        3. Hydration advice
        4. Physical activity suggestions
        
        {context}
        
        Please provide specific, actionable advice tailored to this user's situation.
        """
        
        return self.generate_ai_response(prompt)
    
    def render_sidebar(self):
        """Render the sidebar with navigation and reminders"""
        st.sidebar.title("🩺 HealthGenie")
        st.sidebar.markdown("*Your AI Healthcare Assistant*")
        
        # Navigation
        page = st.sidebar.selectbox(
            "Navigate",
            ["💬 Chat", "📊 Health Insights", "💊 Medications", "📅 Appointments", "📋 Symptom Log"]
        )
        
        # Upcoming reminders
        st.sidebar.markdown("### 🔔 Upcoming Reminders")
        reminders = self.get_upcoming_reminders()
        if reminders:
            for reminder in reminders:
                with st.sidebar.expander(f"{reminder['type']}: {reminder['title']}"):
                    st.write(f"**Time:** {reminder['time']}")
                    st.write(f"**Details:** {reminder['description']}")
        else:
            st.sidebar.info("No upcoming reminders")
        
        # Quick stats
        st.sidebar.markdown("### 📈 Quick Stats")
        st.sidebar.metric("Symptoms Logged", len(st.session_state.symptoms_log))
        st.sidebar.metric("Medications", len(st.session_state.medications))
        st.sidebar.metric("Appointments", len(st.session_state.appointments))
        
        # Author & Social Links
        st.sidebar.markdown("""
---
<h1 style='font-family: poppins; font-weight: bold; color: Green; font-size: 1.2rem;'>👨‍💻Author: Muhammad Atif LAtif</h1>

<a href="https://github.com/m-Atif-Latif" target="_blank"><img src="https://img.shields.io/badge/GitHub-Profile-blue?style=for-the-badge&logo=github" style="margin-right: 4px;"></a>
<a href="https://www.kaggle.com/matiflatif" target="_blank"><img src="https://img.shields.io/badge/Kaggle-Profile-blue?style=for-the-badge&logo=kaggle" style="margin-right: 4px;"></a>
<a href="https://www.linkedin.com/in/muhammad-atif-latif-13a171318?utm_source=share&utm_campaign=share_via&utm_content=profile&utm_medium=android_app" target="_blank"><img src="https://img.shields.io/badge/LinkedIn-Profile-blue?style=for-the-badge&logo=linkedin" style="margin-right: 4px;"></a>
<a href="https://x.com/mianatif5867?s=09" target="_blank"><img src="https://img.shields.io/badge/Twitter-Profile-blue?style=for-the-badge&logo=twitter" style="margin-right: 4px;"></a>
<a href="https://www.instagram.com/its_atif_ai/" target="_blank"><img src="https://img.shields.io/badge/Instagram-Profile-blue?style=for-the-badge&logo=instagram" style="margin-right: 4px;"></a>
<a href="mailto:muhammadatiflatif67@gmail.com" target="_blank"><img src="https://img.shields.io/badge/Email-Contact%20Me-red?style=for-the-badge&logo=email" style="margin-right: 4px;"></a>
""", unsafe_allow_html=True)
        
        return page
    
    def render_chat_page(self):
        # Professional animated header
        st.markdown("""
        <div class="animated-header">💬 Chat with HealthGenie</div>
        """, unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>Ask me anything about your health, log symptoms, or get medical advice!</div>", unsafe_allow_html=True)
        
        # File upload for document summarization
        with st.container():
            st.markdown("<div class='sub-header'>📄 Upload Medical Document</div>", unsafe_allow_html=True)
            uploaded_file = st.file_uploader(
                "Upload a PDF or text file for summarization",
                type=['pdf', 'txt'],
                help="Maximum file size: 1MB"
            )
            if uploaded_file:
                if uploaded_file.size > 1024 * 1024:  # 1MB limit
                    st.error("File size exceeds 1MB limit. Please upload a smaller file.")
                else:
                    with st.spinner("Processing document..."):
                        if uploaded_file.type == "application/pdf":
                            text = self.extract_text_from_pdf(uploaded_file)
                        else:
                            text = str(uploaded_file.read(), "utf-8")
                        if text:
                            summary = self.summarize_medical_document(text)
                            st.success("Document processed successfully!")
                            st.markdown("<div class='glass-card'><b>📋 Document Summary</b><br>" + summary + "</div>", unsafe_allow_html=True)
        
        # Chat interface
        st.markdown("<div class='sub-header'>💬 Chat</div>", unsafe_allow_html=True)
        st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
        for chat in st.session_state.chat_history:
            if chat["role"] == "user":
                st.markdown(f"<div class='chat-message user-message'>{chat['content']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='chat-message assistant-message'>{chat['content']}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        if prompt := st.chat_input("Type your health question or symptom here..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.markdown(f"<div class='chat-message user-message'>{prompt}</div>", unsafe_allow_html=True)
            if self.detect_symptom_logging(prompt):
                self.log_symptom(prompt)
                context = "The user is logging a symptom. Acknowledge the symptom log and provide relevant advice."
            else:
                context = "General health conversation."
            with st.spinner("Thinking..."):
                response = self.generate_ai_response(prompt, context)
                st.markdown(f"<div class='chat-message assistant-message'>{response}</div>", unsafe_allow_html=True)
                st.session_state.chat_history.append({"role": "assistant", "content": response})

    def render_insights_page(self):
        st.markdown("<div class='animated-header'>📊 Health Insights</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>👤 User Profile</div>", unsafe_allow_html=True)
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                age = st.text_input("Age", value=st.session_state.user_profile['age'])
                conditions = st.text_area("Health Conditions", value=st.session_state.user_profile['conditions'])
            with col2:
                allergies = st.text_area("Allergies", value=st.session_state.user_profile['allergies'])
                lifestyle = st.text_area("Lifestyle Notes", value=st.session_state.user_profile['lifestyle'])
            if st.button("Update Profile"):
                st.session_state.user_profile.update({
                    'age': age,
                    'conditions': conditions,
                    'allergies': allergies,
                    'lifestyle': lifestyle
                })
                st.success("Profile updated!")
        st.markdown("<div class='sub-header'>💡 Personalized Health Tips</div>", unsafe_allow_html=True)
        if st.button("Generate New Insights"):
            with st.spinner("Generating personalized insights..."):
                insights = self.generate_health_insights()
                st.markdown(f"<div class='glass-card'>{insights}</div>", unsafe_allow_html=True)
        if st.session_state.symptoms_log:
            st.markdown("<div class='sub-header'>📈 Symptom Trends</div>", unsafe_allow_html=True)
            symptoms_df = pd.DataFrame(st.session_state.symptoms_log)
            daily_counts = symptoms_df.groupby('date').size().reset_index(name='count')
            fig = px.line(daily_counts, x='date', y='count', 
                         title='Daily Symptom Log Count',
                         labels={'date': 'Date', 'count': 'Number of Symptoms'})
            st.plotly_chart(fig, use_container_width=True)

    def render_medications_page(self):
        st.markdown("<div class='animated-header'>💊 Medication Management</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>➕ Add New Medication</div>", unsafe_allow_html=True)
        with st.container():
            col1, col2, col3 = st.columns(3)
            with col1:
                med_name = st.text_input("Medication Name")
                dosage = st.text_input("Dosage")
            with col2:
                frequency = st.selectbox("Frequency", ["Once daily", "Twice daily", "Three times daily", "As needed"])
                next_dose_date = st.date_input("Next Dose Date")
                next_dose_time = st.time_input("Next Dose Time")
            with col3:
                notes = st.text_area("Notes")
            if st.button("Add Medication"):
                if med_name and dosage:
                    next_dose_datetime = datetime.combine(next_dose_date, next_dose_time)
                    medication = {
                        'name': med_name,
                        'dosage': dosage,
                        'frequency': frequency,
                        'next_dose': next_dose_datetime.strftime('%Y-%m-%d %H:%M'),
                        'notes': notes,
                        'added_date': datetime.now().strftime('%Y-%m-%d')
                    }
                    st.session_state.medications.append(medication)
                    st.success(f"Added {med_name} to your medication list!")
                else:
                    st.error("Please fill in medication name and dosage.")
        st.markdown("<div class='sub-header'>📋 Current Medications</div>", unsafe_allow_html=True)
        if st.session_state.medications:
            for i, med in enumerate(st.session_state.medications):
                with st.expander(f"{med['name']} - {med['dosage']}"):
                    st.write(f"**Frequency:** {med['frequency']}")
                    st.write(f"**Next Dose:** {med['next_dose']}")
                    st.write(f"**Notes:** {med['notes']}")
                    if st.button(f"Remove {med['name']}", key=f"remove_med_{i}"):
                        st.session_state.medications.pop(i)
                        st.rerun()
        else:
            st.info("No medications added yet.")

    def render_appointments_page(self):
        st.markdown("<div class='animated-header'>📅 Appointment Management</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>➕ Schedule New Appointment</div>", unsafe_allow_html=True)
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                apt_title = st.text_input("Appointment Title")
                apt_date = st.date_input("Date")
                apt_time = st.time_input("Time")
                doctor = st.text_input("Doctor/Clinic")
            with col2:
                apt_type = st.selectbox("Type", ["Check-up", "Follow-up", "Specialist", "Lab Test", "Other"])
                description = st.text_area("Description/Notes")
            if st.button("Schedule Appointment"):
                if apt_title and apt_date:
                    apt_datetime = datetime.combine(apt_date, apt_time)
                    appointment = {
                        'title': apt_title,
                        'date': apt_datetime.strftime('%Y-%m-%d %H:%M'),
                        'doctor': doctor,
                        'type': apt_type,
                        'description': description,
                        'created_date': datetime.now().strftime('%Y-%m-%d')
                    }
                    st.session_state.appointments.append(appointment)
                    st.success(f"Scheduled appointment: {apt_title}")
                else:
                    st.error("Please fill in appointment title and date.")
        st.markdown("<div class='sub-header'>📅 Upcoming Appointments</div>", unsafe_allow_html=True)
        if st.session_state.appointments:
            sorted_appointments = sorted(st.session_state.appointments, key=lambda x: x['date'])
            for i, apt in enumerate(sorted_appointments):
                apt_datetime = parser.parse(apt['date'])
                is_upcoming = apt_datetime > datetime.now()
                status = "🟢 Upcoming" if is_upcoming else "🔴 Past"
                with st.expander(f"{status} {apt['title']} - {apt['date']}"):
                    st.write(f"**Doctor/Clinic:** {apt['doctor']}")
                    st.write(f"**Type:** {apt['type']}")
                    st.write(f"**Description:** {apt['description']}")
                    if st.button(f"Remove {apt['title']}", key=f"remove_apt_{i}"):
                        st.session_state.appointments.pop(i)
                        st.rerun()
        else:
            st.info("No appointments scheduled yet.")

    def render_symptom_log_page(self):
        st.markdown("<div class='animated-header'>📋 Symptom Log</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>➕ Quick Symptom Log</div>", unsafe_allow_html=True)
        with st.container():
            symptom_input = st.text_input("Describe your symptom:")
            if st.button("Log Symptom"):
                if symptom_input:
                    self.log_symptom(symptom_input)
                    st.success("Symptom logged successfully!")
                else:
                    st.error("Please describe your symptom.")
        st.markdown("<div class='sub-header'>📊 Symptom History</div>", unsafe_allow_html=True)
        if st.session_state.symptoms_log:
            symptoms_df = pd.DataFrame(st.session_state.symptoms_log)
            symptoms_df['timestamp'] = pd.to_datetime(symptoms_df['timestamp'])
            symptoms_df = symptoms_df.sort_values('timestamp', ascending=False)
            for _, symptom in symptoms_df.iterrows():
                st.markdown(f"<div class='glass-card'><b>{symptom['description']}</b><br><span style='color:#888;font-size:0.9rem;'>{symptom['timestamp'].strftime('%Y-%m-%d %H:%M')}</span></div>", unsafe_allow_html=True)
            if len(st.session_state.symptoms_log) > 3:
                st.markdown("<div class='sub-header'>🔍 Pattern Analysis</div>", unsafe_allow_html=True)
                if st.button("Analyze Symptom Patterns"):
                    with st.spinner("Analyzing patterns..."):
                        recent_symptoms = [s['description'] for s in st.session_state.symptoms_log[-10:]]
                        analysis_prompt = f"""
                        Analyze these recent symptoms for patterns and provide insights:
                        {recent_symptoms}
                        Look for:
                        - Recurring symptoms
                        - Possible triggers
                        - Recommendations for tracking
                        - When to consult a doctor
                        """
                        analysis = self.generate_ai_response(analysis_prompt)
                        st.markdown(f"<div class='glass-card'>{analysis}</div>", unsafe_allow_html=True)
        else:
            st.info("No symptoms logged yet. Start by describing how you're feeling!")
    
    def run(self):
        """Main application runner"""
        # Configure Streamlit page
        st.set_page_config(
            page_title="HealthGenie - AI Healthcare Assistant",
            page_icon="🩺",
            layout="wide",
            initial_sidebar_state="expanded"
        )
          # Professional UI Styling with Advanced CSS
        st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@300;400;500;600;700&display=swap');
            
            /* Global Variables */
            :root {
                --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                --success-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                --warning-gradient: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
                --dark-gradient: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
                --glass-bg: rgba(255, 255, 255, 0.25);
                --glass-border: rgba(255, 255, 255, 0.18);
                --shadow-soft: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                --shadow-hover: 0 15px 35px rgba(31, 38, 135, 0.2);
                --border-radius: 16px;
                --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }
            
            /* Hide Streamlit Elements */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .stDeployButton {display: none;}
            
            /* Main Container */
            .main .block-container {
                padding: 2rem 3rem;
                max-width: 1400px;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                min-height: 100vh;
            }
            
            /* Sidebar Styling */
            .css-1d391kg, .css-1cypcdb {
                background: linear-gradient(180deg, #667eea 0%, #764ba2 100%) !important;
                border-radius: 0 20px 20px 0;
                box-shadow: var(--shadow-soft);
            }
            
            .sidebar .sidebar-content {
                background: transparent;
            }
            
            /* Glassmorphism Cards */
            .glass-card {
                background: var(--glass-bg);
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                border-radius: var(--border-radius);
                border: 1px solid var(--glass-border);
                box-shadow: var(--shadow-soft);
                padding: 2rem;
                margin: 1rem 0;
                transition: var(--transition);
                position: relative;
                overflow: hidden;
            }
            
            .glass-card:hover {
                transform: translateY(-5px);
                box-shadow: var(--shadow-hover);
            }
            
            .glass-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: var(--primary-gradient);
                border-radius: var(--border-radius) var(--border-radius) 0 0;
            }
            
            /* Premium Buttons */
            .stButton > button {
                background: var(--primary-gradient) !important;
                color: white !important;
                border: none !important;
                border-radius: 12px !important;
                padding: 0.75rem 2rem !important;
                font-weight: 600 !important;
                font-family: 'Inter', sans-serif !important;
                transition: var(--transition) !important;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
                position: relative !important;
                overflow: hidden !important;
            }
            
            .stButton > button:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6) !important;
            }
            
            .stButton > button:active {
                transform: translateY(0) !important;
            }
            
            /* Success/Warning Buttons */
            .success-btn {
                background: var(--success-gradient) !important;
                box-shadow: 0 4px 15px rgba(79, 172, 254, 0.4) !important;
            }
            
            .warning-btn {
                background: var(--warning-gradient) !important;
                box-shadow: 0 4px 15px rgba(250, 112, 154, 0.4) !important;
            }
            
            /* Input Styling */
            .stTextInput > div > div > input,
            .stTextArea > div > div > textarea,
            .stSelectbox > div > div > select {
                background: rgba(44, 62, 80, 0.95) !important;
                color: #fff !important;
                border: 2px solid #667eea !important;
                border-radius: 12px !important;
                padding: 1rem !important;
                font-family: 'Inter', sans-serif !important;
                font-size: 1.1rem !important;
                transition: var(--transition) !important;
                box-shadow: 0 2px 10px rgba(0,0,0,0.15) !important;
            }
            
            .stTextInput > div > div > input:focus,
            .stTextArea > div > div > textarea:focus,
            .stSelectbox > div > div > select:focus {
                border-color: #764ba2 !important;
                box-shadow: 0 0 0 3px rgba(118, 75, 162, 0.15) !important;
                outline: none !important;
            }
            
            .stTextInput > div > div > input::placeholder,
            .stTextArea > div > div > textarea::placeholder {
                color: #bfc9d1 !important;
                opacity: 1 !important;
            }
            
            /* Animated Headers */
            .animated-header {
                background: var(--primary-gradient);
                background-clip: text;
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-family: 'Poppins', sans-serif;
                font-weight: 700;
                font-size: 3rem;
                text-align: center;
                margin: 2rem 0;
                position: relative;
                animation: fadeInUp 0.8s ease-out;
            }
            
            .sub-header {
                font-family: 'Inter', sans-serif;
                font-weight: 600;
                color: #2c3e50;
                margin: 1.5rem 0;
                padding-left: 1rem;
                border-left: 4px solid #667eea;
                background: rgba(102, 126, 234, 0.05);
                padding: 1rem;
                border-radius: 0 12px 12px 0;
            }
            
            /* Metric Cards */
            .metric-container {
                display: flex;
                gap: 1rem;
                margin: 2rem 0;
                flex-wrap: wrap;
            }
            
            .metric-card {
                background: var(--glass-bg);
                backdrop-filter: blur(16px);
                border-radius: var(--border-radius);
                padding: 1.5rem;
                text-align: center;
                border: 1px solid var(--glass-border);
                box-shadow: var(--shadow-soft);
                transition: var(--transition);
                flex: 1;
                min-width: 200px;
                position: relative;
                overflow: hidden;
            }
            
            .metric-card:hover {
                transform: translateY(-5px);
                box-shadow: var(--shadow-hover);
            }
            
            .metric-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 4px;
                background: var(--primary-gradient);
            }
            
            .metric-value {
                font-size: 2.5rem;
                font-weight: 700;
                color: #667eea;
                font-family: 'Poppins', sans-serif;
            }
            
            .metric-label {
                font-size: 0.9rem;
                color: #666;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            /* Chat Interface */
            .chat-container {
                background: var(--glass-bg);
                backdrop-filter: blur(16px);
                border-radius: var(--border-radius);
                border: 1px solid var(--glass-border);
                box-shadow: var(--shadow-soft);
                padding: 1.5rem;
                margin: 1rem 0;
                max-height: 600px;
                overflow-y: auto;
            }
            
            .chat-message {
                margin: 1rem 0;
                padding: 1rem;
                border-radius: 12px;
                animation: slideInFromLeft 0.3s ease-out;
            }
            
            .user-message {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                margin-left: 2rem;
                border-radius: 20px 20px 5px 20px;
            }
            
            .assistant-message {
                background: rgba(255, 255, 255, 0.9);
                color: #2c3e50;
                margin-right: 2rem;
                border-radius: 20px 20px 20px 5px;
                border-left: 4px solid #667eea;
            }
            
            /* Expander Styling */
            .streamlit-expanderHeader {
                background: var(--glass-bg) !important;
                border-radius: 12px !important;
                border: 1px solid var(--glass-border) !important;
                font-weight: 600 !important;
                color: #2c3e50 !important;
            }
            
            .streamlit-expanderContent {
                background: rgba(255, 255, 255, 0.9) !important;
                border-radius: 0 0 12px 12px !important;
                border: 1px solid var(--glass-border) !important;
                border-top: none !important;
            }
            
            /* File Uploader */
            .stFileUploader {
                background: var(--glass-bg);
                backdrop-filter: blur(16px);
                border-radius: var(--border-radius);
                border: 2px dashed #667eea;
                padding: 2rem;
                text-align: center;
                transition: var(--transition);
            }
            
            .stFileUploader:hover {
                border-color: #764ba2;
                background: rgba(102, 126, 234, 0.1);
            }
            
            /* Progress Bar */
            .stProgress > div > div > div > div {
                background: var(--primary-gradient) !important;
                border-radius: 10px !important;
            }
            
            /* Alerts */
            .stAlert {
                border-radius: 12px !important;
                border: none !important;
                box-shadow: var(--shadow-soft) !important;
                backdrop-filter: blur(16px) !important;
            }
            
            /* Social Links */
            .social-links {
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem;
                justify-content: center;
                margin: 1rem 0;
            }
            
            .social-links img {
                transition: var(--transition);
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }
            
            .social-links img:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
            }
            
            /* Animations */
            @keyframes fadeInUp {
                from {
                    opacity: 0;
                    transform: translateY(30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            @keyframes slideInFromLeft {
                from {
                    opacity: 0;
                    transform: translateX(-30px);
                }
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }
            
            @keyframes pulse {
                0% {
                    box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.7);
                }
                70% {
                    box-shadow: 0 0 0 10px rgba(102, 126, 234, 0);
                }
                100% {
                    box-shadow: 0 0 0 0 rgba(102, 126, 234, 0);
                }
            }
            
            /* Loading Animation */
            .loading-spinner {
                animation: pulse 2s infinite;
            }
            
            /* Sidebar Enhancements */
            .sidebar .sidebar-content .stSelectbox > label {
                color: white !important;
                font-weight: 600 !important;
                font-family: 'Inter', sans-serif !important;
            }
            
            .sidebar .sidebar-content .stMetric {
                background: rgba(255, 255, 255, 0.15) !important;
                backdrop-filter: blur(10px) !important;
                border-radius: 12px !important;
                padding: 1rem !important;
                margin: 0.5rem 0 !important;
                border: 1px solid rgba(255, 255, 255, 0.2) !important;
            }
            
            .sidebar .sidebar-content .stMetric label {
                color: rgba(255, 255, 255, 0.8) !important;
                font-size: 0.8rem !important;
            }
            
            .sidebar .sidebar-content .stMetric div[data-testid="metric-value"] {
                color: white !important;
                font-weight: 700 !important;
            }
            
            /* Responsive Design */
            @media (max-width: 768px) {
                .main .block-container {
                    padding: 1rem;
                }
                
                .animated-header {
                    font-size: 2rem;
                }
                
                .metric-container {
                    flex-direction: column;
                }
                
                .glass-card {
                    padding: 1rem;
                }
            }
            
            /* Custom Scrollbar */
            ::-webkit-scrollbar {
                width: 8px;
            }
            
            ::-webkit-scrollbar-track {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
            }
            
            ::-webkit-scrollbar-thumb {
                background: var(--primary-gradient);
                border-radius: 10px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: var(--secondary-gradient);
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Render sidebar and get current page
        current_page = self.render_sidebar()
        
        # Render appropriate page based on selection
        if current_page == "💬 Chat":
            self.render_chat_page()
        elif current_page == "📊 Health Insights":
            self.render_insights_page()
        elif current_page == "💊 Medications":
            self.render_medications_page()
        elif current_page == "📅 Appointments":
            self.render_appointments_page()
        elif current_page == "📋 Symptom Log":
            self.render_symptom_log_page()

if __name__ == "__main__":
    app = HealthGenieApp()
    app.run()
