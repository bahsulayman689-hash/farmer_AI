"""FarmAI - AI Farming Assistant (Streamlit). Run: streamlit run app.py"""
import os, json, sqlite3, datetime as dt
import numpy as np
import requests
import streamlit as st
from PIL import Image

st.set_page_config(page_title="FarmAI", page_icon="🌾", layout="centered")
st.markdown("""<style>
div.stButton>button{width:100%;border-radius:14px;padding:1.1rem .5rem;font-weight:600}
.hdr{background:#1B6B2F;color:#fff;padding:.8rem 1rem;border-radius:12px;margin-bottom:1rem;font-size:1.2rem;font-weight:700}
</style>""", unsafe_allow_html=True)

# ---------------- Storage (User/Farm data + logs) ----------------
def _db():
    c = sqlite3.connect("farmai.db")
    c.execute("create table if not exists history(ts text, kind text, summary text)")
    return c

def log(kind, summary):
    c = _db(); c.execute("insert into history values (?,?,?)",
        (dt.datetime.now().strftime("%Y-%m-%d %H:%M"), kind, summary)); c.commit(); c.close()

# ---------------- Knowledge ----------------
SOLUTIONS = {
    "Tomato___Late_blight": ("Tomato Late Blight", "Phytophthora infestans (oomycete)",
        ["Remove and destroy infected leaves and crop residues.", "Avoid overhead irrigation to keep foliage dry.", "Improve plant spacing for airflow.", "Apply a recommended fungicide."]),
    "Tomato___Early_blight": ("Tomato Early Blight", "Alternaria solani (fungus)",
        ["Prune lower infected leaves to stop soil splash.", "Rotate crops on a 3-year cycle.", "Mulch the soil to keep leaves dry."]),
    "Potato___Late_blight": ("Potato Late Blight", "Phytophthora infestans (oomycete)",
        ["Destroy volunteer potato plants and cull piles.", "Use certified disease-free seed tubers.", "Avoid excess nitrogen fertiliser."]),
    "Potato___Early_blight": ("Potato Early Blight", "Alternaria solani (fungus)",
        ["Improve soil fertility (nitrogen and potassium).", "Rotate crops strictly.", "Harvest only when vines are fully dead."]),
    "Apple___Apple_scab": ("Apple Scab", "Venturia inaequalis (fungus)",
        ["Rake and destroy fallen leaves in autumn.", "Prune the canopy for sun and airflow.", "Apply protective fungicide at bud-break."]),
}
CROPS = {  # approximate agronomic ranges; replace with your own data/model later
    "Rice":      dict(e="🌾", temp=(22,32), rain=(100,300), ph=(5.5,7.0), n=(60,120), p=(30,60), k=(30,60), soil=["Clay","Loamy"],  y=4.0,  d=120),
    "Maize":     dict(e="🌽", temp=(18,32), rain=(60,150),  ph=(5.8,7.0), n=(80,140), p=(30,60), k=(30,60), soil=["Loamy","Silty"], y=3.5,  d=100),
    "Tomato":    dict(e="🍅", temp=(18,29), rain=(40,120),  ph=(6.0,6.8), n=(70,120), p=(40,80), k=(60,120),soil=["Loamy","Sandy"], y=20.0, d=90),
    "Groundnut": dict(e="🥜", temp=(22,32), rain=(50,130),  ph=(5.8,7.0), n=(10,40),  p=(30,60), k=(30,60), soil=["Sandy","Loamy"], y=1.5,  d=110),
    "Millet":    dict(e="🌱", temp=(25,35), rain=(30,100),  ph=(5.5,7.5), n=(30,80),  p=(20,40), k=(20,40), soil=["Sandy","Loamy"], y=1.0,  d=90),
    "Cassava":   dict(e="🍠", temp=(25,32), rain=(80,200),  ph=(5.5,7.0), n=(40,100), p=(20,50), k=(60,120),soil=["Sandy","Loamy"], y=10.0, d=270),
    "Sorghum":   dict(e="🌾", temp=(25,33), rain=(40,120),  ph=(5.5,7.5), n=(50,100), p=(20,40), k=(20,40), soil=["Loamy","Clay"],  y=1.5,  d=110),
    "Cowpea":    dict(e="🫘", temp=(24,32), rain=(40,100),  ph=(5.5,7.0), n=(10,40),  p=(30,60), k=(30,60), soil=["Sandy","Loamy"], y=1.0,  d=70),
}
WMO = {0:"Clear ☀️",1:"Mostly clear 🌤️",2:"Partly cloudy ⛅",3:"Cloudy ☁️",45:"Fog 🌫️",48:"Fog 🌫️",51:"Drizzle 🌦️",53:"Drizzle 🌦️",55:"Drizzle 🌦️",
       61:"Rain 🌧️",63:"Rain 🌧️",65:"Heavy rain 🌧️",80:"Showers 🌦️",81:"Showers 🌦️",82:"Heavy showers ⛈️",95:"Thunderstorm ⛈️",96:"Thunderstorm ⛈️",99:"Thunderstorm ⛈️"}

