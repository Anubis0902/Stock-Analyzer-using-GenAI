import streamlit as st
import os

st.set_page_config(
    page_title="AI Stock Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Injecting Custom CSS for Rich Aesthetics & Dark Theme
st.markdown("""
    <style>
        /* Base page theme */
        .stApp {
            background-color: #0d1117;
            color: #c9d1d9;
            font-family: 'Inter', sans-serif;
        }
        [data-testid="stHeader"] {
            background-color: transparent;
        }
        /* Style the chat bubbles */
        [data-testid="stChatMessage"] {
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 8px;
            border: 1px solid #30363d;
            background-color: #161b22;
        }
        [data-testid="stChatMessage"] p {
            color: #c9d1d9;
        }
        /* Style the sidebar for dark theme */
        [data-testid="stSidebar"] {
            background-color: #0d1117;
            border-right: 1px solid #30363d;
        }
        /* CSS Card layout for Setup Screen */
        .setup-card {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 30px;
            margin-top: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
        /* Centered headers */
        .center-text {
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

# Synchronize session state keys with environment variables
if "groq_api_key" in st.session_state and st.session_state["groq_api_key"]:
    os.environ["GROQ_API_KEY"] = st.session_state["groq_api_key"]
if "news_api_key" in st.session_state and st.session_state["news_api_key"]:
    os.environ["NEWS_API"] = st.session_state["news_api_key"]

# Check if Groq API Key is configured
groq_api_key = os.environ.get("GROQ_API_KEY")

# ==========================================
# MODE 1: SETUP SCREEN (API Keys Missing)
# ==========================================
if not groq_api_key:
    # Render beautiful main setup screen
    st.markdown("<div style='text-align: center; margin-top: 40px;'>", unsafe_allow_html=True)
    st.title("📈 AI Stock Analyzer")
    st.markdown("### Welcome to your Agentic Investment Assistant!")
    st.markdown("To start analyzing stocks with real-time data, technical trends, and live news, please enter your Groq API key.")
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="setup-card">', unsafe_allow_html=True)
        
        st.markdown("#### 🔑 Credentials Setup")
        groq_key_input = st.text_input(
            "Groq API Key",
            type="password",
            placeholder="gsk_...",
            help="Get your key from console.groq.com"
        )
        
        news_key_input = st.text_input(
            "News API Key (Optional)",
            type="password",
            placeholder="Enter NewsAPI Key",
            help="Get your key from newsapi.org to enable the live news lookup tool."
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚀 Connect Agent", use_container_width=True):
            if groq_key_input:
                # Save keys to session state and environment variables
                st.session_state["groq_api_key"] = groq_key_input
                os.environ["GROQ_API_KEY"] = groq_key_input
                
                if news_key_input:
                    st.session_state["news_api_key"] = news_key_input
                    os.environ["NEWS_API"] = news_key_input
                
                st.success("Successfully connected! Launching workspace...")
                st.rerun()
            else:
                st.error("Please enter a valid Groq API Key to authenticate.")
                
        st.markdown('</div>', unsafe_allow_html=True)

    # Stop execution here to prevent showing chat UI until connected
    st.stop()


# ==========================================
# MODE 2: CHAT INTERFACE (API Keys Configured)
# ==========================================

# Now safe to import agent, since environment variables are fully loaded
from Stock_Analyzer import agent

# Sidebar status and reset credentials option
with st.sidebar:
    st.title("⚙️ Configuration")
    st.success("🟢 Agent Connected via Groq")
    
    st.markdown("---")
    st.markdown("### Credentials in Use:")
    st.code(f"Groq API Key: {'•' * 8}{groq_api_key[-4:] if len(groq_api_key) > 4 else ''}")
    
    news_api = os.environ.get("NEWS_API")
    if news_api:
        st.code(f"News API Key: {'•' * 8}{news_api[-4:] if len(news_api) > 4 else ''}")
    else:
        st.warning("⚠️ News API: Disabled")
        
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Reset Credentials", use_container_width=True):
        # Clear keys and reload
        if "groq_api_key" in st.session_state:
            del st.session_state["groq_api_key"]
        if "news_api_key" in st.session_state:
            del st.session_state["news_api_key"]
        if "GROQ_API_KEY" in os.environ:
            del os.environ["GROQ_API_KEY"]
        if "NEWS_API" in os.environ:
            del os.environ["NEWS_API"]
        st.rerun()

st.title("📈 AI Stock Analyzer")
st.markdown("Ask anything about stock trends, fundamental analysis, and recent news.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("E.g., Should I buy AAPL? Are there any recent news?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Analyzing stock metrics and fetching latest news..."):
            try:
                # Format exactly as the raw agent expects
                messages = [{"role": "user", "content": prompt}]
                
                # Retrieve response from the LangChain agent
                response = agent.invoke({"messages": messages})
                
                # The agent response is a dict containing the messages list with the AI response at the end
                final_content = response['messages'][-1].content
                
                st.markdown(final_content)
                st.session_state.messages.append({"role": "assistant", "content": final_content})
            except Exception as e:
                error_msg = f"An error occurred: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
