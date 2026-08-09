import streamlit as st
from PIL import Image
from openai import OpenAI

from agropulse.core import FREE_TIER, PRO_TIER, diagnose

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
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("⚠️ Missing OpenAI API Key. Please add 'OPENAI_API_KEY' to your local .streamlit/secrets.toml file.")
    st.stop()

st.title("🌱 AgroPulse.ai — Multi-Model Crop Diagnostic Suite")
st.write("Upload a crop tissue photo to pass it through our Deep Learning computer vision engine and OpenAI diagnostic layer.")

# --- SIDEBAR BILLING ENGINE ---
st.sidebar.title("🚜 Agronomist Portal")
user_tier = st.sidebar.radio("Select Plan Tier:", [FREE_TIER, PRO_TIER])

if user_tier == FREE_TIER:
    st.sidebar.warning("🔒 Free tier accounts are limited to basic diagnostics.")
    st.sidebar.markdown("[⚡ Upgrade to Pro Farmer via Stripe](https://stripe.com)")
else:
    st.sidebar.success("👑 PRO Active: Unlimited Deep Gen Inferences Enabled")

# --- MAIN IMAGE CAPTURE INTERFACE ---
uploaded_file = st.file_uploader("Upload leaf or plant image...", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img = Image.open(uploaded_file)
    
    col1, col2 = st.columns([1, 1.3])
    
    with col1:
        st.subheader("📷 Submitted Tissue Sample")
        st.image(img, use_container_width=True)
        
    with col2:
        st.subheader("🔬 Deep Learning & Agronomist Scan")
        
        # Call OpenAI Vision to handle both classification AND solution generation
        with st.spinner("Analyzing plant cells and generating custom agronomist protocol..."):
            try:
                generated_plan = diagnose(client, img)

                # Display the dynamic diagnostic plan directly inside our styled UI container
                st.markdown(f'<div class="report-box">{generated_plan}</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Failed to access OpenAI Vision layer: {str(e)}")
