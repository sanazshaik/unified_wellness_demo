
# Unified Wellness — Hackathon Case Study #3 Demo
# Personal Health & Wellness Aggregator

## [Demo Presentation - Youtube Link](https://youtu.be/5AL9-C3bq5s)

## Description
A lightweight MVP that unifies health data (sleep, activity, nutrition, biometrics) and turns it into
actionable insights via correlations, spearman analysis, AI, and anomaly detection.

## Features
1) User Authentication
2) Google Authenticator 2FA support
3) Unified Dashboard (Sleep, Steps, Calories, Water, Biometrics)
4) Customizable Goals (steps, water, macros, etc.)
5) AI Health Coach (Groq + LLaMA backend)
6) Anomaly Detection
7) Data Visualization
8) Personalized for fitness enthusiasts, health-conscious individuals, and people managing chronic conditions
9) API Support (e.g. FitBit)

## Tech Stack
1) Frontend/UI: Streamlit
2) Backend/Logic: Python
3) Database: SQLite
4) AI: Groq API (LLaMA models)
5) Auth: pyotp + qrcode for 2FA
6) Anomaly Detection
7) Visualization: Altair, Pandas, NumPy


## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py

```

# Create API Key using Groq
https://console.groq.com/home
https://console.groq.com/keys
Click “Create API Key”.



``` bash
cd .../unified_wellness_demo
source .venv/bin/activate      # make sure your in .venv 
pip install groq
export GROQ_API_KEY="your_api_key_here"

# had to force install
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install groq openai

.venv/bin/streamlit run app/streamlit_app.py # only use this command from now on to start up UI after implementing LLM, otherwise will not work
```

## My Groq API Key
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

## For Google 2FA Authenticator 

``` bash
pip install "qrcode[pil]"
pip instal pyoto
pip install qrcode
pip install pillow
```
To scan QR code: download Google Authenticator App

## FitBit API / Get your personal access token to connect to your account
1) Go to https://dev.fitbit.com/apps and log in
2) Click "Register an App"
3) Go to "Manage My Apps" for client details
4) Go to https://dev.fitbit.com/build/reference/web-api/troubleshooting-guide/oauth2-tutorial/?clientEncodedId=23QMWV&redirectUri=http://localhost:8080/&applicationType=PERSONAL
5) Follow steps and get access token
6) Paste access token

