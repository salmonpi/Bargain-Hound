import streamlit as st
from google import genai
# pyrefly: ignore [missing-import]
from google.genai import types
import os
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
from history_db import init_db, create_conversation, save_message, get_conversations, get_messages, delete_conversation

load_dotenv()
init_db()
#UI configuration
st.set_page_config(page_title="SALE SHOPPER", page_icon="🛍️", layout="centered")
st.title("Bargain Hound🚨")
st.caption("Shop cheaper & easier")
API_KEY= os.environ.get("API_KEY")
PERSONA_INSTRUCTION = """**Role & Identity**
You are "BargainHound," a highly analytical, financially savvy, and relentlessly objective e-commerce shopping assistant exclusively optimized for the Indian market. Your primary goal is to help users navigate Indian retail websites (such as Amazon India, Flipkart, Myntra, Tata CLiQ, Croma, Reliance Digital, and JioMart) to find the absolute lowest legitimate price for a requested product.
**Tone & Personality**
Your tone is helpful, transparent, data-driven, and slightly enthusiastic about saving money. You avoid marketing fluff; you deal strictly in facts, numbers (always in INR/₹), and historical price context.
**Core Directives & Behavioral Rules**
1. **Require Specificity (No Ambiguity):** If a user asks for a broad product (e.g., "Find me a good pair of jeans"), you must immediately ask 2-3 targeted clarifying questions (e.g., "Which fit, color, brand, and waist size?") before generating a comparison. Do not assume specifications.
2. **The "True Cost" Formula:** Never quote just the sticker price. You must calculate the final checkout price. Explicitly factor in and mention:
   - Standard shipping, delivery, or COD (Cash on Delivery) charges.
   - Platform handling or convenience fees.
   - Required memberships (e.g., Amazon Prime, Flipkart VIP).
3. **Card & Bank Context:** The Indian market relies heavily on bank tie-ups. Highlight prominent, universally applicable bank/card offers (e.g., "10% instant discount via HDFC Credit Card"), but keep your base "True Cost" calculation independent of these conditional offers.
4. **Vigilance on Seller Authenticity:** If a price on a third-party marketplace seems suspiciously low, warn the user to check seller ratings or "Assured/Fulfilled" badges to avoid counterfeits or scams.
**Output Structure**
Always deliver your final analysis in this exact format:
- **Search Target:** Brief confirmation of the exact product and specifications.
- **Price Matrix:** A Markdown table comparing: Retailer | Sticker Price (₹) | Est. True Cost (₹) | Seller Quality | Notes (Offers/Fees)
- **BargainHound's Verdict:** A clear, definitive recommendation based on the lowest True Cost from a reliable seller. Briefly mention if the user should buy now or wait for a known upcoming major sale (e.g., Diwali sales)."""
#MODEL CONFIG
MODEL_ID = "gemini-2.5-flash"
if "messages" not in st.session_state:
    st.session_state.messages = []

# 1. Save the Client to memory so it doesn't close between reruns!
if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=API_KEY)

if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = None

if "show_history" not in st.session_state:
    st.session_state.show_history = False


def get_chat_config(festival_mode: bool):
    if festival_mode:
        temp = 0.2
        instruction = PERSONA_INSTRUCTION + "\n\n" + "The user wants to wait for major sales. Do not just look at current prices. Predict and analyze historical price drops for this product category during upcoming major Indian festival sales (like Diwali or Big Billion Days) and advise if they should buy now or wait."
    else:
        temp = 0.6
        instruction = PERSONA_INSTRUCTION
    return types.GenerateContentConfig(
        system_instruction=instruction,
        temperature=temp
    )

# SIDEBAR FOR HISTORY
with st.sidebar:
    st.title("Bargain Hound")
    st.caption("Assistant Settings & History")
    
    festival_mode = st.toggle("Upcoming Festival Sale Mode", value=False)
    
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.current_conversation_id = None
        st.session_state.messages = []
        config = get_chat_config(festival_mode)
        st.session_state.chat_session = st.session_state.client.chats.create(
            model=MODEL_ID,
            config=config
        )
        st.rerun()
        
    st.markdown("---")
    
    # History button
    if st.button("📜 History", use_container_width=True):
        st.session_state.show_history = not st.session_state.show_history
        st.rerun()
        
    if st.session_state.show_history:
        st.subheader("Past Conversations")
        conversations = get_conversations()
        if not conversations:
            st.info("No past conversations.")
        else:
            for conv in conversations:
                col1, col2 = st.columns([5, 1])
                button_label = conv['title']
                if st.session_state.current_conversation_id == conv['id']:
                    button_label = f"👉 {button_label}"
                
                with col1:
                    if st.button(button_label, key=f"conv_{conv['id']}", use_container_width=True):
                        st.session_state.current_conversation_id = conv['id']
                        st.session_state.messages = get_messages(conv['id'])
                        
                        # Rebuild chat session history
                        history = []
                        for m in st.session_state.messages:
                            history.append({
                                "role": m["role"],
                                "parts": [{"text": m["content"]}]
                            })
                        
                        config = get_chat_config(festival_mode)
                        st.session_state.chat_session = st.session_state.client.chats.create(
                            model=MODEL_ID,
                            config=config,
                            history=history
                        )
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"del_{conv['id']}", use_container_width=True):
                        delete_conversation(conv['id'])
                        if st.session_state.current_conversation_id == conv['id']:
                            st.session_state.current_conversation_id = None
                            st.session_state.messages = []
                            config = get_chat_config(festival_mode)
                            st.session_state.chat_session = st.session_state.client.chats.create(
                                model=MODEL_ID,
                                config=config
                            )
                        st.rerun()

# Check if festival mode toggle has changed, and if so, update the chat session configuration
if "festival_mode_active" not in st.session_state:
    st.session_state.festival_mode_active = festival_mode

if st.session_state.festival_mode_active != festival_mode:
    st.session_state.festival_mode_active = festival_mode
    if "chat_session" in st.session_state:
        history = []
        for m in st.session_state.messages:
            history.append({
                "role": m["role"],
                "parts": [{"text": m["content"]}]
            })
        
        config = get_chat_config(festival_mode)
        st.session_state.chat_session = st.session_state.client.chats.create(
            model=MODEL_ID,
            config=config,
            history=history
        )

# 2. Use that saved client to create the chat session
if "chat_session" not in st.session_state:
    config = get_chat_config(festival_mode)
    st.session_state.chat_session = st.session_state.client.chats.create(
        model=MODEL_ID,
        config=config
    )
    st.session_state.messages = []
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
user_input = st.chat_input("Type message here...")
if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Save conversation and user message to database
    if st.session_state.current_conversation_id is None:
        title = user_input.strip()
        if len(title) > 30:
            title = title[:27] + "..."
        if not title:
            title = "New Chat"
        st.session_state.current_conversation_id = create_conversation(title)
        
    save_message(st.session_state.current_conversation_id, "user", user_input)
    
    with st.chat_message("model"):
        with st.spinner("Finding best deals..."): # type: ignore
            try:
                response = st.session_state.chat_session.send_message(user_input)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "model", "content": response.text})
                # Save model response to database
                save_message(st.session_state.current_conversation_id, "model", response.text)
            except Exception as e:
                st.error(f"API Error: {e}")