
import os
import io
import json
import base64
import sqlite3
from datetime import datetime
import tempfile

import streamlit as st
from PIL import Image

# ============================================================
# AgriBioVision AI — Final Competition UI
# ============================================================

st.set_page_config(
    page_title="AgriBioVision AI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------- THEME -----------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 10% 10%, rgba(52, 211, 153, 0.14), transparent 28%),
        radial-gradient(circle at 90% 5%, rgba(59, 130, 246, 0.12), transparent 30%),
        linear-gradient(135deg, #f7fff9 0%, #f3f8ff 48%, #fbf7ff 100%);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #063b2b 0%, #075c43 55%, #0a7656 100%);
}

[data-testid="stSidebar"] * {
    color: white !important;
}

.hero {
    padding: 30px 34px;
    border-radius: 28px;
    background: linear-gradient(135deg, #064e3b 0%, #087f5b 45%, #0ea5a4 100%);
    color: white;
    box-shadow: 0 18px 45px rgba(6, 78, 59, .20);
    margin-bottom: 24px;
}

.hero h1 {
    font-size: 42px;
    margin: 0;
    font-weight: 800;
    letter-spacing: -1px;
}

.hero p {
    font-size: 17px;
    margin: 10px 0 0;
    opacity: .94;
    line-height: 1.6;
}

.badge {
    display: inline-block;
    padding: 7px 13px;
    border-radius: 999px;
    background: rgba(255,255,255,.18);
    border: 1px solid rgba(255,255,255,.25);
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 13px;
}

.card {
    background: rgba(255,255,255,.90);
    border: 1px solid rgba(16,185,129,.14);
    border-radius: 22px;
    padding: 22px;
    box-shadow: 0 10px 30px rgba(15,23,42,.07);
    margin-bottom: 18px;
}

.feature-card {
    min-height: 175px;
    transition: .2s ease;
}

.feature-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 15px 35px rgba(15,23,42,.10);
}

.feature-icon {
    font-size: 32px;
}

.feature-title {
    font-size: 18px;
    font-weight: 800;
    margin: 8px 0;
    color: #064e3b;
}

.feature-text {
    color: #475569;
    line-height: 1.55;
    font-size: 14px;
}

.section-title {
    color: #064e3b;
    font-size: 26px;
    font-weight: 800;
    margin: 12px 0 18px;
}

.metric-card {
    text-align: center;
    background: white;
    border-radius: 18px;
    padding: 18px 10px;
    box-shadow: 0 8px 25px rgba(15,23,42,.06);
    border: 1px solid #e2e8f0;
}

.metric-number {
    font-size: 27px;
    font-weight: 800;
    color: #087f5b;
}

.metric-label {
    color: #64748b;
    font-size: 13px;
}

.result-box {
    background: linear-gradient(135deg, #ecfdf5, #effcf6);
    border-left: 5px solid #10b981;
    border-radius: 16px;
    padding: 18px;
    margin: 12px 0;
}

.warning-box {
    background: #fff7ed;
    border-left: 5px solid #f59e0b;
    border-radius: 16px;
    padding: 17px;
}

.footer {
    text-align: center;
    padding: 25px;
    color: #64748b;
    font-size: 12px;
}

div.stButton > button {
    border-radius: 13px;
    font-weight: 700;
    border: 1px solid #10b981;
    min-height: 44px;
}

div.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #047857, #0d9488);
    color: white;
}

.stTextInput input, .stTextArea textarea {
    border-radius: 12px !important;
}

[data-testid="stFileUploader"] {
    border-radius: 16px;
}

</style>
""", unsafe_allow_html=True)

# ---------------------- GEMINI SETUP --------------------------

try:
    from google import genai

    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

    if not GEMINI_API_KEY:
        try:
            from google.colab import userdata
            GEMINI_API_KEY = userdata.get("GEMINI_API_KEY")
        except Exception:
            pass

    if GEMINI_API_KEY:
        client = genai.Client(api_key=GEMINI_API_KEY)
    else:
        client = None

except Exception:
    client = None
    GEMINI_API_KEY = ""

MODEL_NAME = "gemini-3.6-flash"

# ------------------------- DATABASE ---------------------------

DB_NAME = "agribiovision_history.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS case_history (
            case_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            case_type TEXT,
            category TEXT,
            common_name TEXT,
            scientific_name TEXT,
            user_question TEXT,
            symptoms TEXT,
            ai_assessment TEXT,
            confidence TEXT,
            image_name TEXT,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def save_case(
    case_type,
    category="",
    common_name="",
    scientific_name="",
    user_question="",
    symptoms="",
    ai_assessment="",
    confidence="",
    image_name="",
    notes=""
):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO case_history
        (created_at, case_type, category, common_name, scientific_name,
         user_question, symptoms, ai_assessment, confidence, image_name, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(timespec="seconds"),
        case_type,
        category,
        common_name,
        scientific_name,
        user_question,
        symptoms,
        ai_assessment,
        confidence,
        image_name,
        notes
    ))
    conn.commit()
    conn.close()

def load_cases():
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute("""
        SELECT case_id, created_at, case_type, category,
               common_name, scientific_name, confidence, image_name
        FROM case_history
        ORDER BY case_id DESC
    """).fetchall()
    conn.close()
    return rows

# ------------------------- HELPERS ----------------------------

def image_bytes(uploaded):
    img = Image.open(uploaded).convert("RGB")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=92)
    return buffer.getvalue()

def extract_json(text):
    if not text:
        return None

    text = str(text).strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    if "```" in text:
        text = text.replace("```json", "").replace("```JSON", "").replace("```", "").strip()
        try:
            return json.loads(text)
        except Exception:
            pass

    start = text.find("{")
    end = text.rfind("}")

    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            pass

    return None

def gemini_call(parts):
    if client is None:
        return None, "Gemini API is not configured."

    try:
        interaction = client.interactions.create(
            model=MODEL_NAME,
            input=parts
        )
        return interaction.output_text.strip(), None
    except Exception as e:
        return None, str(e)

# --------------------- IDENTIFICATION ------------------------

INFORMATION_TEMPLATES = {
    "plant": [
        "common_name", "scientific_name", "family", "genus",
        "description", "characteristics", "habitat", "climate",
        "soil_requirements", "water_requirements",
        "sunlight_requirements", "cultivation", "uses",
        "common_pests", "common_diseases", "prevention"
    ],
    "animal": [
        "common_name", "scientific_name", "family", "genus",
        "description", "characteristics", "habitat", "diet",
        "behaviour", "importance", "care_requirements",
        "common_health_problems", "prevention"
    ],
    "fish": [
        "common_name", "scientific_name", "family", "genus",
        "description", "characteristics", "habitat", "diet",
        "water_requirements", "breeding", "importance",
        "common_problems", "management"
    ],
    "bird": [
        "common_name", "scientific_name", "family", "genus",
        "description", "characteristics", "habitat", "diet",
        "behaviour", "importance", "breeding", "conservation"
    ],
    "insect": [
        "common_name", "scientific_name", "family", "genus",
        "description", "characteristics", "habitat", "diet",
        "life_cycle", "agricultural_importance",
        "beneficial_or_harmful", "crops_affected", "management"
    ]
}

def identify_image(img_bytes, language="English"):
    schema = INFORMATION_TEMPLATES

    prompt = f"""
You are AgriBioVision AI, a multimodal agriculture and animal-husbandry
intelligence assistant.

Analyze the supplied image.

Identify whether the main subject is:
plant, animal, fish, bird, or insect.

Return ONLY valid JSON.

Use this structure:

{{
  "category": "plant|animal|fish|bird|insect|uncertain",
  "common_name": "",
  "scientific_name": "",
  "family": "",
  "genus": "",
  "confidence": "High|Medium|Low",
  "information": {{}},
  "visual_evidence": [],
  "uncertainty_factors": []
}}

Populate information according to the appropriate predefined template.

Language for explanatory fields: {language}

Important:
- Do not invent visible evidence.
- If identification is uncertain, say so.
- Scientific names should remain standard Latin names.
- This is AI-assisted identification, not definitive expert identification.
"""

    b64 = base64.b64encode(img_bytes).decode()
    raw, error = gemini_call([
        {"type": "image", "mime_type": "image/jpeg", "data": b64},
        {"type": "text", "text": prompt}
    ])

    if error:
        return {"error": error}

    result = extract_json(raw)

    if not result:
        return {"error": "The AI response could not be parsed.", "raw": raw}

    return result

# ---------------------- DISEASE MODULE -----------------------

def disease_analysis(img_bytes, symptoms, context, language="English"):
    prompt = f"""
You are AgriBioVision AI's plant-health intelligence module.

Analyze the plant image together with the user-provided symptoms and context.

Return ONLY valid JSON:

{{
  "category": "plant",
  "organism": "",
  "possible_problem": "",
  "problem_type": "disease|pest|nutrient_deficiency|environmental_stress|water_stress|fungal_problem|bacterial_problem|viral_problem|insect_damage|other_plant_health_problem|uncertain",
  "confidence": "High|Medium|Low",
  "severity": "Low|Moderate|High|Uncertain",
  "observed_evidence": [],
  "possible_causes": [],
  "natural_organic_solutions": [],
  "chemical_solutions": [],
  "prevention_management": [],
  "safety_expert_referral": ""
}}

Rules:
- Plant-health assessment only.
- Do not claim definitive diagnosis.
- Use visible evidence and supplied symptoms.
- Do not invent symptoms.
- Separate natural/organic and chemical solutions.
- Do not give dangerous pesticide mixing instructions.
- Follow product labels and local regulations.
- Recommend expert review for uncertain or severe cases.
- Response language: {language}

User symptoms:
{symptoms}

User context:
{context}
"""

    b64 = base64.b64encode(img_bytes).decode()

    raw, error = gemini_call([
        {"type": "image", "mime_type": "image/jpeg", "data": b64},
        {"type": "text", "text": prompt}
    ])

    if error:
        return {"error": error}

    result = extract_json(raw)

    if not result:
        return {"error": "The disease response could not be parsed.", "raw": raw}

    return result

# -------------------- EXPLAINABLE AI -------------------------

def explain_result(img_bytes, identification, language="English"):
    prompt = f"""
You are the Explainable AI module of AgriBioVision AI.

Given the image and the preliminary identification below, provide
a concise, user-understandable explanation.

Return ONLY valid JSON:

{{
  "visual_evidence": [],
  "reasoning_factors": [],
  "confidence_explanation": "",
  "alternative_possibilities": [],
  "uncertainty_factors": [],
  "decision_support": "",
  "expert_review_recommended": false,
  "limitations": [],
  "source_awareness": []
}}

Do not expose hidden chain-of-thought.
Only provide observable evidence and concise reasoning factors.

Language: {language}

Preliminary identification:
{json.dumps(identification, ensure_ascii=False)}
"""

    b64 = base64.b64encode(img_bytes).decode()

    raw, error = gemini_call([
        {"type": "image", "mime_type": "image/jpeg", "data": b64},
        {"type": "text", "text": prompt}
    ])

    if error:
        return {"error": error}

    result = extract_json(raw)

    if not result:
        return {"error": "Explainable AI response could not be parsed.", "raw": raw}

    return result


# ----------------------- VOICE ASSISTANT -----------------------

def speech_to_text(audio_bytes):
    """Convert browser-recorded speech to text using SpeechRecognition."""
    try:
        import speech_recognition as sr

        recognizer = sr.Recognizer()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            audio_path = tmp.name

        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)

        try:
            os.unlink(audio_path)
        except Exception:
            pass

        # Google Speech Recognition performs automatic language recognition
        # poorly for some multilingual recordings, so we try broad defaults.
        # The user can simply speak naturally; the AI receives the transcript.
        text = recognizer.recognize_google(audio_data)

        return text.strip()

    except ImportError:
        return "Could not process speech because SpeechRecognition is not installed."
    except Exception as e:
        return f"Could not understand the audio: {str(e)}"


def text_to_speech(text, language="en"):
    """Generate a playable MP3 response using gTTS."""
    try:
        from gtts import gTTS

        # gTTS needs a valid language code. For automatic/mixed-language
        # answers, English is the safe fallback.
        supported = {
            "english": "en",
            "hindi": "hi",
            "marathi": "mr",
            "french": "fr",
            "german": "de",
            "italian": "it",
            "spanish": "es",
        }

        lang = supported.get(str(language).lower(), "en")

        audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        audio_file.close()

        tts = gTTS(text=text, lang=lang)
        tts.save(audio_file.name)

        return audio_file.name

    except Exception as e:
        print("Text-to-speech error:", e)
        return None


def voice_pipeline(audio_bytes, response_language="Auto"):
    """
    Complete voice pipeline:

    Speech
      ↓
    Speech-to-Text
      ↓
    AgriBioVision AI
      ↓
    AI Response
      ↓
    Text-to-Speech
    """
    if not audio_bytes:
        return {
            "success": False,
            "error": "No audio was provided."
        }

    question = speech_to_text(audio_bytes)

    if not question or question.startswith("Could not"):
        return {
            "success": False,
            "error": question or "Speech could not be converted to text."
        }

    answer = ask_agribiovision(question)

    if not answer:
        return {
            "success": False,
            "error": "AgriBioVision AI returned an empty response.",
            "question": question
        }

    # For Auto, use English audio as a reliable fallback.
    # The text response itself remains in the user's language.
    tts_language = "en" if response_language == "Auto" else response_language
    audio_path = text_to_speech(answer, tts_language)

    return {
        "success": True,
        "question": question,
        "answer": answer,
        "audio_path": audio_path
    }

# ----------------------- ASK ENGINE --------------------------

def ask_agribiovision(question, language_hint="Auto"):
    prompt = f"""
You are AgriBioVision AI, an expert agricultural and animal-husbandry
knowledge assistant.

Answer the user's question clearly and practically.

Important:
- Understand the user's language automatically.
- Respond in the same language as the user's question unless they explicitly
  request another language.
- Support multilingual and mixed-language questions.
- Focus on agriculture, plants, animals, fish, birds, insects,
  cultivation, plant health, pests, diseases, management and related topics.
- Do not pretend to have certainty when information is uncertain.
- For plant-health questions, do not claim definitive diagnosis.
- For chemical treatment, advise following the product label and local rules.

Question:
{question}
"""

    raw, error = gemini_call(prompt)

    if error:
        return f"⚠️ AI assistant error: {error}"

    return raw

# ------------------------- HEADER ----------------------------

st.markdown("""
<div class="hero">
    <div class="badge">MULTIMODAL AI • AGRICULTURE • ANIMAL HUSBANDRY</div>
    <h1>🌿 AgriBioVision AI</h1>
    <p>
        AI-powered biological identification, plant-health intelligence,
        explainable analysis and agricultural decision support.
    </p>
</div>
""", unsafe_allow_html=True)

# ------------------------- SIDEBAR ---------------------------

st.sidebar.markdown("## 🌿 AgriBioVision AI")
st.sidebar.caption("Intelligent Agriculture & Biological Vision")

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Home",
        "🔎 Identify & Information",
        "🩺 Disease & Pest Intelligence",
        "🧠 Explainable AI",
        "💬 Ask AgriBioVision",
        "🎤 Voice Assistant",
        "📂 Case History",
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ AI Status")

if client:
    st.sidebar.success("Gemini AI Connected")
else:
    st.sidebar.error("Gemini API Not Connected")

st.sidebar.caption(f"Model: {MODEL_NAME}")

# -------------------------- HOME -----------------------------

if page == "🏠 Home":

    st.markdown('<div class="section-title">🌱 What can AgriBioVision AI do?</div>', unsafe_allow_html=True)

    cols = st.columns(3)

    cards = [
        ("🔎", "Multimodal Identification",
         "Identify plants, animals, fish, birds and insects from images with structured information."),
        ("🩺", "Plant Health Intelligence",
         "Analyze possible plant-health problems, evidence, severity and management options."),
        ("🧠", "Explainable AI",
         "Understand visual evidence, confidence, alternatives, uncertainty and decision support."),
        ("💬", "AI Agriculture Assistant",
         "Ask questions naturally in different languages and receive contextual answers."),
        ("🌿", "Natural + Chemical Solutions",
         "Keep organic/natural and chemical management recommendations clearly separated."),
        ("📂", "Case History",
         "Save important analyses for future reference and decision support.")
    ]

    for i, (icon, title, text) in enumerate(cards):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="card feature-card">
                <div class="feature-icon">{icon}</div>
                <div class="feature-title">{title}</div>
                <div class="feature-text">{text}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">🚀 Built for real-world agricultural intelligence</div>', unsafe_allow_html=True)

    m = st.columns(5)
    metrics = [
        ("5", "Biological Categories"),
        ("AI", "Vision Intelligence"),
        ("🌍", "Multilingual"),
        ("🧠", "Explainable"),
        ("📂", "Case Memory"),
    ]

    for col, (num, label) in zip(m, metrics):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-number">{num}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("")
    st.info(
        "💡 Competition positioning: AgriBioVision AI is not only an image "
        "classifier. It combines multimodal identification, structured "
        "knowledge, plant-health intelligence, explainability and decision support."
    )

# -------------------- IDENTIFICATION PAGE --------------------

elif page == "🔎 Identify & Information":

    st.markdown('<div class="section-title">🔎 Identify & Information</div>', unsafe_allow_html=True)

    language = st.text_input(
        "🌍 Output language",
        value="English",
        placeholder="Type any language, e.g. Marathi, Hindi, French, German..."
    )

    uploaded = st.file_uploader(
        "📷 Upload a plant, animal, fish, bird or insect image",
        type=["jpg", "jpeg", "png", "webp"],
        key="identify_upload"
    )

    if uploaded:
        img_bytes = image_bytes(uploaded)

        c1, c2 = st.columns([1, 1.25])

        with c1:
            st.image(img_bytes, caption="Uploaded Image", use_container_width=True)

        with c2:
            if st.button("🔬 Analyze Image", type="primary", use_container_width=True):
                with st.spinner("AgriBioVision AI is analyzing the image..."):
                    result = identify_image(img_bytes, language)

                if result.get("error"):
                    st.error(result["error"])
                else:
                    st.session_state["last_identification"] = result
                    st.session_state["last_identification_image"] = img_bytes

            result = st.session_state.get("last_identification")

            if result:
                category = result.get("category", "uncertain")
                name = result.get("common_name", "Unknown")
                scientific = result.get("scientific_name", "Not available")
                confidence = result.get("confidence", "Unknown")

                st.markdown(f"""
                <div class="result-box">
                    <h3>🌿 {name}</h3>
                    <b>Scientific name:</b> <i>{scientific}</i><br>
                    <b>Category:</b> {category.title()}<br>
                    <b>Confidence:</b> {confidence}
                </div>
                """, unsafe_allow_html=True)

                info = result.get("information", {})

                for key, value in info.items():
                    if value in [None, "", [], {}]:
                        continue
                    title = key.replace("_", " ").title()
                    if isinstance(value, list):
                        value = "<br>".join([f"• {x}" for x in value])
                    else:
                        value = str(value)
                    st.markdown(f"**{title}**  \n{value}")

                evidence = result.get("visual_evidence", [])
                if evidence:
                    with st.expander("👁️ Visual Evidence"):
                        for x in evidence:
                            st.write("•", x)

                uncertainty = result.get("uncertainty_factors", [])
                if uncertainty:
                    with st.expander("⚠️ Uncertainty"):
                        for x in uncertainty:
                            st.write("•", x)

                if st.button("💾 Save Identification Case"):
                    save_case(
                        case_type="identification",
                        category=category,
                        common_name=name,
                        scientific_name=scientific,
                        ai_assessment=json.dumps(result, ensure_ascii=False),
                        confidence=confidence,
                        image_name=uploaded.name
                    )
                    st.success("✅ Case saved successfully.")

# ---------------------- DISEASE PAGE -------------------------

elif page == "🩺 Disease & Pest Intelligence":

    st.markdown('<div class="section-title">🩺 Plant Disease & Pest Intelligence</div>', unsafe_allow_html=True)

    st.warning(
        "⚠️ This module provides AI-assisted plant-health assessment, not a definitive expert diagnosis."
    )

    language = st.text_input(
        "🌍 Response language",
        value="English",
        key="disease_language"
    )

    uploaded = st.file_uploader(
        "📷 Upload an affected plant image",
        type=["jpg", "jpeg", "png", "webp"],
        key="disease_upload"
    )

    symptoms = st.text_area(
        "📝 Describe symptoms",
        placeholder="Example: yellow leaves, brown spots, curling, insects visible..."
    )

    context = st.text_area(
        "🌾 Additional context",
        placeholder="Crop, growth stage, weather, irrigation, soil or other useful information..."
    )

    if uploaded:
        img_bytes = image_bytes(uploaded)
        st.image(img_bytes, caption="Affected Plant", width=500)

        if st.button("🧪 Run Plant Health Analysis", type="primary"):
            with st.spinner("Analyzing plant health..."):
                result = disease_analysis(img_bytes, symptoms, context, language)

            if result.get("error"):
                st.error(result["error"])
            else:
                st.session_state["disease_result"] = result
                st.session_state["disease_image"] = img_bytes

        result = st.session_state.get("disease_result")

        if result:
            st.markdown(f"""
            <div class="result-box">
                <h3>🌿 {result.get("organism", "Unknown plant")}</h3>
                <b>Possible problem:</b> {result.get("possible_problem", "Uncertain")}<br>
                <b>Confidence:</b> {result.get("confidence", "Unknown")}<br>
                <b>Severity:</b> {result.get("severity", "Uncertain")}
            </div>
            """, unsafe_allow_html=True)

            sections = [
                ("👁️ Observed Evidence", "observed_evidence"),
                ("🔬 Possible Causes", "possible_causes"),
                ("🌿 Natural / Organic Solutions", "natural_organic_solutions"),
                ("🧪 Chemical Solutions", "chemical_solutions"),
                ("🛡️ Prevention & Management", "prevention_management"),
            ]

            for title, key in sections:
                with st.expander(title, expanded=True):
                    items = result.get(key, [])
                    if isinstance(items, list):
                        for item in items:
                            st.write("•", item)
                    elif items:
                        st.write(items)
                    else:
                        st.info("No information returned.")

            st.markdown(f"""
            <div class="warning-box">
                <b>🧑‍🌾 Safety & Expert Referral</b><br>
                {result.get("safety_expert_referral", "Verify important treatment decisions with an agricultural expert and follow product labels/local regulations.")}
            </div>
            """, unsafe_allow_html=True)

            if st.button("💾 Save Disease Case"):
                save_case(
                    case_type="disease",
                    category="plant",
                    common_name=result.get("organism", ""),
                    ai_assessment=json.dumps(result, ensure_ascii=False),
                    confidence=result.get("confidence", ""),
                    image_name=uploaded.name,
                    symptoms=symptoms,
                    notes=context
                )
                st.success("✅ Disease case saved.")

# -------------------- EXPLAINABLE AI PAGE --------------------

elif page == "🧠 Explainable AI":

    st.markdown('<div class="section-title">🧠 Explainable AI</div>', unsafe_allow_html=True)

    st.caption(
        "Understand observable evidence, confidence, uncertainty and decision-support factors."
    )

    language = st.text_input(
        "🌍 Explanation language",
        value="English",
        key="xai_language"
    )

    uploaded = st.file_uploader(
        "📷 Upload image",
        type=["jpg", "jpeg", "png", "webp"],
        key="xai_upload"
    )

    identification = st.session_state.get("last_identification")

    if uploaded:
        img_bytes = image_bytes(uploaded)
        st.image(img_bytes, caption="Image for Explainable AI", width=500)

        if not identification:
            st.info("ℹ️ For the strongest explanation, first run identification in the Identify & Information page.")

        if st.button("🧠 Run Explainable AI", type="primary"):
            with st.spinner("Generating evidence-based explanation..."):
                result = explain_result(
                    img_bytes,
                    identification or {},
                    language
                )

            if result.get("error"):
                st.error(result["error"])
            else:
                st.session_state["xai_result"] = result

        result = st.session_state.get("xai_result")

        if result:
            with st.expander("👁️ Visual Evidence", expanded=True):
                for x in result.get("visual_evidence", []):
                    st.write("•", x)

            with st.expander("🧠 Reasoning Factors", expanded=True):
                for x in result.get("reasoning_factors", []):
                    st.write("•", x)

            st.markdown("### 📊 Confidence Explanation")
            st.info(result.get("confidence_explanation", "Not available."))

            with st.expander("🔎 Alternative Possibilities"):
                alternatives = result.get("alternative_possibilities", [])
                if alternatives:
                    for x in alternatives:
                        st.write("•", x)
                else:
                    st.success("No significant alternatives identified.")

            with st.expander("⚠️ Uncertainty Factors"):
                uncertainty = result.get("uncertainty_factors", [])
                if uncertainty:
                    for x in uncertainty:
                        st.write("•", x)
                else:
                    st.success("No major uncertainty factors identified.")

            st.markdown("### 🎯 Decision Support")
            st.info(result.get("decision_support", "Not available."))

            if result.get("expert_review_recommended", False):
                st.warning("🧑‍🌾 Expert review is recommended.")
            else:
                st.success("✅ No immediate expert-review trigger was returned.")

            with st.expander("📋 Limitations"):
                for x in result.get("limitations", []):
                    st.write("•", x)

            with st.expander("📚 Source Awareness"):
                for x in result.get("source_awareness", []):
                    st.write("•", x)

# ----------------------- ASK PAGE ----------------------------

elif page == "💬 Ask AgriBioVision":

    st.markdown('<div class="section-title">💬 Ask AgriBioVision AI</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <b>Ask naturally in your own language.</b><br>
        You do not need to manually select a language. The AI can understand
        multilingual and mixed-language questions and respond accordingly.
    </div>
    """, unsafe_allow_html=True)

    question = st.text_area(
        "💬 Your question",
        height=140,
        placeholder="Ask anything about crops, plants, pests, diseases, animals, fish, birds, insects, soil, cultivation..."
    )

    if st.button("🚀 Ask AgriBioVision AI", type="primary", use_container_width=True):
        if not question.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Thinking..."):
                answer = ask_agribiovision(question)

            st.markdown("### 🤖 AI Response")
            st.markdown(f'<div class="result-box">{answer}</div>', unsafe_allow_html=True)