def fit(v, lo, hi):
    if lo <= v <= hi: return 1.0
    d = (lo - v) if v < lo else (v - hi)
    return max(0.0, 1 - d / ((hi - lo) or 1))

def suitability(c, soil, temp, rain, ph, n, p, k):
    s = [fit(temp,*c["temp"]), fit(rain,*c["rain"]), fit(ph,*c["ph"]), fit(n,*c["n"]), fit(p,*c["p"]), fit(k,*c["k"]),
         1.0 if soil in c["soil"] else 0.4]
    return sum(s) / len(s)

# ---------------- Disease model ----------------
def get_secret(name, default=None):
    try: return st.secrets[name]
    except Exception: return os.getenv(name, default)

MODEL_FILES = ["plant_village_model.keras", "plant_village_model.h5"]

def find_model_file():
    """Local file first; otherwise download from Hugging Face if HF_REPO is set in secrets."""
    for f in MODEL_FILES:
        if os.path.exists(f): return f
    repo = get_secret("HF_REPO")
    if repo:
        from huggingface_hub import hf_hub_download
        return hf_hub_download(repo_id=repo, filename=get_secret("HF_FILE", "plant_village_model.keras"),
                               token=get_secret("HF_TOKEN"))
    return None

def _clean_keras_copy(path):
    """Copy of a .keras file with 'quantization_config' removed (newer Keras -> older Keras)."""
    import zipfile, tempfile
    def strip(o):
        if isinstance(o, dict): return {k: strip(v) for k, v in o.items() if k != "quantization_config"}
        if isinstance(o, list): return [strip(x) for x in o]
        return o
    out = os.path.join(tempfile.gettempdir(), "farmai_clean.keras")
    with zipfile.ZipFile(path) as zi, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            data = zi.read(it.filename)
            if it.filename == "config.json": data = json.dumps(strip(json.loads(data))).encode()
            zo.writestr(it.filename, data)
    return out

@st.cache_resource(show_spinner="Loading model...")
def load_model():
    path = find_model_file()
    if not path: return None
    import tensorflow as tf
    try:
        return tf.keras.models.load_model(path, compile=False)
    except Exception:
        if path.endswith(".keras"):
            return tf.keras.models.load_model(_clean_keras_copy(path), compile=False)
        class PatchedDense(tf.keras.layers.Dense):   # .h5 files: ignore 'quantization_config'
            def __init__(self, *args, quantization_config=None, **kwargs):
                super().__init__(*args, **kwargs)
        return tf.keras.models.load_model(path, custom_objects={"Dense": PatchedDense}, compile=False)

def load_labels():
    if os.path.exists("class_indices.json"):
        with open("class_indices.json") as f:
            data = json.load(f)
        labels = {}
        for a, b in data.items():
            if str(a).isdigit(): labels[int(a)] = b     # {"0": "Apple___Apple_scab"}
            else: labels[int(b)] = a                    # {"Apple___Apple_scab": 0}
        return labels
    return {i: f"Class_{i}" for i in range(38)}

# ---------------- Navigation ----------------
if "page" not in st.session_state: st.session_state.page = "Home"
if "chat" not in st.session_state: st.session_state.chat = []
def go(p): st.session_state.page = p
def header(title):
    st.markdown(f'<div class="hdr">{title}</div>', unsafe_allow_html=True)
    st.button("← Home", on_click=go, args=("Home",), key="back")

page = st.session_state.page

