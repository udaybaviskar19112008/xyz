from flask import Flask, render_template, request
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
import re
import spacy
import pickle
import pdfplumber 

app = Flask(__name__)


with open('tokenizer_new1.pkl', 'rb') as f:
    tokenizer = pickle.load(f)
keras_model = load_model('my_model.h5')


RESUME_LEN = 360
JOB_LEN = 462

nlp = spacy.load('en_core_web_sm')


def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + " "
    return text.strip()


def preprocessing(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = text.replace("\n", " ").strip()
    text = [token.lemma_ for token in nlp(text) if not token.is_stop and not token.is_punct]
    return " ".join(text)

def shorting(tokens):
    keyword = "objective"
    tokens_lower = [t.lower() for t in tokens]
    if keyword in tokens_lower:
        index = tokens_lower.index(keyword)
        return tokens[index + 1:]
    return tokens

def text_to_vectors(text, max_len):
    seq = tokenizer.texts_to_sequences([text])
    return pad_sequences(seq, maxlen=max_len, padding='pre')



@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    
    resume_file = request.files['resume_file']
    resume_text = extract_text_from_pdf(resume_file)

    
    job_text = request.form['job']

    
    resume_clean = preprocessing(resume_text)
    resume_clean = shorting(resume_clean.split())
    job_clean = preprocessing(job_text)

    resume_vec = text_to_vectors(" ".join(resume_clean), RESUME_LEN)
    job_vec = text_to_vectors(job_clean, JOB_LEN)

        
    prob = keras_model.predict([resume_vec, job_vec])[0][0]
    decision = "MATCH" if prob >= 0.5 else "NO MATCH"

    return render_template('index.html', prob=round(prob * 100, 2), decision=decision,
                           job_text=job_text)

if __name__ == "__main__":
    app.run(debug=True)
