# HealthGenie 🩺

An AI-powered Smart Healthcare Assistant built with Streamlit and Google's Gemini Pro API.

## Features

- **💬 Conversational Health Chatbot**: Ask health-related questions and get AI-powered responses
- **📄 Medical Document Summarizer**: Upload PDFs or text files for plain-language summaries
- **💊 Medication Management**: Track medications with reminders
- **📅 Appointment Scheduler**: Manage healthcare appointments
- **📋 Symptom Logging**: Log daily symptoms and track patterns
- **📊 Health Insights**: Get personalized health and wellness tips

## Professional UI/UX

- **Modern, Premium Design**: Glassmorphism, animated headers, and beautiful gradients
- **Dark, Accessible Input Fields**: All input, textarea, and select fields have a dark background and high-contrast text for easy visibility
- **Responsive Layout**: Looks great on desktop and mobile
- **Animated Chat and Cards**: Enjoy a delightful, interactive experience
- **Sidebar with Social Links**: Author info and social badges in a professional style

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root with your Gemini API key:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

## Usage

Run the Streamlit application:
```bash
streamlit run main.py
```

## Features Overview

### Chat Interface
- Natural language conversation with Gemini AI
- Automatic symptom detection and logging
- Medical document upload and summarization

### Health Management
- Medication tracking with dosage and timing
- Appointment scheduling and reminders
- Symptom pattern analysis

### Insights & Analytics
- Personalized health recommendations
- Symptom trend visualization
- User profile management

## Technical Stack

- **Frontend**: Streamlit (with advanced custom CSS)
- **AI/ML**: Google Gemini Pro API
- **Document Processing**: PyMuPDF
- **Data Visualization**: Plotly
- **Data Handling**: Pandas

## Security Note

- The Gemini API key is loaded from a `.env` file (never hardcoded)
- `.env` is included in `.gitignore` for safe deployment
- For production use, add authentication and secure storage

## Disclaimer

This application is for informational purposes only and should not replace professional medical advice. Always consult with healthcare professionals for medical concerns.
