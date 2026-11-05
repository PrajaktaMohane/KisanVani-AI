import os
import io
import time
import base64
import datetime
import requests
import streamlit as st

# Page Configuration - Centered Mobile-First Layout
st.set_page_config(
    page_title="KisanVani — Voice Agricultural Assistant",
    page_icon="🌾",
    layout="centered",
    initial_sidebar_state="collapsed"
)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Initialize Session States
if "theme" not in st.session_state:
    st.session_state.theme = "light"  # "light" or "dark"

if "selected_language" not in st.session_state:
    st.session_state.selected_language = "mr"  # Default: Marathi

if "chat_history" not in st.session_state:
    greetings = {
        "mr": "नमस्कार! 🌾\nतुमचा शेतीविषयक प्रश्न आवाजेत विचारा.",
        "hi": "नमस्कार! 🌾\nअपना कृषि संबंधी प्रश्न आवाज़ में पूछें।",
        "en": "Namaskar! 🌾\nAsk your farming question using voice."
    }
    st.session_state.chat_history = [
        {
            "role": "bot",
            "text": greetings["mr"],
            "audio_bytes": None,
            "sources": [],
            "time": datetime.datetime.now().strftime("%I:%M %p")
        }
    ]

# Theme Definitions & Custom WhatsApp CSS
is_dark = (st.session_state.theme == "dark")

# Color Palettes
bg_app = "#0b141a" if is_dark else "#efeae2"
bg_header = "#1f2c34" if is_dark else "#075e54"
header_text = "#e9edef" if is_dark else "#ffffff"
farmer_bubble_bg = "#005c4b" if is_dark else "#dcf8c6"
farmer_bubble_text = "#e9edef" if is_dark else "#111b21"
bot_bubble_bg = "#202c33" if is_dark else "#ffffff"
bot_bubble_text = "#e9edef" if is_dark else "#111b21"
bot_accent_border = "#00a884" if is_dark else "#075e54"
time_color = "#8696a0" if is_dark else "#667781"
source_box_bg = "#111b21" if is_dark else "#f0f2f5"
source_box_border = "#2a3942" if is_dark else "#e1e9eb"
source_text = "#8696a0" if is_dark else "#54656f"
lang_bar_bg = "#1f2c34" if is_dark else "#ffffff"
lang_bar_text = "#e9edef" if is_dark else "#111b21"

st.markdown(f"""
<style>
    /* Hide Default Streamlit Clutter */
    #MainMenu, header, footer, .stDeployButton {{
        visibility: hidden;
        display: none;
    }}
    
    /* WhatsApp Background Color */
    .stApp {{
        background-color: {bg_app};
        color: {bot_bubble_text};
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}

    /* Centered Mobile Container */
    .block-container {{
        padding-top: 0.5rem;
        padding-bottom: 2rem;
        max-width: 580px;
    }}

    /* WhatsApp Top Bar Header */
    .wa-top-bar {{
        background-color: {bg_header};
        color: {header_text};
        padding: 10px 14px;
        border-radius: 12px 12px 6px 6px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 1px 3px rgba(0,0,0,0.25);
        margin-bottom: 8px;
    }}
    .wa-top-left {{
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    .wa-avatar {{
        width: 38px;
        height: 38px;
        background-color: #128c7e;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        border: 2px solid #25d366;
    }}
    .wa-title {{
        font-size: 15px;
        font-weight: 700;
        margin: 0;
        color: {header_text};
        line-height: 1.2;
    }}
    .wa-status {{
        font-size: 11px;
        color: #25d366;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 4px;
        font-weight: 500;
    }}
    .wa-status-dot {{
        width: 7px;
        height: 7px;
        background-color: #25d366;
        border-radius: 50%;
        display: inline-block;
    }}

    /* Message Bubbles */
    .bubble-farmer {{
        background-color: {farmer_bubble_bg};
        color: {farmer_bubble_text};
        padding: 10px 14px;
        border-radius: 14px 14px 2px 14px;
        margin: 8px 0 8px auto;
        max-width: 82%;
        box-shadow: 0 1px 2px rgba(0,0,0,0.15);
        font-size: 14px;
        line-height: 1.45;
        word-wrap: break-word;
    }}
    .bubble-kisan {{
        background-color: {bot_bubble_bg};
        color: {bot_bubble_text};
        padding: 12px 15px;
        border-radius: 14px 14px 14px 2px;
        margin: 8px auto 8px 0;
        max-width: 85%;
        box-shadow: 0 1px 2px rgba(0,0,0,0.14);
        font-size: 14px;
        line-height: 1.5;
        border-left: 4px solid {bot_accent_border};
        word-wrap: break-word;
    }}
    .bubble-sender {{
        font-size: 11px;
        font-weight: 700;
        color: {bot_accent_border};
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 4px;
    }}
    .bubble-time {{
        font-size: 10px;
        color: {time_color};
        text-align: right;
        margin-top: 4px;
    }}
    .voice-tag {{
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 11px;
        font-weight: 600;
        margin-bottom: 4px;
        color: {bot_accent_border};
    }}
    .voice-tag-farmer {{
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 11px;
        font-weight: 600;
        margin-bottom: 4px;
        color: {farmer_bubble_text};
        opacity: 0.9;
    }}

    /* Streamlit Audio Player styling */
    audio {{
        width: 100% !important;
        height: 38px !important;
        border-radius: 20px !important;
        margin-top: 4px !important;
    }}

    /* Streamlit Chat Input styling */
    .stChatInputContainer {{
        background-color: transparent !important;
    }}
</style>
""", unsafe_allow_html=True)

