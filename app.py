import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import os
from dotenv import load_dotenv
import re
import logging
from urllib.parse import urlparse

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the API keys from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY")

if not GEMINI_API_KEY:
    st.error("GEMINI_API_KEY not found. Please set the GEMINI_API_KEY environment variable.")
    st.stop()

if not SCRAPERAPI_KEY:
    st.error("SCRAPERAPI_KEY not found. Please set the SCRAPERAPI_KEY environment variable.")
    st.stop()

# Streamlit page configuration with wide layout
st.set_page_config(page_title="Enhanced AI Web Agent", layout="wide", initial_sidebar_state="collapsed")

# Enhanced CSS for responsive design with improved color scheme and UI elements
st.markdown("""
<style>
    /* Main container and layout */
    .main > div {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    .main-title {
        color: #2E7D32;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    
    .subtitle {
        color: #424242;
        font-size: 1.1rem;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .user-message {
        background: linear-gradient(135deg, #4285f4 0%, #1976d2 100%);
        color: white;
        padding: 12px 18px;
        border-radius: 18px 18px 4px 18px;
        margin: 8px 0;
        margin-left: 20%;
        box-shadow: 0 2px 8px rgba(66, 133, 244, 0.3);
        font-weight: 500;
    }
    
    .ai-message {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        color: #212121;
        padding: 16px 20px;
        border-radius: 18px 18px 18px 4px;
        margin: 8px 0;
        margin-right: 20%;
        border-left: 4px solid #4caf50;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        line-height: 1.6;
    }
    
    .timestamp {
        font-size: 0.8rem;
        opacity: 0.7;
        margin-top: 5px;
    }
    
    .summary-container {
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        border-radius: 12px;
        padding: 20px;
        margin: 1rem 0;
        border-left: 4px solid #ff9800;
        box-shadow: 0 2px 8px rgba(255, 152, 0, 0.15);
    }
    
    .summary-title {
        color: #ef6c00;
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .summary-content {
        color: #424242;
        line-height: 1.6;
        font-size: 15px;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #4caf50 0%, #2e7d32 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 0.6rem 2rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(76, 175, 80, 0.4) !important;
    }
    
    .error-message {
        background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
        color: #c62828;
        padding: 15px 20px;
        border-radius: 10px;
        border-left: 4px solid #f44336;
        margin: 1rem 0;
    }
    
    .success-message {
        background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
        color: #2e7d32;
        padding: 15px 20px;
        border-radius: 10px;
        border-left: 4px solid #4caf50;
        margin: 1rem 0;
    }
    
    /* Hide Streamlit default elements */
    .stDeployButton {
        display: none;
    }
    
    #MainMenu {
        visibility: hidden;
    }
    
    footer {
        visibility: hidden;
    }
    
    header {
        visibility: hidden;
    }
            
    @media (max-width: 768px) {
        .main-title {
            text-align: left;
            font-size: 2rem;
        }
        
        .subtitle {
            text-align: left;
            font-size: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "content" not in st.session_state:
    st.session_state.content = ""
if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "error" not in st.session_state:
    st.session_state.error = ""
if "extraction_method" not in st.session_state:
    st.session_state.extraction_method = ""
if "content_stats" not in st.session_state:
    st.session_state.content_stats = {}
if "summary" not in st.session_state:
    st.session_state.summary = ""

def validate_url(url):
    """Validates and normalizes URL."""
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        parsed = urlparse(url)
        if not parsed.netloc:
            return None, "Invalid URL format"
        return url, None
    except Exception as e:
        return None, f"URL validation error: {str(e)}"

def extract_with_scraperapi(url):
    """Extracts fully-rendered HTML via ScraperAPI, then cleans & returns text."""
    api_endpoint = f"http://api.scraperapi.com?api_key={SCRAPERAPI_KEY}&render=true&url={url}"
    try:
        resp = requests.get(api_endpoint, timeout=30)
        resp.raise_for_status()
        html = resp.text
        soup = BeautifulSoup(html, 'html.parser')
        # remove scripts/styles/nav/etc.
        for tag in soup(['script','style','nav','header','footer','aside','form']):
            tag.decompose()
        # gather text
        texts = []
        for selector in ['main','article','.content','#content']:
            elems = soup.select(selector)
            if elems:
                for el in elems:
                    t = el.get_text(separator=' ', strip=True)
                    if len(t) > 100:
                        texts.append(t)
                break
        if not texts:
            # fallback to paragraphs
            for p in soup.find_all(['p','h1','h2','li']):
                t = p.get_text(strip=True)
                if len(t) > 20:
                    texts.append(t)
        combined = ' '.join(texts)
        cleaned = re.sub(r'\s+',' ',combined).strip()
        title = soup.title.string if soup.title else "No title"
        if len(cleaned) < 100:
            return None, "Insufficient content extracted by ScraperAPI."
        return f"Title: {title}\n\nContent: {cleaned}", None
    except Exception as e:
        return None, f"ScraperAPI error: {str(e)}"

def extract_with_requests(url):
    """Fallback method using requests and BeautifulSoup."""
    headers = {
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')
        for tag in soup(['script','style','nav','header','footer','aside','form']):
            tag.decompose()
        texts = []
        for selector in ['main','article','.content','#content']:
            elems = soup.select(selector)
            if elems:
                for el in elems:
                    t = el.get_text(separator=' ', strip=True)
                    if len(t) > 100:
                        texts.append(t)
                break
        if not texts:
            for p in soup.find_all(['p','h1','h2','li']):
                t = p.get_text(strip=True)
                if len(t) > 20:
                    texts.append(t)
        combined = ' '.join(texts)
        cleaned = re.sub(r'\s+',' ',combined).strip()
        title = soup.title.string if soup.title else "No title"
        if len(cleaned) < 50:
            return None, "Insufficient content found. The page might require JS or have restrictions."
        return f"Title: {title}\n\nContent: {cleaned}", None
    except Exception as e:
        return None, f"Network/Parsing error: {str(e)}"

def fetch_website_content(url, use_selenium=True):
    """Main function to fetch website content with ScraperAPI + fallback."""
    validated, err = validate_url(url)
    if err:
        return f"Error: {err}", "validation_error"

    # Primary: ScraperAPI
    content, error_msg = extract_with_scraperapi(validated)
    extraction_method = ""
    if content:
        extraction_method = "JavaScript-enabled (ScraperAPI)"
    else:
        logger.warning(f"ScraperAPI failed: {error_msg}")
        # Fallback: static requests
        content, error_msg = extract_with_requests(validated)
        if content:
            extraction_method = "Static HTML (Requests) - Fallback"
        else:
            return f"Error: {error_msg}", "error", {}

    stats = {
        'character_count': len(content),
        'word_count': len(content.split()),
        'extraction_method': extraction_method
    }
    return content, extraction_method, stats

def get_gemini_response(prompt):
    """Enhanced Gemini API call with better error handling."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    data = {
        "contents": [{"parts":[{"text":prompt}]}],
        "generationConfig": {"maxOutputTokens":2048,"temperature":0.7},
        "safetySettings":[
            {"category":"HARM_CATEGORY_HARASSMENT","threshold":"BLOCK_MEDIUM_AND_ABOVE"},
            {"category":"HARM_CATEGORY_HATE_SPEECH","threshold":"BLOCK_MEDIUM_AND_ABOVE"}
        ]
    }
    headers = {"Content-Type":"application/json"}
    try:
        resp = requests.post(url, json=data, headers=headers, timeout=30)
        resp.raise_for_status()
        rj = resp.json()
        candid = rj.get("candidates",[])
        if candid:
            return candid[0]["content"]["parts"][0]["text"].strip()
        return "Error: No candidates in API response"
    except Exception as e:
        return f"Error: API request failed - {str(e)}"

