# 🌾 FarmAI: AI Farming Assistant

An AI assistant for smallholder farmers in The Gambia and West Africa. Take a photo of a crop leaf to find out what disease it has and how to treat it, check the weather, get crop and yield advice, and ask a farming chatbot, all from a phone-friendly web app.

**[Live demo](YOUR_LIVE_LINK_HERE)** · Built by [Sulayman Bah](https://github.com/bahsulayman689-hash/farmer_AI)

![FarmAI screenshot](screenshots/home.png)

## Features

| Feature | What it does |
|---|---|
| 🍃 **Disease Detection** | Upload or capture a leaf photo. A CNN trained on PlantVillage identifies 38 plant disease and healthy classes, shows the confidence, the cause and a treatment plan. |
| 🌱 **Crop Recommendation** | Enter soil type, temperature, rainfall, pH and N-P-K values to get the top 3 crops with suitability scores. Covers rice, maize, groundnut, millet, cassava, sorghum, cowpea and tomato. |
| ⛅ **Weather Forecast** | Live 5-day forecast for any town (Open-Meteo), with farming advice such as when to delay spraying. |
| 📈 **Yield Prediction** | Estimates tons per hectare, total harvest for your farm size and the expected harvest date. |
| 💬 **Ask Farming AI** | Chatbot powered by Google Gemini, set up with a prompt for West African smallholder farmers. |
| 🕘 **History** | Saves past diagnoses, recommendations and questions in a local SQLite database. |

## How it works

```
Leaf photo → resize 224×224 → CNN (Keras) → class + confidence → treatment advice
Farm inputs → suitability scoring → crop ranking / yield estimate
Location → Open-Meteo API → forecast + advice
Question → Gemini API → answer
```

- **Model:** Sequential CNN (4 convolution and pooling blocks, a 256-unit dense layer and a 38-class softmax output), about 9 million parameters, trained on the PlantVillage dataset.
- **App:** Streamlit, with a mobile-friendly layout and a green theme.
- **Data and APIs:** SQLite, Open-Meteo (no key needed) and the Gemini API.

## Model results

| Metric | Value |
|---|---|
| Dataset | PlantVillage (38 classes) |
| Validation accuracy | _add your number_ |
| Macro F1 | _add your number_ |
| Model size | 18.5 MB (float16 weights) |

## Run it locally

```bash
git clone https://github.com/bahsulayman689-hash/farmer-ai.git
cd farmer-ai
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Create `.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "your-key"
```

Then start the app:

```bash
streamlit run app.py
```

Optional: set `HF_REPO` (and `HF_FILE`) in the secrets to download the model from a Hugging Face repo instead of the repo folder.

## Project structure

```
farmer-ai/
├── app.py                    # Streamlit app (all pages)
├── plant_village_model.keras # trained disease model
├── class_indices.json        # class index → label map
├── requirements.txt
└── .streamlit/config.toml    # theme
```

## Limitations

- Crop recommendation and yield prediction use typical agronomic ranges, not a model trained on local data. They give a guide, not a guarantee.
- Disease detection works best on a single clear leaf in good light. PlantVillage images are lab photos, so accuracy in the field will be lower.
- Treatment advice is written for 5 of the 38 classes so far. The others show a general message.
- Not a replacement for an agriculture extension officer.

## Roadmap

- [ ] Treatment advice for all 38 classes
- [ ] Train crop and yield models on Gambian data
- [ ] Field-photo fine-tuning to improve real-world accuracy
- [ ] Mandinka and Wolof language support
- [ ] FastAPI backend and a mobile app

## Tech stack

Python · TensorFlow/Keras · Streamlit · SQLite · Google Gemini API · Open-Meteo · NumPy · Pillow

## Author

**Sulayman Bah**, AI/ML engineer, The Gambia
[GitHub](https://github.com/bahsulayman689-hash) · [LinkedIn](https://linkedin.com/in/sulayman-bah-8a7096423) · bahsulayman689@gmail.com

## Acknowledgements

PlantVillage dataset · Open-Meteo · Google Gemini
