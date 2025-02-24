# AI-Assistant-For-Websites

## Project Description
AI-Assistant-For-Websites is a Streamlit-based application that enables users to interact with any website through a conversational AI agent. The application fetches content from a specified website and allows users to ask questions about that content. Leveraging the Google Gemini API, the assistant provides detailed, contextual, and dynamically generated responses based on the website's content.

## Features
- **Dynamic Website Content Extraction:** Uses `requests` and `BeautifulSoup` to scrape text from websites.
- **Interactive Chat Interface:** Built with Streamlit, providing a clean and responsive chat interface for asking questions and receiving detailed answers.
- **AI-Powered Responses:** Integrates with the Google Gemini API to generate comprehensive and context-aware replies.
- **Custom Styling:** Minimal CSS customizations to ensure a wide, accessible, and modern user interface.

## Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Niketan77/AI-Assistant-For-Websites.git
   cd AI-Assistant-For-Websites
   ```

2. **Set Up Virtual Environment (Optional but Recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use "venv\Scripts\activate"
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run the Application:**
   ```bash
   streamlit run app.py
   ```

2. **Using the App:**
   - Enter a valid website URL (e.g., `https://example.com`) into the input field.
   - Click the **Load Website** button to fetch and display the website's content.
   - Once the content loads successfully, use the chat interface to ask questions about the website.
   - The AI assistant will process the session's history and website content to provide insightful answers.

## Contributing
Contributions are welcome! If you have feature suggestions, bug fixes, or improvements, please follow these steps:
1. Fork the project.
2. Create a new branch (`git checkout -b feature-name`).
3. Commit your changes (`git commit -m "Add new feature"`).
4. Push to the branch (`git push origin feature-name`).
5. Open a pull request with a detailed description of your changes.

Please adhere to the coding style and include appropriate tests for any new features.

## Contact
Developed by [Niketan Choudhari](https://linkedin.com/in/niketan-choudhari-807980270). For questions, suggestions, or issues, please contact via GitHub or LinkedIn.

## Acknowledgments
- [Streamlit](https://streamlit.io/) for providing the tools to build interactive UIs.
- [Google Gemini API](https://developers.generativelanguage.googleapis.com/) for powering the conversational AI.
- Thanks to all contributors and the open source community for their support and continuous improvements.
