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
   * Create a folder named `.streamlit` in the root directory.
   * Inside that folder, create a file named `secrets.toml`.
   * Paste your OpenAI API token into the secrets file exactly like this:
     ```toml
     OPENAI_API_KEY = "sk-proj-yourActualSecretKeyHere..."
     ```

4. **Launch the Streamlit production server:**
   ```bash
   streamlit run app.py
   ```

## 🧪 Running the Test Suite

The UI-independent diagnostic logic lives in `agropulse/core.py` and is covered by unit tests:

```bash
pip install -r requirements-dev.txt
pytest
```

`pytest` prints a coverage report for the `agropulse` package (no API key or network access required).

## 🏗️ Technical Architecture
* **Frontend UI Engine:** Streamlit Framework
* **Computer Vision Model:** OpenAI GPT-4o-mini (Vision API layer)
* **Image Processor:** Pillow & Base64 binary serialization streams
* **Monetization Layer:** Stripe Subscriptions API (Gateway integration ready)

## 🔒 Security Parameters
Never check your `.streamlit/secrets.toml` file into public GitHub repositories. Ensure your `.gitignore` file includes `.streamlit/` to protect your API keys from automated scrapers.
