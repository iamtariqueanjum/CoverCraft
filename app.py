import os
import streamlit as st
from openai import OpenAI

# Initialize OpenAI client
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


def generate_mock_cover_letter(job_description, resume):
    """Generate a mock cover letter when OpenAI API is not available"""
    return f"""
# Professional Cover Letter

Dear Hiring Manager,

I am writing to express my strong interest in the position you have available. With my background and experience, I believe I would be an excellent fit for your team.

Based on the job description you provided, I understand you are looking for a candidate who can contribute effectively to your organization. My experience aligns well with your requirements, and I am excited about the opportunity to bring my skills and enthusiasm to your company.

I am particularly drawn to this role because it offers the chance to work on challenging projects while contributing to meaningful outcomes. I am confident that my background, combined with my strong work ethic and dedication to excellence, would make me a valuable addition to your team.

Thank you for considering my application. I look forward to the opportunity to discuss how my skills and experience can benefit your organization.

Sincerely,
[Your Name]

---
*This is a mock cover letter generated for demonstration purposes. For a personalized cover letter, please ensure your OpenAI API key is properly configured and has sufficient credits.*
"""


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
        error_msg = str(e)
        st.warning("⚠️ OpenAI API Error: " + error_msg)
        st.info("💡 Generating a mock cover letter instead. To use AI-generated cover letters, please check your OpenAI billing status.")
        return generate_mock_cover_letter(job_description, resume)


st.title("Welcome to CoverCraft")

# Add a status indicator
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("❌ OPENAI_API_KEY environment variable not set")
    st.info("Please set your OpenAI API key to use AI-generated cover letters")
elif "insufficient_quota" in str(st.session_state.get('last_error', '')):
    st.warning("⚠️ OpenAI billing issue detected. Using mock cover letters.")

resume = st.file_uploader("Upload your resume", type=["pdf"])

resume_text = ""
if resume:
    resume_text = resume.read()
    st.success("✅ Resume uploaded successfully")
else:
    st.info("📄 Please upload a resume (PDF format)")

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
        with st.spinner("Generating cover letter..."):
            cover_letter = generate_cover_letter(job_description, resume_text)
            st.markdown(cover_letter)
            
            # Add download button
            st.download_button(
                label="📥 Download Cover Letter",
                data=cover_letter,
                file_name="cover_letter.md",
                mime="text/markdown"
            )
    else:
        st.error("Please upload a resume and enter a job description")

