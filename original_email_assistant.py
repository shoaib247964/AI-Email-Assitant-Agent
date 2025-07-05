import streamlit as st
import openai
import os
from dotenv import load_dotenv
from io import BytesIO
from fpdf import FPDF
import pandas as pd
from datetime import datetime

# --- Load API Key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# --- Page Config
st.set_page_config(page_title="AI Email Assistant Pro", page_icon="📧", layout="wide")

# --- Heading
st.markdown("<h1 style='text-align: center; font-size: 3rem;'>📬 AI Email Assistant Pro</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2rem;'>Let AI draft, enhance, summarize and format your emails.</p>", unsafe_allow_html=True)

# --- Sidebar
st.sidebar.header("📋 Customize Email")
mode = st.sidebar.radio("Mode", ["Write New Email", "Reply to Email", "Summarize Email", "Translate Email", "Check Grammar", "Detect Category"])
tone = st.sidebar.selectbox("Tone", ["Formal", "Friendly", "Apologetic", "Assertive", "Thankful"])
persona = st.sidebar.selectbox("Persona", ["Student", "Manager", "HR Officer", "Customer Support", "Freelancer"])
language = st.sidebar.selectbox("Language", ["English", "Urdu", "French", "Arabic"])
temperature = st.sidebar.slider("Creativity Level", 0.0, 1.0, 0.7, 0.1)
compliance_mode = st.sidebar.checkbox("🧑‍⚖️ Compliance Mode")

# --- Templates
template = st.selectbox("📚 Use a Template", ["None", "Reschedule Meeting", "Job Application", "Follow-up", "Apology"])
templates = {
    "Reschedule Meeting": "I want to reschedule our meeting from Friday to next Monday due to a scheduling conflict.",
    "Job Application": "I am applying for the software engineer role at your company.",
    "Follow-up": "Just following up on the proposal I sent last week.",
    "Apology": "I want to apologize for missing our scheduled call yesterday."
}

# --- Email Input
if template != "None":
    email_intent = templates[template]
else:
    email_intent = st.text_area("📝 Describe your email intent:", height=100)

signature = st.text_area("✍️ Signature", "Best regards,
Your Name")

# --- Email Generator
def generate_email():
    prompt = f"""
You are an AI Email Assistant.
Tone: {tone}
Persona: {persona}
Language: {language}
Mode: {mode}
Compliance Mode: {compliance_mode}
Task: Based on the following intent, write a professional email.
Intent/Reply:
{email_intent}
Close with this signature:
{signature}
Also suggest a short subject line.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature
    )
    return response['choices'][0]['message']['content']

def save_to_history(subject, body):
    df = pd.DataFrame([[datetime.now(), subject, body]], columns=["Timestamp", "Subject", "Body"])
    if os.path.exists("email_history.csv"):
        old = pd.read_csv("email_history.csv")
        df = pd.concat([old, df], ignore_index=True)
    df.to_csv("email_history.csv", index=False)

# --- Output Email
if st.button("✍️ Generate Email"):
    if not email_intent.strip():
        st.warning("Please describe your email intent.")
    else:
        with st.spinner("Generating your email..."):
            output = generate_email()
            subject_line = ""
            if "Subject:" in output:
                subject_line = output.split("Subject:")[1].split("\n")[0]
                body = output.replace(f"Subject: {subject_line}", "").strip()
            else:
                body = output

            st.success("✅ Email generated successfully!")
            st.text_input("📝 Subject Line", subject_line)
            st.text_area("📨 Email Body", value=body, height=300)

            save_to_history(subject_line, body)

            # Download as .txt
            st.download_button("💾 Download as .txt", body, file_name="email.txt")

            # Download as PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            for line in body.split("\n"):
                pdf.cell(200, 10, txt=line, ln=True)
            buffer = BytesIO()
            pdf.output(name=buffer)
            buffer.seek(0)
            st.download_button("📄 Download as PDF", buffer, file_name="email.pdf")

# --- Regenerate
if st.button("🔁 Regenerate Another Version"):
    with st.spinner("Regenerating..."):
        output = generate_email()
        st.text_area("🆕 Regenerated Email", value=output, height=300)

# --- Summarize
if mode == "Summarize Email":
    long_email = st.text_area("📥 Paste the long email to summarize")
    if st.button("✂️ Summarize"):
        if long_email.strip():
            prompt = f"Summarize the following email in a short, professional paragraph:\n\n{long_email}"
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5
            )
            summary = response['choices'][0]['message']['content']
            st.text_area("🧾 Summary:", summary)

# --- Translate
if mode == "Translate Email":
    original_email = st.text_area("🌍 Paste your email to translate")
    if st.button("🌐 Translate"):
        prompt = f"Translate the following email to {language}:\n\n{original_email}"
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        translated = response['choices'][0]['message']['content']
        st.text_area("🌐 Translated Email:", translated)

# --- Grammar Check
if mode == "Check Grammar":
    raw_email = st.text_area("📝 Paste your email to correct grammar")
    if st.button("🛠️ Check Grammar"):
        prompt = f"Fix grammar and spelling of the following email without changing its tone or meaning:\n\n{raw_email}"
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        corrected = response['choices'][0]['message']['content']
        st.text_area("✅ Corrected Email:", corrected)

# --- Category Detector
if mode == "Detect Category":
    email_text = st.text_area("🔍 Paste email to detect its category")
    if st.button("🔎 Detect"):
        prompt = f"Classify the category of this email (e.g., Complaint, Job Application, Meeting, Feedback, Casual, Request):\n\n{email_text}"
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        category = response['choices'][0]['message']['content']
        st.success(f"📂 Detected Category: {category}")

# --- File Upload
st.markdown("---")
st.subheader("📤 Upload Email File for Summarization or Category Detection")
uploaded_file = st.file_uploader("Choose a .txt file", type=["txt"])
if uploaded_file:
    file_content = uploaded_file.read().decode("utf-8")
    st.text_area("📄 File Content", value=file_content, height=200)
    if st.button("📌 Summarize Uploaded Email"):
        prompt = f"Summarize this email in a short paragraph:\n\n{file_content}"
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        file_summary = response['choices'][0]['message']['content']
        st.text_area("📋 Summary of File", value=file_summary)

# --- Meeting Scheduler Suggestion
st.markdown("---")
st.subheader("📅 AI-Powered Meeting Scheduler")
meeting_context = st.text_area("🗓️ Describe the purpose of the meeting")
if st.button("📆 Suggest Meeting Email"):
    prompt = f"Write a professional meeting scheduling email based on this context:\n\n{meeting_context}"
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )
    meeting_email = response['choices'][0]['message']['content']
    st.text_area("📨 Suggested Meeting Email:", value=meeting_email)
