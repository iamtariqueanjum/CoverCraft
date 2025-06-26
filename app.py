import os
import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# TODO prompt customization based on resume
def generate_prompt_based_on_resume(resume):
    prompt = f"""
    You are a helpful assistant that generates cover letters for job applications.
    You are given a resume.
    You need to generate a prompt for the job description based on the resume.
    The prompt should be in the same language as the job description.
    The prompt should be 1-2 paragraphs long.
    The prompt should be formatted in markdown.
    """
    return prompt


def generate_cover_letter(job_description, resume):
    prompt = generate_prompt_based_on_resume(resume)

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional cover letter writer."},
                {"role": "user", "content": f"Resume: {resume}\n\nJob Description: {job_description}\n\nPlease write a professional cover letter based on the resume and job description."}
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating cover letter: {str(e)}"


st.title("Welcome to CoverCraft")

resume = st.file_uploader("Upload your resume", type=["pdf"])

resume_text = ""
if resume:
    resume_text = resume.read()
else:
    st.error("Please upload a resume")

# TODO: extract resume text from pdf

job_description = st.text_area("Enter the job description", height=200)

# TODO: extract job description from job description file

# TODO generate cover letter for download

# TODO we can let user save cover letter and generate multiple cover letters

# TODO we can let user save job description and generate multiple cover letters

# TODO we can let user save resume and generate multiple cover letters

# TODO we can let user save cover letter and generate multiple cover letters
if st.button("Generate Cover Letter"):
    if resume_text and job_description:
        cover_letter = generate_cover_letter(job_description, resume_text)
        st.markdown(cover_letter)
    else:
        st.error("Please upload a resume and enter a job description")

