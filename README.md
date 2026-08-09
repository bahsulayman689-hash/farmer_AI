# 🌱 AgroPulse.ai — Multi-Model Crop Diagnostic Suite

An advanced deep learning and computer vision agritech application built using **Streamlit** and **OpenAI GPT-4o-mini Vision**. This software allows farmers to upload photos of diseased plant tissue to get instant classification diagnoses and custom biochemical growth acceleration remediation plans.

## 🛠️ Local Installation & Setup

Follow these steps to run the application on your local machine:

1. **Clone or navigate to the project directory:**
   ```bash
   cd your-project-folder
   ```

2. **Install all required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your secure environment credentials:**
   * Copy `secrets.toml.example` to `.streamlit/secrets.toml` and put your own key in it
     (or export `OPENAI_API_KEY` in the environment instead).
   * `.streamlit/secrets.toml` is git-ignored — never commit it.

4. **Launch the Streamlit production server:**
   ```bash
   streamlit run app_app.py
   ```

## 🏗️ Technical Architecture
* **Frontend UI Engine:** Streamlit Framework
* **Computer Vision Model:** OpenAI GPT-4o-mini (Vision API layer)
* **Image Processor:** Pillow & Base64 binary serialization streams
* **Monetization Layer:** Stripe Subscriptions API (Gateway integration ready)

## 🔒 Security Parameters
* Never check `.streamlit/secrets.toml` (or any file containing a real key) into the repository; `.gitignore` blocks it.
* Uploads are limited to JPEG/PNG under 8 MB, are validated with Pillow, and are downscaled and re-encoded before being sent to the model.
* Model output is rendered as Markdown, never as raw HTML.
* The plan-tier selector in the sidebar is UI-only. It is not authentication or entitlement enforcement — add server-side auth before charging for tiers.
