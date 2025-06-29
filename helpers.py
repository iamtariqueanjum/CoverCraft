import streamlit as st
import openai
import os
from typing import Optional, Tuple
from constants import (
    MODEL_NAME, 
    RESUME_MAX_TOKENS, 
    JOB_DESC_MAX_TOKENS, 
    TOTAL_SAFE_LIMIT,
    ERROR_MESSAGES
)
from utils import count_tokens

def check_openai_api_key() -> bool:
    """Check if OpenAI API key is available."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error(ERROR_MESSAGES["no_api_key"])
        st.info(ERROR_MESSAGES["api_key_info"])
        return False
    return True

def validate_token_limits(resume_text: str, job_description: str) -> Tuple[bool, str]:
    """Validate that content doesn't exceed token limits."""
    resume_tokens = count_tokens(resume_text)
    job_desc_tokens = count_tokens(job_description)
    total_tokens = resume_tokens + job_desc_tokens
    
    if resume_tokens > RESUME_MAX_TOKENS:
        return False, f"resume ({resume_tokens} tokens)"
    
    if job_desc_tokens > JOB_DESC_MAX_TOKENS:
        return False, f"job description ({job_desc_tokens} tokens)"
    
    if total_tokens > TOTAL_SAFE_LIMIT:
        return False, f"total content ({total_tokens} tokens)"
    
    return True, ""

def generate_cover_letter_prompt(resume_text: str, job_description: str) -> str:
    """Generate the prompt for cover letter generation."""
    prompt = f"""You are an expert cover letter writer. Create a professional cover letter based on the following resume and job description.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

INSTRUCTIONS:
1. Write a compelling cover letter that highlights relevant skills and experiences from the resume
2. Address the specific requirements and responsibilities mentioned in the job description
3. Use a professional tone and structure
4. Include placeholders in square brackets [PLACEHOLDER_NAME] for personal information that the user will fill in later, such as:
   - [Your Name]
   - [Your Email]
   - [Your Phone]
   - [Your Address]
   - [Company Name]
   - [Hiring Manager Name]
   - [Date]
   - [Specific achievements or experiences]
5. Make the cover letter specific to the job and company
6. Keep it concise but impactful (around 300-400 words)
7. End with a strong call to action

FORMAT:
- Professional business letter format
- Include all necessary placeholders
- Make it ready for the user to personalize with their specific information

Generate the cover letter now:"""

    return prompt

@st.cache_data(ttl=3600)
def generate_cover_letter_with_cache(resume_text: str, job_description: str, content_hash: str) -> Optional[str]:
    """Generate cover letter with caching based on content hash."""
    try:
        # Validate API key
        if not check_openai_api_key():
            return None
        
        # Validate token limits
        is_valid, exceeded_content = validate_token_limits(resume_text, job_description)
        if not is_valid:
            st.error(ERROR_MESSAGES["token_limit_exceeded"].format(
                exceeded_content, TOTAL_SAFE_LIMIT, MODEL_NAME
            ))
            return None
        
        # Generate prompt
        prompt = generate_cover_letter_prompt(resume_text, job_description)
        
        # Make API call
        api_key = os.getenv("OPENAI_API_KEY")
        client = openai.OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are an expert cover letter writer who creates professional, personalized cover letters."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        cover_letter = response.choices[0].message.content.strip()
        
        if not cover_letter:
            st.error(ERROR_MESSAGES["generation_failed"])
            return None
        
        return cover_letter
        
    except openai.AuthenticationError:
        st.error("❌ Invalid OpenAI API key. Please check your configuration.")
        return None
    except openai.RateLimitError:
        st.error("❌ Rate limit exceeded. Please try again later.")
        return None
    except openai.APIError as e:
        st.error(ERROR_MESSAGES["api_error"].format(str(e)))
        return None
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        return None

def get_cached_cover_letter(resume_text: str, job_description: str) -> Optional[str]:
    """Get cached cover letter if available, otherwise generate new one."""
    from utils import calculate_content_hash
    
    # Calculate content hash for cache key
    content_hash = calculate_content_hash(resume_text, job_description)
    
    # Check if we have cached result for this content
    cache_key = f"cover_letter_{content_hash}"
    cached_letter = st.session_state.get(cache_key)
    
    if cached_letter:
        return cached_letter
    
    # Generate new cover letter
    cover_letter = generate_cover_letter_with_cache(resume_text, job_description, content_hash)
    
    if cover_letter:
        # Cache the result
        st.session_state[cache_key] = cover_letter
        return cover_letter
    
    return None

def clear_cover_letter_cache():
    """Clear all cached cover letters from session state."""
    keys_to_remove = [key for key in st.session_state.keys() if key.startswith("cover_letter_")]
    for key in keys_to_remove:
        del st.session_state[key] 