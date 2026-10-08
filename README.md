# FarmAI - AI Farming Assistant

Features: Disease Detection (your Keras model), Crop Recommendation, Weather Forecast (Open-Meteo, no key),
Yield Prediction, AI Chatbot (Gemini), History (SQLite).

## Run
1. Copy `plant_village_model.h5` and `class_indices.json` into this folder.
2. `pip install -r requirements.txt`
3. Create `.streamlit/secrets.toml` with: `GEMINI_API_KEY = "your-key"`
4. `streamlit run app.py`

## Deploy
Push to GitHub, deploy on Streamlit Community Cloud, add GEMINI_API_KEY under Secrets.
Large .h5 files over 100 MB need Git LFS.
