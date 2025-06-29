import os
import streamlit as st
from openai import OpenAI
import pdfplumber
import tiktoken

# Token limits configuration - can be easily modified here
RESUME_MAX_TOKENS = 8000  # 5K-10K range as requested
JOB_DESC_MAX_TOKENS = 3000  # 2K tokens for description as requested
TOTAL_SAFE_LIMIT = 16000  # Safe limit for GPT-3.5-turbo (16,385 max)
MODEL_NAME = "gpt-3.5-turbo"  # OpenAI model to use

# Initialize OpenAI client
def initialize_openai_client():
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return client

def initialize_tokenizer():
# Initialize tokenizer
    encoding = tiktoken.encoding_for_model(MODEL_NAME)
    return encoding

def count_tokens(text, tokenizer):
    """Count the number of tokens in a text string"""
    return len(tokenizer.encode(text))

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file using pdfplumber"""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return ""

def truncate_text_to_tokens(text, max_tokens, tokenizer):
    """Truncate text to a maximum number of tokens"""
    tokens = tokenizer.encode(text)
    if len(tokens) <= max_tokens:
        return text, len(tokens)
    
    truncated_tokens = tokens[:max_tokens]
    truncated_text = tokenizer.decode(truncated_tokens)
    return truncated_text, max_tokens

def format_token_info(text, max_tokens, text_type):
    """Format token information for display"""
    tokenizer = initialize_tokenizer()  
    token_count = count_tokens(text, tokenizer)
    truncated_text, final_token_count = truncate_text_to_tokens(text, max_tokens, tokenizer)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(f"{text_type} Tokens", token_count)
    with col2:
        st.metric("Max Tokens", max_tokens)
    with col3:
        if token_count > max_tokens:
            st.metric("Final Tokens", final_token_count, delta=f"-{token_count - max_tokens}")
        else:
            st.metric("Final Tokens", final_token_count)
    
    if token_count > max_tokens:
        st.warning(f"⚠️ {text_type} exceeded {max_tokens} tokens and has been truncated.")
    
    return truncated_text

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
    client = initialize_openai_client()
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
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

def main():
    """Main function to handle the Streamlit app logic"""
    # Initialize variables
    final_resume_text = ""
    final_job_description = ""
    
    # Streamlit UI
    st.title("📄 CoverCraft - PDF Reader with Token Limits")

    # Add a status indicator
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("❌ OPENAI_API_KEY environment variable not set")
        st.info("Please set your OpenAI API key to use AI-generated cover letters")
    elif "insufficient_quota" in str(st.session_state.get('last_error', '')):
        st.warning("⚠️ OpenAI billing issue detected. Using mock cover letters.")

    # Display current token limits
    st.info(f"""
    **📊 Current Token Limits:**
    - Resume: {RESUME_MAX_TOKENS:,} tokens
    - Job Description: {JOB_DESC_MAX_TOKENS:,} tokens
    - Total Safe Limit: {TOTAL_SAFE_LIMIT:,} tokens
    - {MODEL_NAME.upper()} Context: 16,385 tokens
    """)

    # Resume upload and processing
    st.header("📋 Resume Upload")
    resume = st.file_uploader("Upload your resume", type=["pdf"])

    resume_text = ""
    if resume:
        with st.spinner("Extracting text from PDF..."):
            resume_text = extract_text_from_pdf(resume)
        
        if resume_text:
            st.success("✅ Resume uploaded and text extracted successfully")
            
            # Show token information for resume
            st.subheader("📊 Resume Token Analysis")
            final_resume_text = format_token_info(resume_text, RESUME_MAX_TOKENS, "Resume")
            
            # Show extracted text in expander
            with st.expander("📄 View Extracted Resume Text"):
                st.text_area("Resume Text", final_resume_text, height=300, disabled=True)
        else:
            st.error("❌ Failed to extract text from PDF")
    else:
        st.info("📄 Please upload a resume (PDF format)")

    # Job description input
    st.header("💼 Job Description")
    job_description = st.text_area("Enter the job description", height=200)
    
    if st.button("📊 Analyze Job Description", type="primary"):
        if job_description:
            # Show token information for job description
            st.success("✅ Job description uploaded and text extracted successfully")
            
            st.subheader("📊 Job Description Token Analysis")
            final_job_description = format_token_info(job_description, JOB_DESC_MAX_TOKENS, "Job Description")
            
            # Show final job description
            with st.expander("📄 View Final Job Description"):
                st.text_area("Job Description", final_job_description, height=200, disabled=True)
        else:
            st.error("❌ Please enter a job description first")

    # Generate cover letter
    st.header("✍️ Generate Cover Letter")
    if st.button("🚀 Generate Cover Letter", type="primary"):
        if resume and job_description:
            # Calculate total tokens
            tokenizer = initialize_tokenizer()
            total_tokens = count_tokens(final_resume_text, tokenizer) + count_tokens(final_job_description, tokenizer)
            
            st.info(f"📊 Total tokens being sent to API: {total_tokens:,}")
            
            if total_tokens > TOTAL_SAFE_LIMIT:
                st.error(f"❌ Total tokens ({total_tokens:,}) exceed safe limit ({TOTAL_SAFE_LIMIT:,}) for {MODEL_NAME}. Please reduce content.")
            else:
                with st.spinner("Generating cover letter..."):
                    cover_letter = generate_cover_letter(final_job_description, final_resume_text)
                    
                    st.subheader("📝 Generated Cover Letter")
                    st.markdown(cover_letter)
                    
                    # Add download button
                    st.download_button(
                        label="📥 Download Cover Letter",
                        data=cover_letter,
                        file_name="cover_letter.md",
                        mime="text/markdown"
                    )
        else:
            st.error("Please upload a resume and analyze a job description first")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>CoverCraft - Smart PDF Processing with Token Management</p>
        <p>Built with Streamlit, pdfplumber, and OpenAI</p>
    </div>
    """, unsafe_allow_html=True)

# Run the main function
if __name__ == "__main__":
    main()

