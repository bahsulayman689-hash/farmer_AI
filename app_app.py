import base64
import io
import logging

import streamlit as st
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    RateLimitError,
)
from PIL import Image, UnidentifiedImageError

try:  # Streamlit >= 1.44 raises a dedicated error for absent secrets.
    from streamlit.errors import StreamlitSecretNotFoundError
except ImportError:
    StreamlitSecretNotFoundError = FileNotFoundError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("agropulse")

st.set_page_config(page_title="AgroPulse.ai - Custom AI Agronomist", layout="wide")

# UI Enhancements for crisp image rendering and high scannability
st.markdown("""
    <style>
    img { image-rendering: -webkit-optimize-contrast !important; border-radius: 12px; }
    .report-box { padding: 25px; background-color: #f4f9f4; border-left: 6px solid #1b5e20; border-radius: 8px; margin-top: 20px; line-height: 1.6; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; }
    </style>
""", unsafe_allow_html=True)

# --- SECURE INITIALIZATION ---
# This looks for your key inside your local file: .streamlit/secrets.toml
@st.cache_resource
def get_openai_client() -> OpenAI:
    api_key = st.secrets["OPENAI_API_KEY"]
    if not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("OPENAI_API_KEY is present but empty")
    return OpenAI(api_key=api_key.strip())


try:
    client = get_openai_client()
except (KeyError, FileNotFoundError, ValueError, StreamlitSecretNotFoundError) as exc:
    logger.error("OpenAI client not configured: %s", exc)
    st.error(
        "⚠️ Missing or empty OpenAI API key. Add 'OPENAI_API_KEY' to your "
        "local .streamlit/secrets.toml file."
    )
    st.stop()
except Exception:
    logger.exception("Unexpected failure while initializing the OpenAI client")
    st.error(
        "⚠️ Could not initialize the OpenAI client. See the server logs for "
        "the full traceback."
    )
    st.stop()

st.title("🌱 AgroPulse.ai — Multi-Model Crop Diagnostic Suite")
st.write("Upload a crop tissue photo to pass it through our Deep Learning computer vision engine and OpenAI diagnostic layer.")

# --- SIDEBAR BILLING ENGINE ---
st.sidebar.title("🚜 Agronomist Portal")
user_tier = st.sidebar.radio("Select Plan Tier:", ["Free Plan (1 Scan/Day)", "Pro Farmer ($29/mo - Unlimited)"])

if user_tier == "Free Plan (1 Scan/Day)":
    st.sidebar.warning("🔒 Free tier accounts are limited to basic diagnostics.")
    st.sidebar.markdown("[⚡ Upgrade to Pro Farmer via Stripe](https://stripe.com)")
else:
    st.sidebar.success("👑 PRO Active: Unlimited Deep Gen Inferences Enabled")

# --- MAIN IMAGE CAPTURE INTERFACE ---
uploaded_file = st.file_uploader("Upload leaf or plant image...", type=["jpg", "jpeg", "png"])

def encode_image(image: Image.Image) -> tuple[str, str]:
    """Return the image as base64 plus the MIME subtype actually encoded."""
    buffer = io.BytesIO()
    source_format = (image.format or "JPEG").upper()
    try:
        image.save(buffer, format=source_format)
        encoded_format = source_format
    except (OSError, ValueError, KeyError) as exc:
        # Formats such as MPO, or modes such as RGBA/P, cannot always be
        # re-encoded in their original format; fall back to baseline JPEG.
        logger.warning("Re-encoding image as JPEG (%s failed: %s)", source_format, exc)
        buffer = io.BytesIO()
        image.convert("RGB").save(buffer, format="JPEG")
        encoded_format = "JPEG"

    mime_subtype = "jpeg" if encoded_format in ("JPEG", "JPG") else encoded_format.lower()
    return base64.b64encode(buffer.getvalue()).decode("utf-8"), mime_subtype


if uploaded_file:
    try:
        img = Image.open(uploaded_file)
        img.load()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        logger.warning("Rejected upload %r: %s", uploaded_file.name, exc)
        st.error(
            "⚠️ That file could not be read as an image. Please upload a valid "
            "JPG or PNG photo."
        )
        st.stop()

    col1, col2 = st.columns([1, 1.3])
    
    with col1:
        st.subheader("📷 Submitted Tissue Sample")
        st.image(img, use_container_width=True)
        
    with col2:
        st.subheader("🔬 Deep Learning & Agronomist Scan")
        
        # 1. Prepare raw image bytes and convert to Base64 for the OpenAI Vision API
        try:
            base64_image, mime_subtype = encode_image(img)
        except Exception:
            logger.exception("Failed to encode uploaded image %r", uploaded_file.name)
            st.error(
                "⚠️ This image could not be prepared for analysis. Try "
                "re-saving it as a standard JPG or PNG and uploading again."
            )
            st.stop()
        
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
                                        "url": f"data:image/{mime_subtype};base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    temperature=0.2 
                )
                
                generated_plan = (
                    response.choices[0].message.content if response.choices else None
                )
                if not generated_plan or not generated_plan.strip():
                    logger.error(
                        "OpenAI returned no diagnostic content (response id=%s, "
                        "finish_reason=%s)",
                        getattr(response, "id", None),
                        response.choices[0].finish_reason if response.choices else None,
                    )
                    st.error(
                        "⚠️ The diagnostic layer returned an empty response. "
                        "Please try again with a clearer photo."
                    )
                    st.stop()

                # Display the dynamic diagnostic plan directly inside our styled UI container
                st.markdown(f'<div class="report-box">{generated_plan}</div>', unsafe_allow_html=True)

            except AuthenticationError:
                logger.exception("OpenAI rejected the configured API key")
                st.error(
                    "⚠️ OpenAI rejected the configured API key. Check "
                    "'OPENAI_API_KEY' in .streamlit/secrets.toml."
                )
            except RateLimitError:
                logger.exception("OpenAI rate limit or quota exceeded")
                st.error(
                    "⚠️ Rate limit or quota exceeded on the OpenAI account. "
                    "Wait a moment and scan again."
                )
            except (APIConnectionError, APITimeoutError):
                logger.exception("Could not reach the OpenAI API")
                st.error(
                    "⚠️ Could not reach OpenAI. Check the server's network "
                    "connection and try again."
                )
            except APIStatusError as exc:
                logger.exception("OpenAI API returned status %s", exc.status_code)
                st.error(
                    f"⚠️ The OpenAI API returned an error (HTTP {exc.status_code}). "
                    "See the server logs for details."
                )
            except Exception:
                logger.exception("Unexpected failure in the diagnostic pipeline")
                st.error(
                    "⚠️ Unexpected failure while generating the diagnosis. See "
                    "the server logs for the full traceback."
                )
