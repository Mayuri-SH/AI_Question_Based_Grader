import easyocr
import pytesseract
from pdf2image import convert_from_bytes
import re
import os
import requests
from dotenv import load_dotenv

load_dotenv()

reader = easyocr.Reader(['en'])
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


# --- OCR for typed PDFs ---
def extract_text_from_pdf(uploaded_file):
    images = convert_from_bytes(uploaded_file.read())
    full_text = ""
    for image in images:
        text = pytesseract.image_to_string(image, config="--psm 6 --oem 1")
        text = text.replace('\x0c', '').strip()
        full_text += text + "\n"
    return full_text.strip()


# --- OCR for handwritten PDFs ---
def extract_text_from_pdf_handwriting(uploaded_file):
    from pdf2image import convert_from_bytes
    import numpy as np

    images = convert_from_bytes(uploaded_file.read())
    full_text = ""
    for image in images:
        img_array = np.array(image)
        results = reader.readtext(img_array)
        page_text = " ".join([res[1] for res in results])
        full_text += page_text + "\n"

    return full_text.strip()


# --- Clean text ---
def clean_text(text):
    lines = text.splitlines()
    filtered = []
    for line in lines:
        if len(re.findall(r'[a-zA-Z0-9]', line)) < 5:
            continue
        if re.search(r'(page \d+|scan|copyright|school name)', line, re.I):
            continue
        filtered.append(line.strip())
    return "\n".join(filtered).strip()


# --- AI evaluation per question ---
def evaluate_answer(question_text, student_text, full_marks=10):
    api_key = os.getenv("OPENROUTER_API_KEY")
    endpoint = "https://openrouter.ai/api/v1/chat/completions"

    cleaned_student = clean_text(student_text)
    if not cleaned_student or len(cleaned_student) < 20:
        return 0, "❗ Could not extract valid content. Please upload a clearer scan or type more text."

    prompt = f"""
Teacher's Questions:
\"\"\"{question_text}\"\"\"

Student's Answers:
\"\"\"{cleaned_student}\"\"\"

Instructions:
- Only evaluate the student's answer for the questions present in the teacher PDF above.
- Ignore any extra text the student wrote that does not match a question.
- Interpret intended meaning even if spelling, grammar, or formatting is poor.
- Try to make sense of the text extracted from student's answer as OCR may be inefficient sometimes.
- Try to be an understanding teacher and use the context to understand what the student was have tried to tell.
- Do not mention text extracted from student's answer. 
- Assign a score out of {full_marks} for each question.
- Provide short feedback explaining why the score was assigned.
- Respond only in this format:

Score: X/{full_marks}
Feedback: <your feedback>
"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "meta-llama/llama-3-8b-instruct",
        "messages": [
            {"role": "system", "content": "You are a strict and knowledgeable teacher."},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(endpoint, headers=headers, json=payload)
    if response.status_code == 200:
        try:
            res_text = response.json()['choices'][0]['message']['content'].strip()
            # parse score from response
            import re
            match = re.search(r'Score:\s*(\d+)', res_text)
            score = int(match.group(1)) if match else 0
            feedback = re.search(r'Feedback:\s*(.+)', res_text, re.DOTALL)
            feedback_text = feedback.group(1).strip() if feedback else res_text
            return score, feedback_text
        except:
            return 0, res_text
    else:
        return 0, "⚠️ Error generating feedback. Please try again later."
    

def ask_ai(text, question):
    api_key = os.getenv("OPENROUTER_API_KEY")
    endpoint = "https://openrouter.ai/api/v1/chat/completions"

    cleaned = clean_text(text)

    payload = {
        "model": "meta-llama/llama-3-8b-instruct",
        "messages": [
            {"role": "system", "content": "You are a strict tutor."},
            {"role": "user", "content": f"Context:\n{cleaned}\n\nQuestion: {question}"}
        ],
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response = requests.post(endpoint, headers=headers, json=payload)
    return response.json()["choices"][0]["message"]["content"].strip()

