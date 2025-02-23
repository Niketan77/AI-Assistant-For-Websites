import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

# Streamlit page configuration with wide layout
st.set_page_config(page_title="AI AGENT ", layout="wide")

# Minimal CSS for clean, no-background, wide UI with smaller buttons
st.markdown("""
    <style>
    body {
        color: #000000; /* Default black text for readability */
        margin: 0; /* Remove default margins */
        padding: 0; /* Remove default padding */
    }
    .stButton>button {
        background-color: #4CAF50; /* Streamlit default green */
        color: white;
        border: none;
        border-radius: 4px;
        padding: 5px 10px;  /* Reduced padding for smaller buttons */
        font-size: 14px;  /* Smaller font size */
        margin-top: 10px;
        width: auto;  /* Let button size adjust based on content */
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .stTextInput>div>input {
        background-color: transparent; /* No background for inputs */
        color: #000000; /* Black text */
        border: 1px solid #ccc;
        border-radius: 4px;
        padding: 12px;
        font-size: 16px;
        margin-top: 10px;
        width: 100%; /* Stretch inputs horizontally */
    }
    .stSuccess {
        background-color: #4CAF50; /* Streamlit default green */
        color: white;
        padding: 12px;
        border-radius: 4px;
        margin-top: 10px;
        width: 100%; /* Stretch success messages horizontally */
    }
    .stError {
        background-color: #f44336; /* Streamlit default red */
        color: white;
        padding: 12px;
        border-radius: 4px;
        margin-top: 10px;
        width: 100%; /* Stretch error messages horizontally */
    }
    .chat-container {
        padding: 5px 0; /* Minimal vertical padding, no horizontal padding */
        border-radius: 4px;
        margin-top: 10px;
        margin-bottom: 10px;
        width: 100%; /* Stretch chat horizontally */
    }
    .timestamp {
        font-size: 12px;
        color: #666;
        font-style: italic;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for website content, chat history, and errors
if "content" not in st.session_state:
    st.session_state.content = ""  # Holds the website text
if "conversation" not in st.session_state:
    st.session_state.conversation = []  # Holds chat history with timestamps
if "error" not in st.session_state:
    st.session_state.error = ""  # Tracks errors

def fetch_website_content(url):
    """Fetches text from a website's paragraph tags with improved error handling and user-agent."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}  # Mimic a browser
    try:
        response = requests.get(url, headers=headers, timeout=10)  # Add user-agent and timeout
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        # Try different tags if <p> fails (e.g., <div>, <span>)
        paragraphs = soup.find_all('p')
        if not paragraphs:  # If no <p> tags, try <div> or other common tags
            paragraphs = soup.find_all('div') + soup.find_all('span')
        text = ' '.join(p.get_text().strip() for p in paragraphs if p.get_text().strip())  # Clean text
        if not text:
            return "Error: No content found on this website. Try a different URL with static text (e.g., Wikipedia)."
        return text[:15000]  # Increased limit for more content
    except requests.RequestException as e:
        error_msg = f"Error: Could not fetch website - {str(e)}"
        return error_msg
    except Exception as e:
        error_msg = f"Error: Parsing failed - {str(e)}"
        return error_msg

def get_gemini_response(prompt):
    """Calls the Gemini API with the prompt, ensuring detailed, relevant, and conversational responses."""
    api_key = "AIzaSyACIafUagUoPgjKyC-lzXQl4ohmRQBS8Ao"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {"maxOutputTokens": 2000, "temperature": 0.8}  # Longer, more natural responses
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        if "candidates" in result and result["candidates"]:
            answer = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            return answer
        else:
            return "Error: No candidates in API response"
    except requests.RequestException as e:
        return f"Error: API request failed - {str(e)}"
    except (KeyError, IndexError) as e:
        return f"Error: Invalid API response - {str(e)}"

# Main app layout (simple, wide, single-column)
st.title("AI Agent To Interact With Any Website")
st.write("Enter a website URL and engage in a natural, interactive conversation about its content!")

# URL input and loading section (wide, single column)
url = st.text_input("Website URL", placeholder="https://example.com", key="url_input")
if st.button("Load Website", key="load_button"):
    if url:
        with st.spinner("Loading..."):
            time.sleep(1)  # Simulate loading for better UX
            content = fetch_website_content(url)
            st.session_state.content = content
            st.session_state.conversation = []  # Reset chat history
            st.session_state.error = ""
            if "Error" in content:
                st.error(content)
            else:
                st.success("Website loaded successfully!")
    else:
        st.warning("Please enter a valid URL.")

# Chat interface (wide, single column)
if st.session_state.content and "Error" not in st.session_state.content:
    st.subheader("Chat with the Website")
    
    # Display chat history with timestamps, using Streamlit defaults
    for qa in st.session_state.conversation:
        timestamp = qa.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        st.markdown(f"""
        <div class="chat-container">
            <div style="text-align: right;">
                <p><strong>You:</strong> {qa['question']}</p>
                <span class="timestamp">You, {timestamp}</span>
            </div>
            <div>
                <p><strong>AI:</strong> {qa['answer']}</p>
                <span class="timestamp">AI, {timestamp}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Chat input and actions (wide, single column)
    # Chat input and actions (wide, single column)
    row = st.columns([5, 1])  # Adjust the ratio as needed
    with row[0]:
        question = st.text_input("Ask a question about the website", key="question_input", placeholder="e.g., Ask anything to AI.")
    with row[1]:
        if st.button("Send", key="send_button"):
            if question:
                with st.spinner("Loading..."):
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    prompt = (
                        "You are an expert in web content analysis and a highly interactive conversational AI assistant. "
                        "When answering, provide detailed, specific insights and refer directly to facts, events, or examples mentioned in the website content. "
                        "Include technical details when needed and use concrete examples to support your answer. "
                        "If the question is unclear or requires more context, politely ask targeted follow-up questions. "
                        "Avoid generic responses; be precise, specific, and advanced in your explanation.\n\n"
                        f"Website content: {st.session_state.content}\n\n"
                        "Conversation history:\n"
                    )
                    for qa in st.session_state.conversation:
                        prompt += f"User: {qa['question']}\nAssistant: {qa['answer']}\n"
                    prompt += f"User: {question}\nAssistant:"
                    answer = get_gemini_response(prompt)
                    st.session_state.conversation.append({
                        "question": question,
                        "answer": answer,
                        "timestamp": timestamp
                    })
                    st.rerun()
            else:
                st.warning("Please enter a question.")

    # Clear chat button (wide, single column)
    if st.button("Clear Chat", key="clear_button"):
        st.session_state.conversation = []
        st.rerun()
else:
    if st.session_state.error:
        st.error(st.session_state.error)
    else:
        st.info("Load a website to start chatting!")

st.markdown("""
    <footer style="text-align: center; padding: 20px; color: #666;">
        Build by Niketan Choudhari | Using Google Gemini Ai| 
        <a href="https://linkedin.com/in/niketan-choudhari-807980270" target="_blank" style="color: #0077B5; margin-right: 10px;">LinkedIn</a> | 
        <a href="https://github.com/Niketan77" target="_blank" style="color: #333;">GitHub</a>
    </footer>
""", unsafe_allow_html=True)