# ---------------------- VOICE ASSISTANT PAGE -------------------

elif page == "🎤 Voice Assistant":

    st.markdown(
        '<div class="section-title">🎤 AgriBioVision Voice Assistant</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class="card">
        <b>Speak naturally to AgriBioVision AI.</b><br>
        Record your question → Speech-to-Text → AI answer → Voice response.
        You can ask about crops, plants, diseases, pests, animals, fish,
        birds, insects, soil and agricultural management.
    </div>
    """, unsafe_allow_html=True)

    st.info(
        "🎙️ Speak clearly and keep the browser microphone permission enabled. "
        "Your spoken question is converted to text before being sent to the AI."
    )

    response_language = st.text_input(
        "🔊 Voice response language",
        value="Auto",
        placeholder="Auto, English, Hindi, Marathi, French, German, Italian..."
    )

    audio_input = st.audio_input(
        "🎙️ Record your question",
        key="voice_recorder"
    )

    if audio_input:
        audio_bytes = audio_input.getvalue()

        st.audio(audio_bytes, format="audio/wav")

        if st.button(
            "🚀 Ask AgriBioVision with Voice",
            type="primary",
            use_container_width=True
        ):
            with st.spinner("🎤 Processing your voice..."):
                result = voice_pipeline(
                    audio_bytes,
                    response_language=response_language.strip() or "Auto"
                )

            if not result.get("success"):
                st.error(result.get("error", "Voice processing failed."))
            else:
                st.session_state["voice_result"] = result

    voice_result = st.session_state.get("voice_result")

    if voice_result:
        st.markdown("### 📝 You said")
        st.markdown(
            f'<div class="result-box">{voice_result.get("question", "")}</div>',
            unsafe_allow_html=True
        )

        st.markdown("### 🤖 AgriBioVision AI Response")
        st.markdown(
            f'<div class="result-box">{voice_result.get("answer", "")}</div>',
            unsafe_allow_html=True
        )

        audio_path = voice_result.get("audio_path")

        if audio_path and os.path.exists(audio_path):
            st.markdown("### 🔊 Voice Response")
            with open(audio_path, "rb") as audio_file:
                st.audio(audio_file.read(), format="audio/mp3")
        else:
            st.warning(
                "Text response was generated, but voice playback could not be created."
            )

# --------------------- CASE HISTORY PAGE ---------------------

elif page == "📂 Case History":

    st.markdown('<div class="section-title">📂 Case History</div>', unsafe_allow_html=True)

    rows = load_cases()

    if not rows:
        st.info("No cases have been saved yet.")
    else:
        st.success(f"✅ {len(rows)} case(s) stored.")

        for row in rows:
            case_id, created, case_type, category, common, scientific, confidence, image_name = row

            with st.expander(
                f"#{case_id} • {case_type.title()} • {common or 'Unknown'} • {created}"
            ):
                st.write("**Category:**", category)
                st.write("**Scientific name:**", scientific or "—")
                st.write("**Confidence:**", confidence or "—")
                st.write("**Image:**", image_name or "—")
                st.write("**Created:**", created)

# -------------------------- FOOTER ---------------------------

st.markdown("""
<div class="footer">
    🌿 <b>AgriBioVision AI</b> · Multimodal Agriculture & Biological Intelligence<br>
    AI-assisted information and decision support. Verify important agricultural
    and treatment decisions with appropriate experts and trusted sources.
</div>
""", unsafe_allow_html=True)
