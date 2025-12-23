import streamlit as st
from feedback_engine import (
    extract_text_from_pdf,
    extract_text_from_pdf_handwriting,
    evaluate_answer,
    ask_ai
)

st.set_page_config(page_title="AI Question-Based Grader", layout="centered")

st.title("📄 AI Question-Based Homework Grader")
st.write("Upload the question PDF and the student answer PDF to automatically evaluate each answer.")

# --- Upload ---
question_file = st.file_uploader("Upload question PDF or TXT file", type=["pdf", "txt"])
student_file = st.file_uploader("Upload student answer PDF or TXT file", type=["pdf", "txt"])

if st.button("📬 Evaluate"):
    if not question_file or not student_file:
        st.warning("Please upload both question and student answer files.")
        st.stop()

    # Extract questions
    if question_file.type == "application/pdf":
        question_text = extract_text_from_pdf(question_file)
    else:
        question_text = question_file.read().decode("utf-8")
    question_text = question_text.strip()

    # Extract student answers
    if student_file.type == "application/pdf":
        student_text = extract_text_from_pdf_handwriting(student_file)
    else:
        student_text = student_file.read().decode("utf-8")
    student_text = student_text.strip()

    # Evaluate
    with st.spinner("Evaluating..."):
        score, feedback = evaluate_answer(question_text, student_text)
        st.subheader("📊 Score & Feedback")
        st.write(f"Score: {score}/10")
        st.markdown(f"**Feedback:** {feedback}")

# Chatbot 

st.markdown("---")
st.subheader("💬 Ask AI about this answer")

question = st.text_input("Your question")

if st.button("🤖 Ask"):
    if student_text.strip():
        response = ask_ai(student_text, question)
        st.markdown(response)
    else:
        st.warning("Evaluate an answer first.")

