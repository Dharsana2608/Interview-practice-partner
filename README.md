# Interview Agent - Technical Assessment Platform

A voice-based technical interview platform built with Streamlit.

## Prerequisites

- Python 3.7 or higher
- Groq API key (for AI and transcription services)

## Setup Instructions

### 1. Activate Virtual Environment

Since you already have a `venv` folder, activate it:

**On Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```cmd
venv\Scripts\activate
```

**On Mac/Linux:**
```bash
source venv/bin/activate
```

### 2. Install Dependencies (if not already installed)

If the virtual environment doesn't have all packages, install them:

```bash
pip install streamlit openai python-dotenv audio-recorder-streamlit gtts
```

### 3. Set Up Environment Variables

Create a `.env` file in the project root directory:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Replace `your_groq_api_key_here` with your actual Groq API key. You can get one from [Groq's website](https://console.groq.com/).

### 4. Run the Application

Once the virtual environment is activated and the `.env` file is set up, run:

```bash
streamlit run app.py
```

The application will start and automatically open in your default web browser at `http://localhost:8501`.

## Features

- **30-second timer** for answering each question
- **10-second timeout** after mic activation if no response is received
- Voice-based interview with automatic transcription
- AI-powered interview coordinator and interviewer
- Real-time feedback and assessment

## Usage

1. Start the application using the command above
2. Configure the role and level in the sidebar
3. Click "Start Assessment Now" to begin
4. Use the microphone button to record your answers
5. You have 30 seconds to start answering each question
6. If you activate the mic but don't respond within 10 seconds, it will skip to the next question

## Troubleshooting

- **Port already in use**: If port 8501 is busy, Streamlit will automatically use the next available port
- **API errors**: Make sure your `GROQ_API_KEY` is correctly set in the `.env` file
- **Audio issues**: Ensure your microphone permissions are granted in your browser