# ——— UI & interaction (unchanged) ———

st.markdown('<h1 class="main-title">🤖 AI Agent To Chat With Websites</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Engage in a natural, interactive conversation about website content!</p>', unsafe_allow_html=True)

url = st.text_input(
    "Website URL", 
    placeholder="https://example.com or paste any website URL here...", 
    help="Enter any website URL - automatically handles both static and JavaScript content!",
    key="url_input"
)

if st.button("🔍 Load Website", key="load_button"):
    if url:
        with st.spinner("🔄 Loading website content..."):
            result = fetch_website_content(url)
            
            if len(result) == 3:
                content, extraction_method, stats = result
                if not content.startswith("Error:"):
                    st.session_state.content = content
                    st.session_state.extraction_method = extraction_method
                    st.session_state.content_stats = stats
                    st.session_state.error = None
                    st.session_state.summary = ""
                    
                    st.markdown(f"""
                    <div class="success-message">
                        ✅ <strong>Website loaded successfully!</strong><br>
                        📊 Extraction Method: {extraction_method}<br>
                        📝 Content Length: {stats.get('character_count', 0):,} characters<br>
                        📖 Word Count: {stats.get('word_count', 0):,} words
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.session_state.error = content
                    st.markdown(f'<div class="error-message">❌ {content}</div>', unsafe_allow_html=True)
            else:
                st.session_state.error = result[0] if result else "Unknown error occurred"
                st.markdown(f'<div class="error-message">❌ {st.session_state.error}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="error-message">⚠️ Please enter a valid URL</div>', unsafe_allow_html=True)

# Chat interface with enhanced styling
if st.session_state.content and not st.session_state.error:
    st.markdown("---")
    
    # Summary section with separate output
    if st.button("📋 Generate Summary", key="summary_button", help="Get an AI-generated summary of the website content"):
        with st.spinner("🤖 Generating summary..."):
            summary_prompt = f"""
            Please provide a comprehensive summary of the following website content. 
            Include key points, main topics, and important information:
            
            {st.session_state.content[:8000]}
            """
            
            summary = get_gemini_response(summary_prompt)
            if summary and not summary.startswith("Error"):
                st.session_state.summary = summary
            else:
                st.session_state.summary = "Unable to generate summary. Please try again."
    
    if st.session_state.summary:
        # Process the summary text to handle Markdown formatting
        processed_summary = st.session_state.summary
        
        # Convert **text** to <strong>text</strong> for proper HTML bold formatting
        processed_summary = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', processed_summary)
        
        # Convert bullet points (lines starting with * ) to proper HTML bullets
        processed_summary = re.sub(r'^\* (.+)$', r'• \1', processed_summary, flags=re.MULTILINE)
        
        # Convert *text* to <em>text</em> for italic formatting (but not for bullet points)
        processed_summary = re.sub(r'(?<!^)\*([^*\n]+?)\*(?!\s)', r'<em>\1</em>', processed_summary, flags=re.MULTILINE)
        
        # Convert newlines to <br> tags
        processed_summary = processed_summary.replace('\n', '<br>')
        
        st.markdown(f"""
        <div class="summary-container">
            <div class="summary-title">
                📋 Website Summary
            </div>
            <div class="summary-content">
                {processed_summary}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Chat interface
    st.subheader("💬 Chat with the Website")
    
    # Display conversation history
    if st.session_state.conversation:
        for i, qa in enumerate(st.session_state.conversation):
            timestamp = qa.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            # User message
            st.markdown(f"""
            <div class="user-message">
                👤 {qa['question']}
                <div class="timestamp">Asked at {timestamp}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # AI response
            st.markdown(f"""
            <div class="ai-message">
                🤖 {qa['answer']}
                <div class="timestamp">Responded at {timestamp}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Input section with original Streamlit design
    col1, col2 = st.columns([4, 1])
    
    with col1:
        question = st.text_input(
            "Ask a question about the website",
            placeholder="Type your question here...",
            key="question_input",
            label_visibility="collapsed"
        )
    
    with col2:
        send_clicked = st.button("Send", key="send_button", help="Send your question", type="primary", use_container_width=True)
    
    # Process message sending
    if send_clicked and question.strip():
        with st.spinner("🤖 AI is thinking..."):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            prompt = f"""
            Based on the following website content, please answer the user's question comprehensively and accurately:
            
            Website Content:
            {st.session_state.content}
            
            User Question: {question}
            
            Please provide a detailed, helpful response based solely on the website content provided.
            """
            
            response = get_gemini_response(prompt)
            
            if response and not response.startswith("Error"):
                st.session_state.conversation.append({
                    'question': question,
                    'answer': response,
                    'timestamp': timestamp
                })
                st.rerun()
            else:
                st.markdown('<div class="error-message">❌ Sorry, I encountered an error processing your question. Please try again.</div>', unsafe_allow_html=True)
    elif send_clicked and not question.strip():
        st.markdown('<div class="error-message">⚠️ Please enter a question</div>', unsafe_allow_html=True)
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Clear Chat", key="clear_button", use_container_width=True):
            st.session_state.conversation = []
            st.rerun()
    
    with col2:
        if st.button("🔄 Reload Website", key="reload_button", use_container_width=True):
            if url:
                with st.spinner("🔄 Reloading..."):
                    result = fetch_website_content(url)
                    if len(result) == 3:
                        content, method, stats = result
                        if "Error:" not in content:
                            st.session_state.content = content
                            st.session_state.extraction_method = method
                            st.session_state.content_stats = stats
                            st.session_state.summary = ""
                            st.success("✅ Website reloaded successfully!")
                            st.rerun()

else:
    # Welcome message when no content is loaded
    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: #666;">
        <h3>👋 Welcome!</h3>
        <p>Enter a website URL above to start chatting with the AI about its content.</p>
        <p>The AI can answer questions, provide summaries, and help you understand any website's content.</p>
    </div>
    """, unsafe_allow_html=True)

# Instructions and tips
with st.expander("ℹ️ How to Use & Tips"):
    st.markdown("""
    ### 🚀 How to Use:
    1. **Enter URL:** Paste any website URL in the input box
    2. **Load Content:** Click "Load Website"
    3. **Generate Summary:** Click the summary button to get an overview
    4. **Start Chatting:** Type questions in the input box and click Send
    
    ### 💡 Tips for Better Results:
    - **Specific Questions:** Ask targeted questions for detailed answers
    - **Context Matters:** The AI remembers your conversation history
    - **Quick Actions:** Use "Generate Summary" for overviews, "Clear Chat" to restart
    
    ### 🔧 Supported Websites:
    - ✅ News sites, blogs, documentation
    - ✅ E-commerce product pages  
    - ✅ Wikipedia and educational content
    
    ### ⚠️ Limitations:
    - Some sites may block automated access
    - Very complex JavaScript applications might need manual review
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🚀 Enhanced AI Web Agent | Built with Streamlit & Google Gemini API</p>
    <p><small>Created by Niketan Choudhari | 
    <a href="https://linkedin.com/in/niketan-choudhari-807980270" target="_blank" style="color: #0077B5;">LinkedIn</a> | 
    <a href="https://github.com/Niketan77" target="_blank" style="color: #333;">GitHub</a></small></p>
</div>
""", unsafe_allow_html=True)