# 1. Top Header with Status & Controls
col_hdr1, col_hdr2 = st.columns([0.72, 0.28])

with col_hdr1:
    st.markdown("""
    <div class="wa-top-bar">
        <div class="wa-top-left">
            <div class="wa-avatar">🌾</div>
            <div>
                <div class="wa-title">🌾 KisanVani</div>
                <div class="wa-status"><span class="wa-status-dot"></span> Online</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_hdr2:
    # Theme Toggle & Language Quick Controls
    theme_btn_label = "☀ Light" if is_dark else "🌙 Dark"
    if st.button(theme_btn_label, key="theme_toggle", use_container_width=True):
        st.session_state.theme = "light" if is_dark else "dark"
        st.rerun()

# 2. Compact Language Selector (Dropdown / Pills)
lang_map = {
    "मराठी": "mr",
    "हिन्दी": "hi",
    "English": "en"
}
lang_keys = list(lang_map.keys())
current_idx = lang_keys.index(
    next((k for k, v in lang_map.items() if v == st.session_state.selected_language), "मराठी")
)

selected_lang_name = st.radio(
    "Language",
    options=lang_keys,
    index=current_idx,
    horizontal=True,
    label_visibility="collapsed"
)
new_lang_code = lang_map[selected_lang_name]

# If language changed, update welcome message if only greeting is present
if new_lang_code != st.session_state.selected_language:
    st.session_state.selected_language = new_lang_code
    greetings = {
        "mr": "नमस्कार! 🌾\nतुमचा शेतीविषयक प्रश्न आवाजेत विचारा.",
        "hi": "नमस्कार! 🌾\nअपना कृषि संबंधी प्रश्न आवाज़ में पूछें।",
        "en": "Namaskar! 🌾\nAsk your farming question using voice."
    }
    if len(st.session_state.chat_history) == 1:
        st.session_state.chat_history[0]["text"] = greetings[new_lang_code]
    st.rerun()

selected_lang = st.session_state.selected_language

# 3. Message Stream (Continuous WhatsApp Chat History)
for idx, msg in enumerate(st.session_state.chat_history):
    time_str = msg.get("time") or datetime.datetime.now().strftime("%I:%M %p")
    
    if msg["role"] == "farmer":
        st.markdown(f"""
        <div class="bubble-farmer">
            <div class="voice-tag-farmer">🎙️ You</div>
            <div>{msg['text']}</div>
            <div class="bubble-time">{time_str} ✓✓</div>
        </div>
        """, unsafe_allow_html=True)
        if msg.get("audio_bytes"):
            st.audio(msg["audio_bytes"], format="audio/wav")

    else:
        st.markdown(f"""
        <div class="bubble-kisan">
            <div class="bubble-sender">🌾 KisanVani</div>
            <div>{msg['text']}</div>
            <div class="bubble-time">{time_str}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Playable Voice Note
        if msg.get("audio_bytes"):
            st.markdown("<div style='font-size: 13px; font-weight: 600; color: #25d366; margin: 4px 0 2px 4px;'>🔊 Voice response</div>", unsafe_allow_html=True)
            st.audio(msg["audio_bytes"], format=msg.get("mime_type", "audio/mpeg"))

        # Clean Multi-Source Display (ICAR / KVK / KCC)
        if msg.get("sources"):
            src_list = msg["sources"]
            unique_src_names = list(dict.fromkeys([s.get("source", "Agricultural Advisory") for s in src_list]))
            src_title = f"ⓘ Source: {', '.join(unique_src_names)}" if len(unique_src_names) <= 2 else "ⓘ Sources: ICAR / KVK & Kisan Call Centre"

            with st.expander(src_title):
                for s_idx, src in enumerate(src_list):
                    src_name = src.get("source", "Agricultural Advisory")
                    crop_str = f" • Crop: {src.get('crop')}" if src.get('crop') and src.get('crop') != 'General' else ""
                    page_str = f" • Page {src.get('page_number')}" if src.get('page_number') else ""
                    doc_str = f" ({src.get('file_name')})" if src.get('file_name') and "pdf" in str(src.get('file_name')).lower() else ""

                    st.caption(f"**{src_name}{crop_str}{page_str}{doc_str}**")
                    if src.get("question") and not "Agricultural advisory on" in str(src.get("question")):
                        st.write(f"**Query:** {src.get('question', '')}")
                    st.write(f"**Advisory:** {src.get('answer', '')}")
                    if s_idx < len(src_list) - 1:
                        st.divider()

# 4. Primary Voice Input (Microphone Bar)
mic_label = {
    "mr": "🎤 आवाजेत प्रश्न विचारा (माईक दाबा):",
    "hi": "🎤 आवाज़ में प्रश्न पूछें (माइक दबाएं):",
    "en": "🎤 Ask question using voice (Press Mic):"
}
st.markdown(f"<div style='font-size: 12px; font-weight: 600; color: {bot_accent_border}; margin: 16px 0 6px 2px;'>{mic_label[selected_lang]}</div>", unsafe_allow_html=True)

# Try an Example Section (Test questions demo)
example_questions_map = {
    "mr": [
        "सोयाबीनची पेरणी कधी करावी?",
        "कापसावर गुलाबी बोंडअळी असल्यास काय करावे?",
        "गव्हासाठी कोणते खत वापरावे?",
        "तांदळाला पाणी कसे द्यावे?"
    ],
    "hi": [
        "सोयाबीन की बुवाई कब करनी चाहिए?",
        "कपास में गुलाबी सुंडी होने पर क्या करें?",
        "गेहूं में सिंचाई कितनी बार करनी चाहिए?",
        "धान में कीट नियंत्रण कैसे करें?"
    ],
    "en": [
        "When should soybean be sown?",
        "What should be done if pink bollworm is found in cotton?",
        "Which fertilizer should be used for wheat?",
        "How should rice be irrigated?"
    ]
}

example_header = {
    "mr": "💡 उदाहरण प्रश्न निवडा (Try an example)",
    "hi": "💡 उदाहरण प्रश्न चुनें (Try an example)",
    "en": "💡 Try an example question"
}

with st.expander(example_header[selected_lang], expanded=False):
    demo_cols = st.columns(2)
    for q_idx, eg_q in enumerate(example_questions_map[selected_lang]):
        target_col = demo_cols[q_idx % 2]
        if target_col.button(eg_q, key=f"demo_q_{selected_lang}_{q_idx}", use_container_width=True):
            current_time = datetime.datetime.now().strftime("%I:%M %p")
            st.session_state.chat_history.append({
                "role": "farmer",
                "text": eg_q,
                "audio_bytes": None,
                "time": current_time
            })
            with st.spinner("⏳ Retrieving verified agricultural advisory..."):
                try:
                    payload = {"question": eg_q, "language": selected_lang}
                    resp = requests.post(f"{BACKEND_URL}/ask", json=payload, timeout=30)
                    if resp.status_code == 200:
                        res_data = resp.json()
                        ans_text = res_data.get("answer", "")
                        aud_b64 = res_data.get("audio_base64")
                        srcs = res_data.get("sources", [])
                        audio_mime = res_data.get("audio_mime_type", "audio/mpeg")
                        bot_audio_bytes = base64.b64decode(aud_b64) if aud_b64 else None
                        st.session_state.chat_history.append({
                            "role": "bot",
                            "text": ans_text,
                            "audio_bytes": bot_audio_bytes,
                            "mime_type": audio_mime,
                            "sources": srcs,
                            "time": datetime.datetime.now().strftime("%I:%M %p")
                        })
                        st.rerun()
                except Exception as ex:
                    st.error(f"Error querying advisory: {ex}")

# Native Streamlit Audio Input
voice_buffer = st.audio_input("Record Voice Message", key="kisan_voice_input", label_visibility="collapsed")

if voice_buffer is not None:
    audio_raw_bytes = voice_buffer.getvalue()
    audio_hash = hash(audio_raw_bytes)

    if st.session_state.get("last_processed_audio_hash") != audio_hash:
        st.session_state["last_processed_audio_hash"] = audio_hash
        current_time = datetime.datetime.now().strftime("%I:%M %p")

        proc_msg = {
            "mr": "⏳ प्रक्रिया चालू आहे... (Processing voice & KCC knowledge base)...",
            "hi": "⏳ प्रक्रिया जारी है... (Processing voice & KCC knowledge base)...",
            "en": "⏳ Processing voice & retrieving KCC advisory..."
        }

        with st.spinner(proc_msg[selected_lang]):
            try:
                files = {"audio_file": ("farmer_query.wav", audio_raw_bytes, "audio/wav")}
                data = {"language": selected_lang}
                
                resp = requests.post(f"{BACKEND_URL}/voice", files=files, data=data, timeout=35)
                
                if resp.status_code == 200:
                    res_data = resp.json()
                    transcript = res_data.get("transcript", "Voice query")
                    answer_text = res_data.get("answer", "")
                    audio_b64 = res_data.get("audio_base64")
                    sources = res_data.get("sources", [])
                    audio_mime = res_data.get("audio_mime_type", "audio/mpeg")

                    bot_audio_bytes = base64.b64decode(audio_b64) if audio_b64 else None

                    if bot_audio_bytes:
                        audio_kb = round(len(bot_audio_bytes) / 1024, 2)
                        print(f"\nVOICE RESPONSE RECEIVED\nText: YES\nAudio: YES\nAudio size: {audio_kb:.2f} KB\nMIME: {audio_mime}\nPlaying audio...\n")
                    else:
                        print("\nVOICE RESPONSE RECEIVED\nText: YES\nAudio: NO\n")

                    # Append farmer message
                    st.session_state.chat_history.append({
                        "role": "farmer",
                        "text": transcript,
                        "audio_bytes": audio_raw_bytes,
                        "time": current_time
                    })

                    # Append bot response
                    st.session_state.chat_history.append({
                        "role": "bot",
                        "text": answer_text,
                        "audio_bytes": bot_audio_bytes,
                        "mime_type": audio_mime,
                        "sources": sources,
                        "time": datetime.datetime.now().strftime("%I:%M %p")
                    })

                    st.rerun()
                else:
                    st.error("Unable to connect. Please try again.")
            except Exception:
                st.error("Unable to connect. Please try again.")

# 5. Secondary Fallback Text Input
text_placeholder = {
    "mr": "किंवा संदेश टाईप करा...",
    "hi": "या संदेश टाइप करें...",
    "en": "Type a message..."
}
text_query = st.chat_input(text_placeholder.get(selected_lang, "Type a message..."))

if text_query:
    current_time = datetime.datetime.now().strftime("%I:%M %p")
    st.session_state.chat_history.append({
        "role": "farmer",
        "text": text_query,
        "audio_bytes": None,
        "time": current_time
    })

    with st.spinner("⏳ Analyzing..."):
        try:
            payload = {
                "question": text_query,
                "language": selected_lang
            }
            resp = requests.post(f"{BACKEND_URL}/ask", json=payload, timeout=30)
            if resp.status_code == 200:
                res_data = resp.json()
                answer_text = res_data.get("answer", "")
                audio_b64 = res_data.get("audio_base64")
                sources = res_data.get("sources", [])
                audio_mime = res_data.get("audio_mime_type", "audio/mpeg")

                bot_audio_bytes = base64.b64decode(audio_b64) if audio_b64 else None

                st.session_state.chat_history.append({
                    "role": "bot",
                    "text": answer_text,
                    "audio_bytes": bot_audio_bytes,
                    "mime_type": audio_mime,
                    "sources": sources,
                    "time": datetime.datetime.now().strftime("%I:%M %p")
                })
                st.rerun()
            else:
                st.error("Unable to connect. Please try again.")
        except Exception:
            st.error("Unable to connect. Please try again.")
