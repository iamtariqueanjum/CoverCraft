# Token limits configuration - can be easily modified here
RESUME_MAX_TOKENS = 8000  # 5K-10K range as requested
JOB_DESC_MAX_TOKENS = 3000  # 2K tokens for description as requested
TOTAL_SAFE_LIMIT = 16000  # Safe limit for GPT-3.5-turbo (16,385 max)
MODEL_NAME = "gpt-3.5-turbo"  # OpenAI model to use

# Cache configuration
CACHE_TTL = 3600  # Cache time-to-live in seconds (1 hour)

# UI Configuration
TEXT_AREA_MIN_HEIGHT = 80  # Minimum height for text areas
RESUME_TEXT_AREA_HEIGHT = 300  # Height for resume text display
JOB_DESC_TEXT_AREA_HEIGHT = 200  # Height for job description display

# File Configuration
SUPPORTED_FILE_TYPES = ["pdf"]
COVER_LETTER_FILENAME = "personalized_cover_letter.md"
COVER_LETTER_MIME_TYPE = "text/markdown"

# Error Messages
ERROR_MESSAGES = {
    "no_api_key": "❌ OPENAI_API_KEY environment variable not set",
    "api_key_info": "Please set your OpenAI API key to use AI-generated cover letters",
    "pdf_error": "Error reading PDF: {}",
    "api_error": "❌ OpenAI API Error: {}",
    "generation_failed": "❌ Failed to generate cover letter. Please check your OpenAI API configuration.",
    "missing_resume": "❌ Please upload a resume first",
    "missing_job_desc": "❌ Please enter a job description first",
    "missing_both": "❌ Please upload a resume and enter a job description first",
    "token_limit_exceeded": "❌ Total tokens ({}) exceed safe limit ({}) for {}. Please reduce content.",
    "empty_fields": "❌ Please fill in all fields: {}",
    "cache_cleared": "✅ Cache cleared successfully!",
    "personal_info_saved": "✅ Personal information saved successfully!",
    "resume_uploaded": "✅ Resume uploaded and text extracted successfully",
    "job_desc_entered": "✅ Job description entered successfully",
    "cover_letter_generated": "✅ AI Cover Letter Generated Successfully!",
    "pdf_extraction_failed": "❌ Failed to extract text from PDF",
    "no_placeholders": "✅ No placeholders found - cover letter is ready!",
    "no_placeholders_in_letter": "✅ No placeholders found in the generated cover letter. It's ready to use!"
}

# Success Messages
SUCCESS_MESSAGES = {
    "resume_uploaded": "✅ Resume uploaded and text extracted successfully",
    "job_desc_entered": "✅ Job description entered successfully",
    "cover_letter_generated": "✅ AI Cover Letter Generated Successfully!",
    "personal_info_saved": "✅ Personal information saved successfully!",
    "cache_cleared": "✅ Cache cleared successfully!"
}

# Info Messages
INFO_MESSAGES = {
    "upload_resume": "📄 Please upload a resume (PDF format)",
    "enter_job_desc": "📝 Please enter a job description",
    "using_cached": "💾 Using cached cover letter. Upload new resume or change job description to regenerate.",
    "cache_help": "💡 Cache helps improve performance by storing generated cover letters for 1 hour.",
    "found_placeholders": "🔍 Found {} placeholders to personalize: {}"
}

# Placeholder Patterns
PLACEHOLDER_PATTERN = r'\[([^\]]+)\]'

# Input Type Keywords
INPUT_TYPE_KEYWORDS = {
    'email': ['email', 'mail'],
    'phone': ['phone', 'mobile', 'tel'],
    'address': ['address', 'street'],
    'date': ['date'],
    'name': ['name']
}

# Placeholder Defaults
PLACEHOLDER_DEFAULTS = {
    'email': 'example@email.com',
    'phone': '(123) 456-7890',
    'address': '123 Main Street',
    'name': 'John Doe',
    'generic': 'Enter value'
} 