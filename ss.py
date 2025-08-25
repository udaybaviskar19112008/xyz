import streamlit as st
import spacy
import PyPDF2

nlp = spacy.load("en_core_web_lg")

def clean_text(text):
    doc = nlp(text)
    return [token.text.lower() for token in doc if not token.is_stop and not token.is_punct]

def compute_similarity(job_desc, res_text):
    cleaned_tokens_job = clean_text(job_desc)
    cleaned_tokens_res = clean_text(res_text)

    job_docs = [nlp(word)[0] for word in cleaned_tokens_job]
    res_docs = [nlp(word)[0] for word in cleaned_tokens_res]

    matched_key = []
    total_sim = 0
    match_count = 0

    for res_word in res_docs:
        for job_word in job_docs:
            sim = res_word.similarity(job_word)
            if sim > 0.7:  
                matched_key.append(job_word.text)
                total_sim += sim
                match_count += 1
                break

    coverage_score = round((len(matched_key) / len(cleaned_tokens_job)) * 100, 2) if cleaned_tokens_job else 0
    similarity_score = round((total_sim / match_count) * 100, 2) if match_count > 0 else 0

    return similarity_score, coverage_score, set(matched_key)


def extract_text_from_pdf(uploaded_file):
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""  
    return text


st.set_page_config(page_title="Resume vs JD Similarity Checker", layout="wide")

st.title("📄 Resume vs Job Description Matcher")
st.write("Paste a Job Description and upload a Resume PDF to check similarity.")

col1, col2 = st.columns(2)

with col1:
    job_desc = st.text_area("📝 Job Description", height=300)

with col2:
    uploaded_file = st.file_uploader("📂 Upload Resume (PDF)", type=["pdf"])
    res_text = ""
    if uploaded_file is not None:
        res_text = extract_text_from_pdf(uploaded_file)
        st.success("✅ Resume uploaded and text extracted.")

if st.button("🔍 Check Similarity"):
    if job_desc.strip() and res_text.strip():
        sim_score, coverage, matched_keywords = compute_similarity(job_desc, res_text)
        st.success(f"✅ Semantic Similarity Score: {sim_score}%")
        st.info(f"📊 Coverage Score: {coverage}% of JD keywords matched")
        st.write("**Matched Keywords:**", ", ".join(matched_keywords) if matched_keywords else "None")
    else:
        st.error("Please provide both Job Description and Resume PDF.")
