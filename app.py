import os
import streamlit as st
from openai import OpenAI
import pdfplumber
import tiktoken
import re
import datetime

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
        return "Error in extracting text from PDF"

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

def generate_cover_letter_prompt(job_description, resume_text):
    """Abstract method to generate the prompt for cover letter generation"""
    prompt = f"""
    Write a professional cover letter for a job application. Use the following information:
    
    Resume: {resume_text}
    Job Description: {job_description}
    
    Requirements:
    1. Write a professional cover letter in business letter format
    2. Use placeholders in square brackets [] for personal information that needs to be filled later
    3. Make the content relevant to the resume and job description
    4. Keep it professional and well-structured
    5. Include proper business letter formatting with header and signature
    6. Use any placeholders you think are appropriate for personalization
    """
    return prompt

def generate_ai_cover_letter(job_description, resume_text):
    """Generate AI cover letter with placeholders for personalization"""
    client = initialize_openai_client()
    
    # Use the abstract prompt method
    prompt = generate_cover_letter_prompt(job_description, resume_text)
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a professional cover letter writer. Use placeholders in square brackets for any personal information that should be customized."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"❌ OpenAI API Error: {str(e)}")
        return None

def extract_placeholders_from_text(text):
    """Extract all placeholders in square brackets from the generated cover letter"""
    placeholder_pattern = r'\[([^\]]+)\]'
    placeholders = re.findall(placeholder_pattern, text)
    return list(set(placeholders))  # Remove duplicates

def get_generic_personalization_form(placeholders):
    """Display a generic form for any placeholders found in the AI response"""
    st.subheader("👤 Personalize Your Cover Letter")
    st.info(f"Please fill in the following {len(placeholders)} fields to personalize your cover letter.")
    
    personal_info = {}
    
    with st.form("personalization_form"):
        # Create form fields dynamically based on extracted placeholders
        for i, placeholder in enumerate(placeholders):
            # Determine input type based on placeholder content
            if any(keyword in placeholder.lower() for keyword in ['email', 'mail']):
                value = st.text_input(f"{placeholder}", placeholder="example@email.com")
            elif any(keyword in placeholder.lower() for keyword in ['phone', 'mobile', 'tel']):
                value = st.text_input(f"{placeholder}", placeholder="(123) 456-7890")
            elif any(keyword in placeholder.lower() for keyword in ['address', 'street']):
                value = st.text_area(f"{placeholder}", placeholder="123 Main Street", height=60)
            elif any(keyword in placeholder.lower() for keyword in ['date']):
                # Auto-fill current date
                value = datetime.datetime.now().strftime("%B %d, %Y")
                st.text_input(f"{placeholder}", value=value, disabled=True)
            elif any(keyword in placeholder.lower() for keyword in ['name']):
                value = st.text_input(f"{placeholder}", placeholder="John Doe")
            else:
                # Generic text input for unknown placeholders
                value = st.text_input(f"{placeholder}", placeholder="Enter value")
            
            personal_info[placeholder] = value
        
        submitted = st.form_submit_button("✅ Personalize Cover Letter")
        
        if submitted:
            # Validate that all fields are filled
            empty_fields = [placeholder for placeholder, value in personal_info.items() if not value.strip()]
            if empty_fields:
                st.error(f"❌ Please fill in all fields: {', '.join(empty_fields)}")
                return None
            else:
                st.success("✅ Personal information saved successfully!")
                return personal_info
    
    return None

def replace_placeholders_with_regex(cover_letter, personal_info):
    """Replace placeholders in cover letter using regex"""
    personalized_letter = cover_letter
    
    for placeholder, value in personal_info.items():
        # Use regex to replace the exact placeholder
        pattern = r'\[' + re.escape(placeholder) + r'\]'
        personalized_letter = re.sub(pattern, value, personalized_letter)
    
    return personalized_letter

def main():
    """Main function to handle the Streamlit app logic"""
    # Initialize variables
    final_resume_text = ""
    final_job_description = ""
    generated_cover_letter = None
    personal_info = None
    
    # Streamlit UI
    st.title("📄 CoverCraft - AI Cover Letter Generator")

    # Add a status indicator
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("❌ OPENAI_API_KEY environment variable not set")
        st.info("Please set your OpenAI API key to use AI-generated cover letters")

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
    st.header(" Job Description")
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

    # Generate AI Cover Letter
    st.header("🤖 Generate AI Cover Letter")
    if st.button("🚀 Generate Cover Letter", type="primary"):
        if final_resume_text and final_job_description:
            # Calculate total tokens
            tokenizer = initialize_tokenizer()
            total_tokens = count_tokens(final_resume_text, tokenizer) + count_tokens(final_job_description, tokenizer)
            
            st.info(f" Total tokens being sent to API: {total_tokens:,}")
            
            if total_tokens > TOTAL_SAFE_LIMIT:
                st.error(f"❌ Total tokens ({total_tokens:,}) exceed safe limit ({TOTAL_SAFE_LIMIT:,}) for {MODEL_NAME}. Please reduce content.")
            else:
                with st.spinner("Generating AI cover letter..."):
                    generated_cover_letter = generate_ai_cover_letter(final_job_description, final_resume_text)
                    
                    if generated_cover_letter:
                        # Store in session state for later use
                        st.session_state.generated_cover_letter = generated_cover_letter
                        
                        # Show success message only after generation
                        st.success("✅ AI Cover Letter Generated Successfully!")
                        
                        # Show the generated cover letter
                        st.subheader("📝 Generated Cover Letter (with placeholders)")
                        st.markdown(generated_cover_letter)
                        
                        # Extract placeholders
                        placeholders = extract_placeholders_from_text(generated_cover_letter)
                        
                        if placeholders:
                            st.info(f"🔍 Found {len(placeholders)} placeholders to personalize: {', '.join(placeholders)}")
                        else:
                            st.info("✅ No placeholders found - cover letter is ready!")
                    else:
                        st.error("❌ Failed to generate cover letter. Please check your OpenAI API configuration.")
        else:
            st.error("Please upload a resume and analyze a job description first")

    # Personalization Form (only show if cover letter is generated)
    if 'generated_cover_letter' in st.session_state and st.session_state.generated_cover_letter:
        st.header("👤 Personalize Your Cover Letter")
        
        # Extract placeholders from the generated cover letter
        placeholders = extract_placeholders_from_text(st.session_state.generated_cover_letter)
        
        if placeholders:
            personal_info = get_generic_personalization_form(placeholders)
            
            if personal_info:
                # Replace placeholders with user data
                personalized_letter = replace_placeholders_with_regex(st.session_state.generated_cover_letter, personal_info)
                
                st.subheader("🎉 Your Personalized Cover Letter")
                st.markdown(personalized_letter)
                
                # Add download button
                st.download_button(
                    label="📥 Download Personalized Cover Letter",
                    data=personalized_letter,
                    file_name="personalized_cover_letter.md",
                    mime="text/markdown"
                )
                
                # Show what was replaced
                with st.expander("🔍 Personalization Summary"):
                    st.write("**Replaced placeholders:**")
                    for placeholder, value in personal_info.items():
                        st.write(f"- `[{placeholder}]` → `{value}`")
        else:
            st.info("✅ No placeholders found in the generated cover letter. It's ready to use!")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>CoverCraft - AI-Powered Cover Letter Generator</p>
        <p>Built with Streamlit, pdfplumber, and OpenAI</p>
    </div>
    """, unsafe_allow_html=True)

# Run the main function
if __name__ == "__main__":
    main() 