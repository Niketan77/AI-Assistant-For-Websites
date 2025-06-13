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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the API key from environment variable
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    st.error("API key not found. Please set the GEMINI_API_KEY environment variable.")
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

def setup_selenium_driver():
    """Sets up a headless Chrome driver for JavaScript rendering."""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        driver = webdriver.Chrome(options=chrome_options)
        return driver, None
    except Exception as e:
        logger.error(f"Selenium setup failed: {str(e)}")
        return None, f"Browser setup failed: {str(e)}. Please ensure Chrome and ChromeDriver are installed."

def extract_with_selenium(url, timeout=15):
    """Extracts content using Selenium for JavaScript-rendered pages."""
    driver, error = setup_selenium_driver()
    if error:
        return None, error
    
    try:
        driver.set_page_load_timeout(timeout)
        driver.get(url)
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(3)
        
        try:
            WebDriverWait(driver, 5).until_not(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".loading, .spinner, [data-loading]"))
            )
        except TimeoutException:
            pass
        
        # Execute JavaScript to ensure all content is loaded
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        
        # Get page source after JavaScript execution
        html_source = driver.page_source
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html_source, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form']):
            element.decompose()
        
        # Extract text from multiple elements
        text_elements = []
        
        # Priority elements for content extraction
        priority_selectors = [
            'main', 'article', '.content', '#content', '.post', '.entry',
            '[role="main"]', '.main-content', '#main-content'
        ]
        
        content_found = False
        for selector in priority_selectors:
            elements = soup.select(selector)
            if elements:
                for element in elements:
                    text = element.get_text(separator=' ', strip=True)
                    if len(text) > 100:
                        text_elements.append(text)
                        content_found = True
                break
        
        # If no priority content found, extract from common elements
        if not content_found:
            for tag in ['p', 'div', 'span', 'section', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']:
                elements = soup.find_all(tag)
                for element in elements:
                    text = element.get_text(strip=True)
                    if len(text) > 20 and text not in text_elements:
                        text_elements.append(text)
        
        # Clean and join text
        combined_text = ' '.join(text_elements)
        cleaned_text = re.sub(r'\s+', ' ', combined_text).strip()
        
        # Get page title
        title = soup.title.string if soup.title else "No title"
        
        # Combine title and content
        final_content = f"Title: {title}\n\nContent: {cleaned_text}"
        
        if len(cleaned_text) < 100:
            return None, "Insufficient content extracted. The page might be heavily JavaScript-dependent or have access restrictions."
        
        return final_content[:20000], None
        
    except TimeoutException:
        return None, "Page load timeout. The website might be slow or unresponsive."
    except WebDriverException as e:
        return None, f"Browser error: {str(e)}"
    except Exception as e:
        return None, f"Content extraction error: {str(e)}"
    finally:
        if driver:
            driver.quit()

def extract_with_requests(url):
    """Fallback method using requests and BeautifulSoup."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        session = requests.Session()
        session.headers.update(headers)
        
        response = session.get(url, timeout=15, allow_redirects=True)
        response.raise_for_status()
        
        # Handle different encodings
        if response.encoding is None:
            response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form']):
            element.decompose()
        
        # Extract text using multiple strategies
        text_parts = []
        
        # Strategy 1: Priority content areas
        priority_selectors = [
            'main', 'article', '.content', '#content', '.post', '.entry',
            '[role="main"]', '.main-content', '#main-content'
        ]
        
        content_found = False
        for selector in priority_selectors:
            elements = soup.select(selector)
            if elements:
                for element in elements:
                    text = element.get_text(separator=' ', strip=True)
                    if len(text) > 100:
                        text_parts.append(text)
                        content_found = True
                break
        
        # Strategy 2: If no main content found, get paragraphs and headings
        if not content_found:
            for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'li']:
                elements = soup.find_all(tag)
                for element in elements:
                    text = element.get_text(strip=True)
                    if len(text) > 15:
                        text_parts.append(text)
        
        # Get page title
        title = soup.title.string if soup.title else "No title"
        
        # Clean and combine text
        combined_text = ' '.join(text_parts)
        cleaned_text = re.sub(r'\s+', ' ', combined_text).strip()
        
        # Combine title and content
        final_content = f"Title: {title}\n\nContent: {cleaned_text}"
        
        if len(cleaned_text) < 50:
            return None, "Insufficient content found. The page might require JavaScript or have access restrictions."
        
        return final_content[:20000], None
        
    except requests.RequestException as e:
        return None, f"Network error: {str(e)}"
    except Exception as e:
        return None, f"Parsing error: {str(e)}"

def fetch_website_content(url, use_selenium=True):
    """Main function to fetch website content with multiple strategies."""
    
    # Validate URL
    validated_url, error = validate_url(url)
    if error:
        return f"Error: {error}", "validation_error"
    
    extraction_method = ""
    content = None
    error_msg = None
    
    # Try Selenium first for JavaScript content
    if use_selenium:
        try:
            content, error_msg = extract_with_selenium(validated_url)
            if content:
                extraction_method = "JavaScript-enabled (Selenium)"
            else:
                logger.warning(f"Selenium extraction failed: {error_msg}")
        except Exception as e:
            logger.error(f"Selenium method failed: {str(e)}")
            error_msg = str(e)
    
    # Fallback to requests method
    if not content:
        try:
            content, fallback_error = extract_with_requests(validated_url)
            if content:
                extraction_method = "Static HTML (Requests)" + (" - Fallback" if use_selenium else "")
            else:
                error_msg = fallback_error
        except Exception as e:
            error_msg = f"All extraction methods failed: {str(e)}"
    
    if content:
        # Calculate content statistics
        stats = {
            'character_count': len(content),
            'word_count': len(content.split()),
            'extraction_method': extraction_method
        }
        return content, extraction_method, stats
    else:
        return f"Error: {error_msg}", "error", {}

def get_gemini_response(prompt):
    """Enhanced Gemini API call with better error handling."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "maxOutputTokens": 2048,
            "temperature": 0.7
        },
        "safetySettings": [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if "candidates" in result and result["candidates"]:
            candidate = result["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                answer = candidate["content"]["parts"][0]["text"].strip()
                return answer
            else:
                return "Error: Invalid response structure from API"
        else:
            return "Error: No candidates in API response"
            
    except requests.RequestException as e:
        return f"Error: API request failed - {str(e)}"
    except (KeyError, IndexError) as e:
        return f"Error: Invalid API response structure - {str(e)}"
    except Exception as e:
        return f"Error: Unexpected error - {str(e)}"

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
                if "Error:" not in content:
                    st.session_state.content = content
                    st.session_state.extraction_method = extraction_method
                    st.session_state.content_stats = stats
                    st.session_state.error = None
                    st.session_state.summary = ""
                    
                    # Success message
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