# ---------------- Pages ----------------
if page == "Home":
    st.markdown('<div class="hdr">🌾 FarmAI</div>', unsafe_allow_html=True)
    st.subheader("Hello, Farmer 👋")
    st.caption("How can we help your farm today?")
    a, b = st.columns(2)
    a.button("🍃 Disease Detection", on_click=go, args=("Disease Detection",))
    b.button("🌱 Crop Recommendation", on_click=go, args=("Crop Recommendation",))
    c, d = st.columns(2)
    c.button("⛅ Weather Forecast", on_click=go, args=("Weather Forecast",))
    d.button("📈 Yield Prediction", on_click=go, args=("Yield Prediction",))
    st.button("💬 Ask Farming AI (Chat)", on_click=go, args=("Ask AI",))
    st.button("🕘 History", on_click=go, args=("History",))

elif page == "Disease Detection":
    header("Disease Detection")
    f = st.file_uploader("Upload or capture a plant leaf", type=["jpg", "jpeg", "png"])
    cam = st.camera_input("…or take a photo") if st.toggle("Use camera") else None
    f = f or cam
    if f:
        img = Image.open(f).convert("RGB")
        st.image(img, use_container_width=True)
        model = load_model()
        if model is None:
            st.error("Model not found. Put plant_village_model.keras (or .h5) in the app folder, or set HF_REPO in secrets.")
        elif st.button("Analyze Image", type="primary"):
            with st.spinner("Analyzing leaf..."):
                x = np.expand_dims(np.array(img.resize((224, 224))).astype("float32") / 255.0, 0)
                pred = model.predict(x, verbose=0)[0]
                labels = load_labels()
                top = np.argsort(pred)[::-1][:3]
                raw = labels.get(int(top[0]), "Unknown"); conf = float(pred[top[0]])
            name, cause, steps = SOLUTIONS.get(raw, (raw.replace("___", " – ").replace("_", " "),
                "Healthy, or a disease not yet in the solutions list.",
                ["Monitor the plant weekly.", "Keep regular watering and feeding.", "Ask the AI chat for advice if symptoms appear."]))
            st.success(f"### {name}")
            st.metric("Confidence", f"{conf*100:.1f}%")
            if conf < 0.6: st.warning("Low confidence. Retake the photo in good light with one leaf filling the frame.")
            st.markdown(f"**Cause:** {cause}")
            st.markdown("**Treatment**")
            for s in steps:
                st.markdown(f"- {s}")
            with st.expander("Other possibilities"):
                for i in top[1:]: st.write(f"{labels.get(int(i), i)}: {pred[i]*100:.1f}%")
            log("Disease", f"{name} ({conf*100:.0f}%)")

elif page == "Crop Recommendation":
    header("Crop Recommendation")
    soil = st.selectbox("Soil type", ["Loamy", "Sandy", "Clay", "Silty"])
    c1, c2 = st.columns(2)
    temp = c1.number_input("Temperature (°C)", 5.0, 45.0, 30.0)
    rain = c2.number_input("Rainfall (mm / month)", 0.0, 500.0, 120.0)
    ph = c1.number_input("Soil pH", 3.5, 9.5, 6.5)
    n = c2.number_input("Nitrogen (N)", 0, 200, 90)
    p = c1.number_input("Phosphorus (P)", 0, 200, 40)
    k = c2.number_input("Potassium (K)", 0, 200, 50)
    if st.button("Get Recommendation", type="primary"):
        res = sorted(((suitability(c, soil, temp, rain, ph, n, p, k), name) for name, c in CROPS.items()), reverse=True)[:3]
        st.subheader("Best crops for you")
        for i, (s, name) in enumerate(res, 1):
            st.markdown(f"**{i}. {CROPS[name]['e']} {name}**: score {s*100:.0f}%"); st.progress(s)
        log("Crop", f"Top: {res[0][1]} ({res[0][0]*100:.0f}%)")

elif page == "Weather Forecast":
    header("Weather Forecast")
    city = st.text_input("Location", "Banjul")
    try:
        g = requests.get("https://geocoding-api.open-meteo.com/v1/search", params={"name": city, "count": 1}, timeout=10).json()
        if not g.get("results"): st.warning("Location not found."); st.stop()
        loc = g["results"][0]
        w = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": loc["latitude"], "longitude": loc["longitude"], "timezone": "auto", "forecast_days": 5,
            "current": "temperature_2m,relative_humidity_2m,weather_code",
            "daily": "temperature_2m_max,precipitation_probability_max,weather_code"}, timeout=10).json()
        cur, day = w["current"], w["daily"]
        st.markdown(f"### {loc['name']}, {loc.get('country','')}")
        a, b, c = st.columns(3)
        a.metric("Now", f"{cur['temperature_2m']:.0f} °C"); b.metric("Humidity", f"{cur['relative_humidity_2m']}%")
        c.metric("Rain chance", f"{day['precipitation_probability_max'][0]}%")
        st.write(WMO.get(cur["weather_code"], "—"))
        st.markdown("**5-day forecast**")
        for t, mx, pr, wc in zip(day["time"], day["temperature_2m_max"], day["precipitation_probability_max"], day["weather_code"]):
            st.write(f"{dt.date.fromisoformat(t).strftime('%a %d %b')}: {mx:.0f} °C · rain {pr}% · {WMO.get(wc,'—')}")
        rainy = max(day["precipitation_probability_max"][:3])
        st.info("Rain likely soon: delay spraying and fertiliser, and prepare drainage." if rainy >= 60
                else "Mostly dry: good time for spraying, weeding and harvesting; check irrigation.")
    except Exception as e:
        st.error(f"Could not load weather (check your internet connection): {e}")

