import streamlit as st
import datetime
from constants import (
    RESUME_MAX_TOKENS, 
    JOB_DESC_MAX_TOKENS, 
    TOTAL_SAFE_LIMIT, 
    MODEL_NAME,
    ERROR_MESSAGES,
    SUCCESS_MESSAGES,
    INFO_MESSAGES,
    TEXT_AREA_MIN_HEIGHT,
    RESUME_TEXT_AREA_HEIGHT,
    JOB_DESC_TEXT_AREA_HEIGHT,
    COVER_LETTER_FILENAME,
    COVER_LETTER_MIME_TYPE
)
from utils import (
    count_tokens,
    extract_text_from_pdf,
    calculate_content_hash,
    extract_placeholders,
    determine_input_type,
    get_placeholder_default,
    replace_placeholders,
    validate_file_type,
    format_token_count,
    validate_required_fields,
    convert_cover_letter_to_csv
)
from helpers import (
    check_openai_api_key,
    validate_token_limits,
    get_cached_cover_letter,
    clear_cover_letter_cache
)

def initialize_tokenizer():
    """Initialize tokenizer for token counting"""
    import tiktoken
    return tiktoken.encoding_for_model(MODEL_NAME)

def truncate_text_to_tokens(text: str, max_tokens: int, tokenizer) -> tuple[str, int]:
    """Truncate text to a maximum number of tokens"""
    tokens = tokenizer.encode(text)
    if len(tokens) <= max_tokens:
        return text, len(tokens)
    
    truncated_tokens = tokens[:max_tokens]
    truncated_text = tokenizer.decode(truncated_tokens)
    return truncated_text, max_tokens

def format_token_info(text: str, max_tokens: int, text_type: str) -> str:
    """Format token information for display"""
    tokenizer = initialize_tokenizer()  
    token_count = count_tokens(text)
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

def get_generic_personalization_form(placeholders: list[str]) -> dict[str, str] | None:
    """Display a generic form for any placeholders found in the AI response"""
    st.subheader("👤 Personalize Your Cover Letter")
    st.info(f"Please fill in the following {len(placeholders)} fields to personalize your cover letter.")
    
    personal_info = {}
    
    with st.form("personalization_form"):
        # Create form fields dynamically based on extracted placeholders
        for placeholder in placeholders:
            input_type = determine_input_type(placeholder)
            default_value = get_placeholder_default(placeholder)
            
            if input_type == 'email':
                value = st.text_input(f"{placeholder}", placeholder=default_value)
            elif input_type == 'phone':
                value = st.text_input(f"{placeholder}", placeholder=default_value)
            elif input_type == 'address':
                value = st.text_area(f"{placeholder}", placeholder=default_value, height=TEXT_AREA_MIN_HEIGHT)
            elif input_type == 'date':
                # Auto-fill current date
                value = datetime.datetime.now().strftime("%B %d, %Y")
                st.text_input(f"{placeholder}", value=value, disabled=True)
            elif input_type == 'name':
                value = st.text_input(f"{placeholder}", placeholder=default_value)
            else:
                # Generic text input for unknown placeholders
                value = st.text_input(f"{placeholder}", placeholder=default_value)
            
            personal_info[placeholder] = value
        
        # Submit button must be inside the form
        submitted = st.form_submit_button("✅ Personalize Cover Letter")
    
    # Handle form submission outside the form context
    if submitted:
        # Validate that all fields are filled
        is_valid, empty_fields = validate_required_fields(personal_info, placeholders)
        if not is_valid:
            st.error(ERROR_MESSAGES["empty_fields"].format(', '.join(empty_fields)))
            return None
        else:
            st.success(SUCCESS_MESSAGES["personal_info_saved"])
            return personal_info
    
    return None

def manage_session_state():
    """Initialize and manage session state variables"""
    if 'generated_cover_letter' not in st.session_state:
        st.session_state.generated_cover_letter = None
    if 'personal_info' not in st.session_state:
        st.session_state.personal_info = None
    if 'resume_hash' not in st.session_state:
        st.session_state.resume_hash = None
    if 'job_desc_hash' not in st.session_state:
        st.session_state.job_desc_hash = None

