import base64
import io
import logging
import os

import streamlit as st
from openai import OpenAI
from PIL import Image, ImageFile

logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
MAX_DIMENSION = 2048

Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
ImageFile.LOAD_TRUNCATED_IMAGES = False

st.set_page_config(page_title="AgroPulse.ai - Custom AI Agronomist", layout="wide")

# UI Enhancements for crisp image rendering and high scannability
st.markdown("""
    <style>
    img { image-rendering: -webkit-optimize-contrast !important; border-radius: 12px; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; }
    </style>
""", unsafe_allow_html=True)

# --- SECURE INITIALIZATION ---
# Key comes from .streamlit/secrets.toml or the OPENAI_API_KEY environment variable.
def load_api_key() -> str:
    try:
        key = st.secrets["OPENAI_API_KEY"]
    except Exception:
        key = ""
    return key or os.environ.get("OPENAI_API_KEY", "")


api_key = load_api_key()
if not api_key:
    st.error("⚠️ Missing OpenAI API Key. Add 'OPENAI_API_KEY' to .streamlit/secrets.toml or the environment.")
    st.stop()

client = OpenAI(api_key=api_key)


def load_validated_image(upload) -> Image.Image:
    """Decode an uploaded file into a bounded, re-encoded RGB image."""
    data = upload.getvalue()
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError(f"Image is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.")

    Image.open(io.BytesIO(data)).verify()
    image = Image.open(io.BytesIO(data))
    if image.format not in {"JPEG", "PNG"}:
        raise ValueError("Only JPEG and PNG images are supported.")

    image = image.convert("RGB")
    image.thumbnail((MAX_DIMENSION, MAX_DIMENSION))
    return image


def to_jpeg_base64(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

st.title("🌱 AgroPulse.ai — Multi-Model Crop Diagnostic Suite")
st.write("Upload a crop tissue photo to pass it through our Deep Learning computer vision engine and OpenAI diagnostic layer.")

# --- SIDEBAR BILLING ENGINE ---
# NOTE: this selector is presentational only. It is client-controlled and must not be
# treated as an entitlement check; real plan enforcement needs server-side auth.
st.sidebar.title("🚜 Agronomist Portal")
user_tier = st.sidebar.radio("Select Plan Tier:", ["Free Plan (1 Scan/Day)", "Pro Farmer ($29/mo - Unlimited)"])

if user_tier == "Free Plan (1 Scan/Day)":
    st.sidebar.warning("🔒 Free tier accounts are limited to basic diagnostics.")
    st.sidebar.markdown("[⚡ Upgrade to Pro Farmer via Stripe](https://stripe.com)")
else:
    st.sidebar.success("👑 PRO Active: Unlimited Deep Gen Inferences Enabled")

# --- MAIN IMAGE CAPTURE INTERFACE ---
uploaded_file = st.file_uploader("Upload leaf or plant image...", type=["jpg", "jpeg", "png"])

if uploaded_file:
    try:
        img = load_validated_image(uploaded_file)
    except Exception as exc:
        logger.exception("Rejected uploaded image")
        st.error(f"❌ Could not process that image: {exc}")
        st.stop()

    col1, col2 = st.columns([1, 1.3])
    
    with col1:
        st.subheader("📷 Submitted Tissue Sample")
        st.image(img, use_container_width=True)
        
    with col2:
        st.subheader("🔬 Deep Learning & Agronomist Scan")
        
        # 1. Re-encode the validated image as JPEG and Base64 it for the OpenAI Vision API
        base64_image = to_jpeg_base64(img)

        # 2. Call OpenAI Vision to handle both classification AND solution generation
        with st.spinner("Analyzing plant cells and generating custom agronomist protocol..."):
            try:
                system_prompt = "You are a senior plant pathologist and expert commercial agronomist. Provide clean, highly accurate, actionable advice based on images."
                
                user_prompt = """
                Analyze this plant image. Act as a deep learning classifier and tell the farmer exactly what disease or issue you see.
                
                Format your final response using this exact clean structure:
                
                ### 🔍 Diagnosis: [Write the Plant Name and the Detected Disease/Issue Here]
                
                ### 🛑 1. Immediate Field Intervention Strategy
                (Provide specific spray ratios, organic alternatives, or pruning steps to kill this issue immediately)
                
                ### 🚀 2. Accelerated Growth Protocol
                (Provide exact N-P-K fertilizer shifts, soil remedies, or watering cadences to make this plant grow faster during recovery)
                """
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",  # Supports extremely accurate image processing
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    temperature=0.2 
                )
                
                generated_plan = response.choices[0].message.content or ""

                # Model output is untrusted: render it as Markdown, never as raw HTML.
                with st.container(border=True):
                    st.markdown(generated_plan)

            except Exception:
                logger.exception("OpenAI Vision request failed")
                st.error("Failed to access the OpenAI Vision layer. Please try again later.")