elif page == "Yield Prediction":
    header("Yield Prediction")
    crop = st.selectbox("Crop", list(CROPS))
    soil = st.selectbox("Soil type", ["Loamy", "Sandy", "Clay", "Silty"])
    area = st.number_input("Farm size (hectares)", 0.1, 1000.0, 1.0)
    plant = st.date_input("Planting date", dt.date.today())
    c1, c2 = st.columns(2)
    temp = c1.number_input("Avg temperature (°C)", 5.0, 45.0, 30.0)
    rain = c2.number_input("Rainfall (mm / month)", 0.0, 500.0, 120.0)
    ph = c1.number_input("Soil pH", 3.5, 9.5, 6.5)
    n = c2.number_input("Nitrogen (N)", 0, 200, 90)
    p = c1.number_input("Phosphorus (P)", 0, 200, 40)
    k = c2.number_input("Potassium (K)", 0, 200, 50)
    if st.button("Predict Yield", type="primary"):
        c = CROPS[crop]; s = suitability(c, soil, temp, rain, ph, n, p, k)
        per_ha = c["y"] * (0.4 + 0.7 * s)
        harvest = plant + dt.timedelta(days=c["d"])
        st.metric("Expected yield", f"{per_ha:.1f} tons/ha", f"{per_ha*0.8:.1f} – {per_ha*1.2:.1f} range")
        st.metric("Total for your farm", f"{per_ha*area:.1f} tons")
        st.metric("Estimated harvest", harvest.strftime("%d %b %Y"), f"{c['d']} days")
        st.caption(f"Growing-condition match: {s*100:.0f}%. This is an estimate from typical crop data, not a trained model.")
        log("Yield", f"{crop}: {per_ha*area:.1f} t on {area} ha")

elif page == "Ask AI":
    header("AI Farming Chatbot")
    SYS = ("You are FarmAI, a practical farming assistant for smallholder farmers in The Gambia and West Africa. "
           "Give short, clear answers with numbered possible causes and simple steps. Prefer low-cost, locally available solutions. "
           "If unsure, say so and suggest visiting the local agriculture extension officer.")
    key = get_secret("GEMINI_API_KEY")
    if not key: st.info("Add GEMINI_API_KEY in .streamlit/secrets.toml to enable the AI chat.")
    for m in st.session_state.chat:
        st.chat_message("user" if m["role"] == "user" else "assistant").write(m["text"])
    q = st.chat_input("Type your message…")
    if q and key:
        st.session_state.chat.append({"role": "user", "text": q}); st.chat_message("user").write(q)
        model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
        body = {"system_instruction": {"parts": [{"text": SYS}]},
                "contents": [{"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["text"]}]} for m in st.session_state.chat[-10:]]}
        try:
            r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                              params={"key": key}, json=body, timeout=60)
            data = r.json()
            if data.get("candidates") and data["candidates"][0].get("content"):
                ans = data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                err = data.get("error", {}).get("message") or str(data)[:300]
                ans = f"Gemini error (HTTP {r.status_code}): {err}"
        except Exception as e:
            ans = f"Sorry, the AI could not answer right now ({e})."
        st.session_state.chat.append({"role": "model", "text": ans}); st.chat_message("assistant").write(ans)
        log("Chat", q[:80])

elif page == "History":
    header("History")
    c = _db(); rows = c.execute("select ts, kind, summary from history order by ts desc limit 50").fetchall(); c.close()
    if not rows: st.info("Nothing saved yet.")
    for ts, kind, s in rows: st.write(f"**{kind}** · {ts}  \n{s}")