def main():
    """Main function to handle the Streamlit app logic"""
    # Initialize session state
    manage_session_state()
    
    # Streamlit UI
    st.title("📄 CoverCraft - AI Cover Letter Generator")

    # Add cache management in sidebar
    with st.sidebar:
        st.header("⚙️ Cache Management")
        if st.button("🗑️ Clear Cache", help="Clear all cached data"):
            clear_cover_letter_cache()
            st.cache_data.clear()
            st.session_state.generated_cover_letter = None
            st.session_state.personal_info = None
            st.session_state.resume_hash = None
            st.session_state.job_desc_hash = None
            st.success(SUCCESS_MESSAGES["cache_cleared"])
        
        st.info(INFO_MESSAGES["cache_help"])

    # Add a status indicator
    if not check_openai_api_key():
        return

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
        if not validate_file_type(resume.name):
            st.error(f"❌ Unsupported file type. Please upload a PDF file.")
            return
            
        with st.spinner("Extracting text from PDF..."):
            try:
                resume_text = extract_text_from_pdf(resume)
            except Exception as e:
                st.error(ERROR_MESSAGES["pdf_error"].format(str(e)))
                return
        
        if resume_text:
            st.success(SUCCESS_MESSAGES["resume_uploaded"])
            
            # Show token information for resume
            st.subheader("📊 Resume Token Analysis")
            final_resume_text = format_token_info(resume_text, RESUME_MAX_TOKENS, "Resume")
            
            # Show extracted text in expander
            with st.expander("📄 View Extracted Resume Text"):
                st.text_area("Resume Text", final_resume_text, height=RESUME_TEXT_AREA_HEIGHT, disabled=True)
        else:
            st.error(ERROR_MESSAGES["pdf_extraction_failed"])
    else:
        final_resume_text = ""
        st.info(INFO_MESSAGES["upload_resume"])

    # Job description input
    st.header("📝 Job Description")
    job_description = st.text_area("Enter the job description", height=JOB_DESC_TEXT_AREA_HEIGHT)
    
    # Automatically process job description when entered
    if job_description:
        st.success(SUCCESS_MESSAGES["job_desc_entered"])
        
        st.subheader("📊 Job Description Token Analysis")
        final_job_description = format_token_info(job_description, JOB_DESC_MAX_TOKENS, "Job Description")
        
        # Show final job description
        with st.expander("📄 View Final Job Description"):
            st.text_area("Job Description", final_job_description, height=JOB_DESC_TEXT_AREA_HEIGHT, disabled=True)
    else:
        final_job_description = ""
        st.info(INFO_MESSAGES["enter_job_desc"])

    # Check if content has changed
    current_resume_hash = calculate_content_hash(final_resume_text, "") if final_resume_text else None
    current_job_desc_hash = calculate_content_hash("", final_job_description) if final_job_description else None
    
    # Clear cached cover letter if content has changed
    if (current_resume_hash != st.session_state.resume_hash or 
        current_job_desc_hash != st.session_state.job_desc_hash):
        st.session_state.generated_cover_letter = None
        st.session_state.personal_info = None
        st.session_state.resume_hash = current_resume_hash
        st.session_state.job_desc_hash = current_job_desc_hash

    # Generate AI Cover Letter
    st.header("🤖 Generate AI Cover Letter")
    
    # Show cached status if available
    if st.session_state.generated_cover_letter:
        st.info(INFO_MESSAGES["using_cached"])
    
    if st.button("🚀 Generate Cover Letter", type="primary"):
        if final_resume_text and final_job_description:
            # Calculate total tokens
            total_tokens = count_tokens(final_resume_text) + count_tokens(final_job_description)
            
            st.info(f"📊 Total tokens being sent to API: {format_token_count(total_tokens)}")
            
            # Validate token limits
            is_valid, exceeded_content = validate_token_limits(final_resume_text, final_job_description)
            if not is_valid:
                st.error(ERROR_MESSAGES["token_limit_exceeded"].format(
                    format_token_count(total_tokens), format_token_count(TOTAL_SAFE_LIMIT), MODEL_NAME
                ))
            else:
                with st.spinner("Generating AI cover letter..."):
                    generated_cover_letter = get_cached_cover_letter(final_resume_text, final_job_description)
                    
                    if generated_cover_letter:
                        # Store in session state for later use
                        st.session_state.generated_cover_letter = generated_cover_letter
                        
                        # Show success message only after generation
                        st.success(SUCCESS_MESSAGES["cover_letter_generated"])
                        
                        # Show the generated cover letter
                        st.subheader("📝 Generated Cover Letter (with placeholders)")
                        st.markdown(generated_cover_letter)
                        
                        # Extract placeholders
                        placeholders = extract_placeholders(generated_cover_letter)
                        
                        if placeholders:
                            st.info(INFO_MESSAGES["found_placeholders"].format(len(placeholders), ', '.join(placeholders)))
                        else:
                            st.info(ERROR_MESSAGES["no_placeholders"])
                    else:
                        st.error(ERROR_MESSAGES["generation_failed"])
        else:
            if not final_resume_text:
                st.error(ERROR_MESSAGES["missing_resume"])
            elif not final_job_description:
                st.error(ERROR_MESSAGES["missing_job_desc"])
            else:
                st.error(ERROR_MESSAGES["missing_both"])

    # Personalization Form (only show if cover letter is generated)
    if st.session_state.generated_cover_letter:
        st.header("👤 Personalize Your Cover Letter")
        
        # Extract placeholders from the generated cover letter
        placeholders = extract_placeholders(st.session_state.generated_cover_letter)
        
        if placeholders:
            personal_info = get_generic_personalization_form(placeholders)
            
            if personal_info:
                # Replace placeholders with user data
                personalized_letter = replace_placeholders(st.session_state.generated_cover_letter, personal_info)
                
                st.subheader("🎉 Your Personalized Cover Letter")
                st.markdown(personalized_letter)
                
                # Convert to CSV format for download
                csv_data = convert_cover_letter_to_csv(personalized_letter, personal_info)
                
                # Add download button
                st.download_button(
                    label="📥 Download Personalized Cover Letter (CSV)",
                    data=csv_data,
                    file_name=COVER_LETTER_FILENAME,
                    mime=COVER_LETTER_MIME_TYPE
                )
                
                # Show what was replaced
                with st.expander("🔍 Personalization Summary"):
                    st.write("**Replaced placeholders:**")
                    for placeholder, value in personal_info.items():
                        st.write(f"- `[{placeholder}]` → `{value}`")
        else:
            st.info(ERROR_MESSAGES["no_placeholders_in_letter"])

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