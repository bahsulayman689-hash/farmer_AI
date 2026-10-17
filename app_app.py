"""FarmAI - AI Farming Assistant (Streamlit). Run: streamlit run app.py"""
import os, json, re, io, base64, hashlib, time, sqlite3, urllib.parse, html as _h, datetime as dt
import numpy as np
import requests
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

st.set_page_config(page_title="FarmAI", page_icon="🌾", layout="centered", initial_sidebar_state="auto")

# ---------------- Design system ----------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700;12..96,800&family=Figtree:wght@400;500;600;700&display=swap');
:root{--g:#12503A;--g2:#1F6B4E;--gl:#E4F0E8;--gold:#E3A72F;--ink:#14231B;--mut:#5B6B61;--line:#E1E8DF;--bg:#F2F5F0;--red:#C2543B;}
html,body,.stApp,[class*="st-"]{font-family:'Figtree',system-ui,sans-serif;}
.stApp{background:var(--bg);color:var(--ink);}
#MainMenu,footer,[data-testid="stToolbarActions"],[data-testid="stAppDeployButton"],[data-testid="stDecoration"]{display:none!important;}
header[data-testid="stHeader"]{background:transparent;}
[data-testid="stExpandSidebarButton"],[data-testid="stSidebarCollapsedControl"]{color:var(--g);}
.block-container{max-width:720px;padding:1.2rem 1rem 4rem;}
[data-testid="stIconMaterial"],[class*="material-symbols"]{font-family:"Material Symbols Rounded"!important;}
h1,h2,h3,.disp{font-family:'Bricolage Grotesque','Figtree',sans-serif;letter-spacing:-.01em;}

/* hero */
.hero{position:relative;overflow:hidden;background:var(--g);border-radius:22px;padding:1.6rem 1.4rem 1.5rem;margin-bottom:1.1rem;color:#fff;
 background-image:repeating-linear-gradient(105deg,rgba(255,255,255,.045) 0 2px,transparent 2px 20px),linear-gradient(135deg,#0E3F2D,#1F6B4E);}
.hero:after{content:"🌾";position:absolute;right:-6px;bottom:-22px;font-size:7.5rem;opacity:.16;transform:rotate(-10deg);}
.hero-date{font-size:.85rem;font-weight:600;color:var(--gold);margin-bottom:.35rem;}
.hero-h{font-family:'Bricolage Grotesque',sans-serif;font-size:2rem;font-weight:800;line-height:1.1;margin-bottom:.45rem;}
.hero-p{font-size:1rem;color:#D3E6DA;max-width:30rem;}

/* page header */
.ph{display:flex;align-items:center;gap:.8rem;margin:.2rem 0 1.1rem;}
.ph-ic{width:48px;height:48px;border-radius:14px;background:var(--gl);display:flex;align-items:center;justify-content:center;font-size:1.5rem;flex:none;}
.ph-t{font-family:'Bricolage Grotesque',sans-serif;font-size:1.6rem;font-weight:700;line-height:1.1;}
.ph-s{color:var(--mut);font-size:.92rem;margin-top:2px;}

/* bordered containers = cards */
div[data-testid="stVerticalBlockBorderWrapper"]{background:#fff;border:1px solid var(--line)!important;border-radius:18px!important;}
.tile-ic{width:46px;height:46px;border-radius:13px;display:flex;align-items:center;justify-content:center;font-size:1.45rem;margin-bottom:.7rem;}
.tile-t{font-family:'Bricolage Grotesque',sans-serif;font-weight:700;font-size:1.12rem;margin-bottom:.15rem;}
.tile-d{color:var(--mut);font-size:.88rem;line-height:1.35;margin-bottom:.7rem;min-height:2.4em;}

/* buttons */
div.stButton>button{width:100%;border-radius:12px;padding:.6rem .9rem;font-weight:600;border:1px solid var(--line);background:#fff;color:var(--g);transition:all .15s;}
div.stButton>button:hover{border-color:var(--g);color:var(--g);background:var(--gl);}
div.stButton>button:focus-visible{outline:3px solid var(--gold);outline-offset:2px;}
div.stButton>button[kind="primary"]{background:var(--g);color:#fff;border-color:var(--g);padding:.75rem 1rem;font-size:1rem;}
div.stButton>button[kind="primary"]:hover{background:var(--g2);color:#fff;}

/* inputs */
div[data-baseweb="input"],div[data-baseweb="select"]>div,div[data-baseweb="base-input"],.stTextInput input{border-radius:12px!important;}
label[data-testid="stWidgetLabel"] p{font-weight:600;color:var(--ink);font-size:.92rem;}
[data-testid="stFileUploaderDropzone"]{border-radius:16px;border:2px dashed #B9CBBE;background:#fff;}
[data-testid="stImage"] img{border-radius:16px;}

/* result blocks */
.card{background:#fff;border:1px solid var(--line);border-radius:18px;padding:1.1rem 1.2rem;margin:.7rem 0;}
.badge{display:inline-block;font-size:.78rem;font-weight:700;padding:.2rem .65rem;border-radius:99px;}
.b-ok{background:#DDF1E3;color:#17703A;} .b-bad{background:#FBE3DC;color:#A63A22;} .b-warn{background:#FBEFCF;color:#8A5E00;}
.res-t{font-family:'Bricolage Grotesque',sans-serif;font-size:1.55rem;font-weight:800;margin:.5rem 0 .2rem;line-height:1.15;}
.res-c{color:var(--mut);font-size:.92rem;margin-bottom:.8rem;}
.lbl{font-weight:700;font-size:.95rem;margin:.9rem 0 .35rem;}
.bar{height:10px;background:#E8EEE6;border-radius:99px;overflow:hidden;}
.bar span{display:block;height:100%;border-radius:99px;}
.conf{display:flex;justify-content:space-between;font-size:.88rem;font-weight:600;margin-bottom:.35rem;}
.steps{margin:0;padding:0;list-style:none;}
.steps li{display:flex;gap:.7rem;padding:.55rem 0;border-top:1px solid var(--line);font-size:.95rem;line-height:1.4;}
.steps li:first-child{border-top:0;}
.steps b{flex:none;width:24px;height:24px;border-radius:50%;background:var(--gl);color:var(--g);display:flex;align-items:center;justify-content:center;font-size:.8rem;}
.alt{display:flex;justify-content:space-between;font-size:.9rem;padding:.3rem 0;color:var(--mut);}

/* crop ranks */
.rank{display:flex;gap:.9rem;align-items:center;}
.rank-e{width:54px;height:54px;border-radius:15px;background:var(--gl);display:flex;align-items:center;justify-content:center;font-size:1.9rem;flex:none;}
.rank-b{flex:1;min-width:0;}
.rank-n{display:flex;justify-content:space-between;align-items:baseline;font-weight:700;font-size:1.05rem;margin-bottom:.4rem;}
.rank-n span{font-family:'Bricolage Grotesque',sans-serif;font-size:1.25rem;color:var(--g);}
.rank-w{font-size:.82rem;color:var(--mut);margin-top:.4rem;}
.first{border:2px solid var(--g);}

/* weather */
.wx{background:linear-gradient(135deg,#0E3F2D,#1F6B4E);color:#fff;border-radius:22px;padding:1.3rem 1.4rem;margin:.4rem 0 .9rem;}
.wx-loc{font-weight:600;color:#CFE3D6;font-size:.95rem;}
.wx-main{display:flex;align-items:baseline;gap:.9rem;flex-wrap:wrap;margin:.2rem 0 .8rem;}
.wx-temp{font-family:'Bricolage Grotesque',sans-serif;font-size:3.6rem;font-weight:800;line-height:1;}
.wx-cond{font-size:1.15rem;font-weight:600;}
.wx-row{display:flex;gap:1.6rem;font-size:.9rem;color:#CFE3D6;}
.wx-row b{display:block;color:#fff;font-size:1.1rem;}
.fc{display:flex;gap:.6rem;overflow-x:auto;padding-bottom:.4rem;}
.fc div{flex:1 0 96px;background:#fff;border:1px solid var(--line);border-radius:16px;padding:.8rem .5rem;text-align:center;}
.fc .d{font-weight:700;font-size:.85rem;color:var(--mut);} .fc .i{font-size:1.6rem;margin:.2rem 0;}
.fc .t{font-family:'Bricolage Grotesque',sans-serif;font-weight:700;font-size:1.2rem;} .fc .r{font-size:.8rem;color:var(--g2);font-weight:600;}
.tip{background:#FBF3DC;border-left:4px solid var(--gold);border-radius:12px;padding:.8rem 1rem;font-size:.95rem;margin-top:.8rem;}

/* yield stats */
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.7rem;margin:.7rem 0;}
.stat{background:#fff;border:1px solid var(--line);border-radius:16px;padding:.9rem 1rem;}
.stat small{color:var(--mut);font-weight:600;font-size:.8rem;} .stat .v{font-family:'Bricolage Grotesque',sans-serif;font-size:1.65rem;font-weight:800;color:var(--g);line-height:1.2;}
.stat .s{font-size:.8rem;color:var(--mut);}
.stat.hi{background:var(--g);border-color:var(--g);} .stat.hi small,.stat.hi .s{color:#CFE3D6;} .stat.hi .v{color:#fff;}
.note{color:var(--mut);font-size:.82rem;margin-top:.4rem;}

/* history + activity */
.row{display:flex;gap:.8rem;align-items:flex-start;background:#fff;border:1px solid var(--line);border-radius:14px;padding:.75rem .9rem;margin-bottom:.5rem;}
.row .ic{width:36px;height:36px;border-radius:10px;background:var(--gl);display:flex;align-items:center;justify-content:center;flex:none;}
.row .tx{flex:1;min-width:0;font-size:.93rem;font-weight:600;} .row .tm{font-size:.78rem;color:var(--mut);font-weight:500;}
.sec{font-family:'Bricolage Grotesque',sans-serif;font-weight:700;font-size:1.2rem;margin:1.3rem 0 .6rem;}

/* calendar tasks */
.tk{border-left:4px solid #B9CBBE;padding:.45rem .8rem;margin:.4rem 0;font-size:.93rem;background:#F8FBF7;border-radius:0 12px 12px 0;}
.tk.done{border-color:var(--g);opacity:.6;} .tk.due{border-color:var(--gold);} .tk.late{border-color:var(--red);}
.tk b{font-weight:600;} .tk small{display:block;color:var(--mut);font-size:.8rem;margin-top:1px;}
.tk .warn{color:#8A5E00;font-weight:600;font-size:.82rem;margin-top:3px;}
.pl{display:flex;justify-content:space-between;align-items:center;gap:.6rem;margin-bottom:.5rem;}
.pl-n{font-family:'Bricolage Grotesque',sans-serif;font-weight:800;font-size:1.25rem;} .pl-m{color:var(--mut);font-size:.85rem;}
/* chat */
[data-testid="stChatMessage"]{background:#fff;border:1px solid var(--line);border-radius:16px;}
[data-testid="stChatInput"]{border-radius:16px;}
/* sidebar */
section[data-testid="stSidebar"]{background:linear-gradient(185deg,#0E3F2D 0%,#12503A 100%);border-right:0;}
section[data-testid="stSidebar"] *{color:#E4F0E8;}
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"]{padding-bottom:0;}
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"]{padding-top:.2rem;}
.sb-brand{display:flex;gap:.75rem;align-items:center;padding:.2rem .3rem 1.1rem;}
.sb-logo{width:46px;height:46px;border-radius:14px;background:rgba(255,255,255,.13);display:flex;align-items:center;justify-content:center;font-size:1.6rem;flex:none;}
section[data-testid="stSidebar"] .sb-name{font-family:'Bricolage Grotesque',sans-serif;font-weight:800;font-size:1.45rem;color:#fff;line-height:1.05;}
section[data-testid="stSidebar"] .sb-tag{font-size:.78rem;color:#A9C9B6;margin-top:2px;}
section[data-testid="stSidebar"] div.stButton>button{background:transparent;border:0;color:#D3E6DA;justify-content:flex-start;text-align:left;padding:.58rem .85rem;border-radius:12px;font-weight:600;box-shadow:none;}
section[data-testid="stSidebar"] div.stButton>button *{color:inherit;text-align:left;}
section[data-testid="stSidebar"] div.stButton>button:hover{background:rgba(255,255,255,.1);color:#fff;border:0;}
section[data-testid="stSidebar"] div.stButton>button[kind="primary"]{background:#fff;color:#12503A;padding:.58rem .85rem;font-size:1rem;box-shadow:inset 4px 0 0 #E3A72F;}
section[data-testid="stSidebar"] div.stButton>button[kind="primary"]:hover{background:#fff;color:#12503A;}
section[data-testid="stSidebar"] [data-testid="stElementContainer"]:has(.stButton){margin-bottom:-.35rem;}
.sb-user{display:flex;gap:.6rem;align-items:center;background:rgba(255,255,255,.09);border-radius:12px;padding:.5rem .6rem;margin-bottom:.4rem;}
.sb-av{width:30px;height:30px;border-radius:50%;background:#E3A72F;color:#14231B!important;font-weight:800;display:flex;align-items:center;justify-content:center;flex:none;}
section[data-testid="stSidebar"] .sb-av{color:#14231B;}
.sb-em{font-size:.82rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
div[data-testid="stFormSubmitButton"]>button{width:100%;border-radius:12px;background:var(--g);color:#fff;border:1px solid var(--g);padding:.75rem 1rem;font-weight:600;font-size:1rem;}
div[data-testid="stFormSubmitButton"]>button:hover{background:var(--g2);color:#fff;border-color:var(--g2);}
div[data-testid="stFormSubmitButton"]{width:100%;}
.sb-sep{height:1px;background:rgba(255,255,255,.14);margin:1rem .3rem .8rem;}
section[data-testid="stSidebar"] label p{color:#A9C9B6;font-size:.82rem;font-weight:600;}
section[data-testid="stSidebar"] input,section[data-testid="stSidebar"] div[data-baseweb="select"] *{color:#14231B!important;-webkit-text-fill-color:#14231B!important;}
section[data-testid="stSidebar"] div[data-baseweb="select"] svg{fill:#5B6B61!important;color:#5B6B61!important;}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"]{color:#A9C9B6;}
.sb-stats{display:grid;grid-template-columns:1fr 1fr;gap:.5rem;margin:.9rem 0 .6rem;}
.sb-stats div{background:rgba(255,255,255,.09);border-radius:12px;padding:.6rem .7rem;font-size:.75rem;color:#A9C9B6;}
section[data-testid="stSidebar"] .sb-stats b{display:block;font-family:'Bricolage Grotesque',sans-serif;font-size:1.15rem;color:#fff;}
.sb-foot{font-size:.74rem;color:#7FA38E;padding:.4rem .3rem 0;line-height:1.4;}
[data-testid="stElementContainer"]:has(>.stButton){width:100%!important;}
.stButton{width:100%!important;}
.stButton>button{width:100%!important;}
/* mobile bottom tab bar */
.st-key-tabbar{display:none;}
@media (max-width:768px){
 .st-key-tabbar{display:block;position:fixed;left:0;right:0;bottom:0;z-index:999;background:#fff;border-top:1px solid var(--line);
  padding:.35rem .5rem calc(.35rem + env(safe-area-inset-bottom,0px));box-shadow:0 -4px 16px rgba(20,35,27,.07);}
 .st-key-tabbar div[data-testid="stHorizontalBlock"]{flex-direction:row!important;flex-wrap:nowrap!important;gap:.25rem!important;}
 .st-key-tabbar div[data-testid="stColumn"],.st-key-tabbar div[data-testid="column"]{min-width:0!important;width:100%!important;flex:1 1 0!important;}
 .st-key-tabbar div.stButton>button{justify-content:center;border:0;background:transparent;color:#5B6B61;padding:.6rem .1rem;border-radius:12px;box-shadow:none;}
 .st-key-tabbar div.stButton>button *{font-size:.8rem;font-weight:700;white-space:nowrap;color:inherit;}
 .st-key-tabbar div.stButton>button:hover{background:var(--gl);color:var(--g);}
 .st-key-tabbar div.stButton>button[kind="primary"]{background:var(--gl);color:var(--g);padding:.6rem .1rem;font-size:.8rem;}
 .block-container{padding-top:4rem;padding-bottom:6.5rem;}
 [data-testid="stBottom"]{padding-bottom:4rem;}
}
@media (max-width:480px){.hero-h{font-size:1.65rem}.wx-temp{font-size:3rem}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

def html(s): st.markdown(s, unsafe_allow_html=True)
def esc(s): return _h.escape(str(s))
def bar(p, color="#12503A"): return f'<div class="bar"><span style="width:{max(0,min(1,p))*100:.0f}%;background:{color}"></span></div>'
def level_color(p): return "#1F8A4C" if p >= .8 else "#E3A72F" if p >= .6 else "#C2543B"

# ---------------- Storage (User/Farm data + logs) ----------------
# Cloud mode: set SUPABASE_URL and SUPABASE_ANON_KEY in secrets. Every farmer signs in and sees only their own rows.
# Local mode (no secrets): a single-user SQLite file, handy for development.
def sb_url(): return (get_secret("SUPABASE_URL") or "").rstrip("/")
def sb_key(): return get_secret("SUPABASE_ANON_KEY") or get_secret("SUPABASE_KEY")
def sb_on(): return bool(sb_url() and sb_key())

def _auth_call(path, body, params=None):
    try:
        r = requests.post(f"{sb_url()}/auth/v1/{path}", params=params, json=body, timeout=15,
                          headers={"apikey": sb_key(), "Content-Type": "application/json"})
    except Exception as e:
        return None, f"Could not reach the server. Check your connection. ({e})"
    try: d = r.json() if r.text else {}
    except Exception: d = {}
    if r.status_code >= 400:
        return None, d.get("error_description") or d.get("msg") or d.get("message") or d.get("error") or f"Error {r.status_code}"
    return d, None

def _store_session(d):
    old = st.session_state.get("auth") or {}
    u = d.get("user") or {}
    st.session_state.auth = dict(access=d["access_token"], refresh=d.get("refresh_token") or old.get("refresh"),
                                 uid=u.get("id") or old.get("uid"), email=u.get("email") or old.get("email"),
                                 exp=time.time() + int(d.get("expires_in", 3600)))
    st.session_state["_c"] = {}
    if st.session_state.auth.get("refresh"): st.session_state["_cookie_op"] = ("set", st.session_state.auth["refresh"])

# Keep farmers signed in across browser refreshes: the (rotating) refresh token lives in a cookie for 30 days.
COOKIE = "farmai_rt"
def _run_js(js):
    js = f"/*{time.time_ns()}*/" + js          # unique text so the browser runs it every time
    try: st.html(f"<script>{js}</script>", unsafe_allow_javascript=True)
    except TypeError: components.html(f"<script>{js}</script>", height=0)      # older Streamlit

def flush_cookie():
    op = st.session_state.pop("_cookie_op", None)
    if not op: return
    base = "const D=(window.parent&&window.parent!==window?window.parent.document:document);"      # runs inside its own function scope
    if op[0] == "set":
        val = json.dumps(op[1]).replace("<", "\\u003c")
        _run_js("(function(){" + base + f'D.cookie="{COOKIE}="+encodeURIComponent({val})+"; max-age=2592000; path=/; SameSite=Lax"+(location.protocol==="https:"?"; Secure":"");' + "})();")
    else:
        _run_js("(function(){" + base + f'D.cookie="{COOKIE}=; max-age=0; path=/; SameSite=Lax";' + "})();")

def try_restore():
    """First run of a browser session: turn the saved cookie back into a signed-in session."""
    if "auth" in st.session_state or st.session_state.get("_restore_done"): return
    st.session_state["_restore_done"] = True
    try: rt = st.context.cookies.get(COOKIE)
    except Exception: rt = None
    if not rt: return
    d, err = _auth_call("token", {"refresh_token": urllib.parse.unquote(rt)}, {"grant_type": "refresh_token"})
    if d and d.get("access_token"): _store_session(d)
    else: st.session_state["_cookie_op"] = ("clear", None)

def sb_signin(email, pw):
    d, err = _auth_call("token", {"email": email, "password": pw}, {"grant_type": "password"})
    if err: return False, err
    _store_session(d); return True, ""

def sb_signup(email, pw):
    d, err = _auth_call("signup", {"email": email, "password": pw})
    if err: return False, err
    if d.get("access_token"): _store_session(d); return True, ""
    return False, "CONFIRM"

def sb_recover(email):
    _, err = _auth_call("recover", {"email": email})
    return err

def sb_signout():
    a = st.session_state.get("auth") or {}
    if a.get("access"):          # best effort: revoke the session on the server
        try: requests.post(f"{sb_url()}/auth/v1/logout", headers={"apikey": sb_key(), "Authorization": f"Bearer {a['access']}"}, timeout=10)
        except Exception: pass
    for k in ("auth", "_c", "chat", "pending"): st.session_state.pop(k, None)
    st.session_state["_cookie_op"] = ("clear", None)
    st.session_state.page = "Home"

def sb_token():
    """Valid access token, refreshed when close to expiry. None means the farmer must sign in again."""
    a = st.session_state.get("auth")
    if not a: return None
    if a["exp"] - time.time() < 60:
        d, err = _auth_call("token", {"refresh_token": a.get("refresh")}, {"grant_type": "refresh_token"}) if a.get("refresh") else (None, "x")
        if d and d.get("access_token"): _store_session(d); a = st.session_state.auth
        else: st.session_state.pop("auth", None); return None
    return a["access"]

def sb(method, table, params=None, body=None, prefer=None):
    """PostgREST call as the signed-in farmer (row-level security does the isolation). Returns None on failure."""
    tok = sb_token()
    if not tok: return None
    h = {"apikey": sb_key(), "Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
    if prefer: h["Prefer"] = prefer
    try:
        r = requests.request(method, f"{sb_url()}/rest/v1/{table}", headers=h, params=params, json=body, timeout=15)
        if r.status_code >= 400: raise RuntimeError(r.text[:200])
        return r.json() if r.text else []
    except Exception as e:
        st.error(f"Could not reach your farm data. Check your connection and try again. ({e})")
        return None

def _cached(key, fn, ttl=30):
    c = st.session_state.setdefault("_c", {})
    hit = c.get(key)
    if hit and time.time() - hit[0] < ttl: return hit[1]
    v = fn(); c[key] = (time.time(), v); return v
def _dirty(): st.session_state["_c"] = {}

def _db():
    c = sqlite3.connect("farmai.db")
    c.execute("create table if not exists history(ts text, kind text, summary text)")
    c.execute("create table if not exists plots(id integer primary key autoincrement, crop text, area real, soil text, planted text)")
    c.execute("create table if not exists task_done(plot_id integer, idx integer, primary key(plot_id, idx))")
    c.execute("create table if not exists ledger(id integer primary key autoincrement, d text, kind text, crop text, cat text, amount real, note text)")
    return c

def log(kind, summary):
    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    if sb_on(): sb("POST", "history", body={"ts": ts, "kind": kind, "summary": summary}, prefer="return=minimal")
    else:
        c = _db(); c.execute("insert into history values (?,?,?)", (ts, kind, summary)); c.commit(); c.close()
    _dirty()

def recent(n):
    def load():
        if sb_on():
            rows = sb("GET", "history", {"select": "ts,kind,summary", "order": "ts.desc,id.desc", "limit": n}) or []
            return [(r["ts"], r["kind"], r["summary"]) for r in rows]
        c = _db(); rows = c.execute("select ts, kind, summary from history order by ts desc limit ?", (n,)).fetchall(); c.close()
        return rows
    return _cached(f"recent{n}", load)

KIND_ICON = {"Disease": "🍃", "Crop": "🌱", "Yield": "📈", "Chat": "💬", "Calendar": "📅", "Ledger": "💰"}
def history_rows(rows):
    for ts, kind, s in rows:
        html(f'<div class="row"><div class="ic">{KIND_ICON.get(kind,"🌾")}</div><div class="tx">{esc(s)}<div class="tm">{esc(kind)} · {esc(ts)}</div></div></div>')

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
WMO = {0:("Clear","☀️"),1:("Mostly clear","🌤️"),2:("Partly cloudy","⛅"),3:("Cloudy","☁️"),45:("Fog","🌫️"),48:("Fog","🌫️"),
       51:("Drizzle","🌦️"),53:("Drizzle","🌦️"),55:("Drizzle","🌦️"),61:("Rain","🌧️"),63:("Rain","🌧️"),65:("Heavy rain","🌧️"),
       80:("Showers","🌦️"),81:("Showers","🌦️"),82:("Heavy showers","⛈️"),95:("Thunderstorm","⛈️"),96:("Thunderstorm","⛈️"),99:("Thunderstorm","⛈️")}

def fit(v, lo, hi):
    if lo <= v <= hi: return 1.0
    d = (lo - v) if v < lo else (v - hi)
    return max(0.0, 1 - d / ((hi - lo) or 1))

def factor_scores(c, soil, temp, rain, ph, n, p, k):
    return {"temperature": fit(temp,*c["temp"]), "rainfall": fit(rain,*c["rain"]), "soil pH": fit(ph,*c["ph"]),
            "nitrogen": fit(n,*c["n"]), "phosphorus": fit(p,*c["p"]), "potassium": fit(k,*c["k"]),
            "soil type": 1.0 if soil in c["soil"] else 0.4}

def suitability(c, soil, temp, rain, ph, n, p, k):
    s = list(factor_scores(c, soil, temp, rain, ph, n, p, k).values())
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

@st.cache_data(ttl=900, show_spinner=False)
def fetch_weather(city):
    g = requests.get("https://geocoding-api.open-meteo.com/v1/search", params={"name": city, "count": 1}, timeout=10).json()
    if not g.get("results"): return None
    loc = g["results"][0]
    w = requests.get("https://api.open-meteo.com/v1/forecast", params={
        "latitude": loc["latitude"], "longitude": loc["longitude"], "timezone": "auto", "forecast_days": 5,
        "current": "temperature_2m,relative_humidity_2m,weather_code",
        "daily": "temperature_2m_max,precipitation_probability_max,weather_code"}, timeout=10).json()
    return loc, w

# ---------------- Navigation ----------------
if "page" not in st.session_state: st.session_state.page = "Home"
if "chat" not in st.session_state: st.session_state.chat = []
if "pending" not in st.session_state: st.session_state.pending = None
if "lang" not in st.session_state: st.session_state.lang = "English"
def go(p): st.session_state.page = p
def ask(q): st.session_state.pending = q

def header(icon, title, sub):
    st.button("← Home", on_click=go, args=("Home",), key="back")
    html(f'<div class="ph"><div class="ph-ic">{icon}</div><div><div class="ph-t">{title}</div><div class="ph-s">{sub}</div></div></div>')

def tile(col, icon, title, desc, target, tint):
    with col:
        with st.container(border=True):
            html(f'<div class="tile-ic" style="background:{tint}">{icon}</div><div class="tile-t">{title}</div><div class="tile-d">{desc}</div>')
            st.button("Open", key=f"open_{target}", on_click=go, args=(target,))

LANGS = ["English", "Mandinka", "Wolof", "Fula"]
def lang_picker(k):
    st.session_state[k] = st.session_state.lang          # keep every copy of the picker in sync
    st.selectbox("Language", LANGS, key=k, on_change=lambda: st.session_state.update(lang=st.session_state[k]))
    if st.session_state.lang != "English":
        st.caption("Answers are translated by AI and may contain mistakes. Confirm important advice with your extension officer.")

page = st.session_state.page

# ---------------- Crop calendar ----------------
TASK_ICON = {"plant": "🌱", "weed": "🌿", "fert": "🧪", "spray": "💧", "water": "🚰", "harvest": "🧺"}
SCHEDULE = {  # (days after planting, task type, what to do)
    "Rice": [(0,"plant","Transplant seedlings into a levelled, puddled field"),(14,"weed","First weeding and fill gaps"),(21,"fert","Apply basal NPK"),
             (45,"fert","Top-dress with nitrogen at tillering"),(50,"weed","Second weeding, keep water about 5 cm deep"),(75,"spray","Scout for blast and stem borers"),
             (105,"water","Drain the field 10 days before harvest"),(120,"harvest","Harvest when most grains are golden")],
    "Maize": [(0,"plant","Plant seeds 25 cm apart in rows"),(10,"weed","Thin to one plant per stand and fill gaps"),(14,"weed","First weeding"),
              (21,"fert","Apply NPK basal dose"),(40,"fert","Top-dress with urea and earth up"),(45,"weed","Second weeding"),
              (60,"spray","Check whorls for fall armyworm"),(100,"harvest","Harvest when husks are dry")],
    "Tomato": [(0,"plant","Transplant seedlings and water well"),(10,"water","Stake plants and mulch the soil"),(14,"fert","Apply NPK after establishment"),
               (21,"weed","First weeding"),(35,"fert","Top-dress with potassium-rich fertiliser"),(40,"spray","Scout for early and late blight"),
               (60,"spray","Check for fruit borer and whitefly"),(90,"harvest","Start harvesting ripe fruit")],
    "Groundnut": [(0,"plant","Sow seeds 10 cm apart in rows"),(14,"weed","First weeding"),(30,"weed","Second weeding and light earthing up"),
                  (40,"fert","Apply gypsum at flowering"),(60,"spray","Scout for leaf spot and rosette virus"),
                  (100,"water","Stop watering and check pod maturity"),(110,"harvest","Lift plants and dry pods in the sun")],
    "Millet": [(0,"plant","Sow seeds in rows or hills"),(14,"weed","Thin seedlings and weed"),(21,"fert","Apply manure or NPK"),
               (40,"weed","Second weeding"),(60,"spray","Scout for downy mildew and stem borers"),(90,"harvest","Harvest when heads are hard and dry")],
    "Cassava": [(0,"plant","Plant stem cuttings in ridges or mounds"),(30,"weed","First weeding"),(60,"fert","Apply NPK rich in potassium"),
                (90,"weed","Second weeding"),(150,"spray","Scout for mosaic disease and mealybugs"),(270,"harvest","Harvest roots as leaves start to yellow")],
    "Sorghum": [(0,"plant","Sow seeds in rows"),(14,"weed","Thin to 2-3 plants per stand and weed"),(21,"fert","Apply NPK or manure"),
                (45,"weed","Second weeding"),(65,"spray","Scout for head bugs and shoot fly"),(95,"water","Protect heads from birds"),(110,"harvest","Harvest when grain is hard")],
    "Cowpea": [(0,"plant","Sow seeds in rows"),(14,"weed","First weeding"),(28,"spray","Check for aphids and pod borers"),
               (40,"weed","Second weeding"),(55,"spray","Spray if pod borers appear"),(70,"harvest","Harvest dry pods in batches")],
}

def add_plot(crop, area, soil, planted):
    if sb_on(): sb("POST", "plots", body={"crop": crop, "area": float(area), "soil": soil, "planted": planted.isoformat()}, prefer="return=minimal")
    else:
        c = _db(); c.execute("insert into plots(crop,area,soil,planted) values (?,?,?,?)", (crop, float(area), soil, planted.isoformat())); c.commit(); c.close()
    _dirty()
    log("Calendar", f"Added {crop} ({float(area):g} ha), planted {planted.strftime('%d %b %Y')}")
    st.toast(f"{crop} added to your crop calendar", icon="📅")

def get_plots():
    def load():
        if sb_on():
            rows = sb("GET", "plots", {"select": "id,crop,area,soil,planted", "order": "planted.desc,id.desc"}) or []
            return [dict(id=r["id"], crop=r["crop"], area=float(r["area"]), soil=r.get("soil") or "", planted=dt.date.fromisoformat(r["planted"])) for r in rows]
        c = _db(); rows = c.execute("select id,crop,area,soil,planted from plots order by planted desc").fetchall(); c.close()
        return [dict(id=i, crop=cr, area=a, soil=sl, planted=dt.date.fromisoformat(pl)) for i, cr, a, sl, pl in rows]
    return _cached("plots", load)

def _done_all():
    def load():
        out = {}
        if sb_on():
            for r in sb("GET", "task_done", {"select": "plot_id,idx"}) or []: out.setdefault(r["plot_id"], set()).add(r["idx"])
        else:
            c = _db()
            for pid, idx in c.execute("select plot_id, idx from task_done").fetchall(): out.setdefault(pid, set()).add(idx)
            c.close()
        return out
    return _cached("done", load)

def done_set(pid): return _done_all().get(pid, set())

def toggle_done(pid, idx):
    was = idx in done_set(pid)
    if sb_on():
        if was: sb("DELETE", "task_done", {"plot_id": f"eq.{pid}", "idx": f"eq.{idx}"})
        else: sb("POST", "task_done", body={"plot_id": pid, "idx": idx}, prefer="return=minimal,resolution=ignore-duplicates")
    else:
        c = _db()
        if was: c.execute("delete from task_done where plot_id=? and idx=?", (pid, idx))
        else: c.execute("insert or ignore into task_done values (?,?)", (pid, idx))
        c.commit(); c.close()
    _dirty()

def delete_plot(pid):
    if sb_on(): sb("DELETE", "plots", {"id": f"eq.{pid}"})      # task_done rows go with it (ON DELETE CASCADE)
    else:
        c = _db(); c.execute("delete from plots where id=?", (pid,)); c.execute("delete from task_done where plot_id=?", (pid,)); c.commit(); c.close()
    _dirty()

def plot_tasks(p):
    today = dt.date.today(); done = done_set(p["id"]); out = []
    for idx, (off, kind, text) in enumerate(SCHEDULE[p["crop"]]):
        due = p["planted"] + dt.timedelta(days=off)
        if idx in done or (kind == "plant" and due <= today): status = "done"
        elif due < today: status = "late"
        elif due <= today + dt.timedelta(days=2): status = "due"
        else: status = "up"
        out.append(dict(idx=idx, due=due, kind=kind, text=text, status=status))
    return out

def task_label(t):
    d = (t["due"] - dt.date.today()).days
    if t["status"] == "done": return "Done"
    if t["status"] == "late": return f"Overdue by {-d} day{'s' if d != -1 else ''}"
    if d == 0: return "Due today"
    if d == 1: return "Due tomorrow"
    return f"{t['due'].strftime('%a %d %b')} (in {d} days)"

def task_row(t, warn=""):
    w = f'<div class="warn">{warn}</div>' if warn else ""
    return f'<div class="tk {t["status"]}"><b>{TASK_ICON.get(t["kind"],"🌾")} {esc(t["text"])}</b><small>{task_label(t)}</small>{w}</div>'

def next_tasks(limit=3):
    today = dt.date.today(); out = []
    for p in get_plots():
        for t in plot_tasks(p):
            if t["status"] in ("late", "due") or (t["status"] == "up" and (t["due"] - today).days <= 7): out.append((p["crop"], t))
    out.sort(key=lambda x: x[1]["due"]); return out[:limit]

def rain_soon(city):
    try:
        d = fetch_weather(city)
        return bool(d) and max(d[1]["daily"]["precipitation_probability_max"][:3]) >= 60
    except Exception:
        return False

# ---------------- AI vision + diagnosis card ----------------
@st.cache_data(ttl=86400, show_spinner=False)
def translate_texts(texts, lang):
    """Translate a tuple of strings into `lang` with Gemini. Falls back to the originals on any problem."""
    texts = list(texts); key = get_secret("GEMINI_API_KEY")
    if lang == "English" or not key or not texts: return texts
    prompt = (f"Translate every string in this JSON array into {lang} as spoken in The Gambia, in simple farmer-friendly words. "
              "Keep crop, chemical and place names recognisable. Reply with a JSON array of the same length and order, nothing else.\n"
              + json.dumps(texts, ensure_ascii=False))
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2}}
    model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    try:
        r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", params={"key": key}, json=body, timeout=60)
        txt = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        out = json.loads(re.sub(r"^```(?:json)?|```$", "", txt.strip(), flags=re.M).strip())
        return [str(x) for x in out] if isinstance(out, list) and len(out) == len(texts) else texts
    except Exception:
        return texts

# ---------------- Voice: speech to text (Gemini) and read-aloud (browser) ----------------
def gemini_transcribe(raw, mime="audio/wav"):
    key = get_secret("GEMINI_API_KEY")
    if not key: return None, "Add GEMINI_API_KEY in .streamlit/secrets.toml to use voice input."
    prompt = ("Transcribe this audio exactly as spoken. The speaker is a farmer in The Gambia and may speak English, Mandinka, Wolof or Fula. "
              f"They have chosen {st.session_state.get('lang', 'English')}. If they speak a local language, write it as spoken. "
              "Reply with the transcript only. If there is no speech, reply with exactly NO_SPEECH.")
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}, {"inline_data": {"mime_type": mime, "data": base64.b64encode(raw).decode()}}]}],
            "generationConfig": {"temperature": 0}}
    model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    try:
        r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", params={"key": key}, json=body, timeout=60)
        data = r.json()
        if not (data.get("candidates") and data["candidates"][0].get("content")):
            return None, "Gemini error: " + (data.get("error", {}).get("message") or str(data)[:200])
        txt = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        if not txt or txt == "NO_SPEECH": return None, "I could not hear anything. Hold the phone closer and try again."
        return txt, None
    except Exception as e:
        return None, f"Could not process the recording ({e})."

TTS_LANG = {"English": "en", "Wolof": "wo", "Mandinka": "mnk", "Fula": "ff"}
def speak_button(text):
    """Browser read-aloud button (no API cost). Works offline on most phones."""
    lang_name = st.session_state.get("lang", "English")
    clean = re.sub(r"[*_#`>]", "", str(text)).strip()
    if not clean: return
    payload = json.dumps(clean).replace("<", "\\u003c").replace(">", "\\u003e")   # ASCII-only, no tag characters
    doc = (f"""<style>
body{{margin:0;font-family:system-ui,sans-serif}}
button{{background:#E4F0E8;color:#12503A;border:1px solid #CFE0D4;border-radius:10px;padding:.45rem .9rem;font-weight:700;font-size:.9rem;cursor:pointer}}
button:hover{{background:#D3E8DA}} button:focus-visible{{outline:3px solid #E3A72F}} span{{font-size:.8rem;color:#5B6B61;margin-left:.6rem}}
</style><button id="b">🔊 Listen</button><span id="m"></span>
<script>
const T={payload}, L="{TTS_LANG.get(lang_name, 'en')}", N="{lang_name}";
const b=document.getElementById('b'), m=document.getElementById('m'); let on=false;
const reset=()=>{{on=false;b.textContent='🔊 Listen';}};
b.onclick=()=>{{
  if(!('speechSynthesis' in window)){{m.textContent='Read-aloud is not supported on this browser.';return;}}
  if(on){{speechSynthesis.cancel();reset();return;}}
  const v=speechSynthesis.getVoices().find(x=>x.lang.toLowerCase().startsWith(L));
  if(!v && L!=='en'){{m.textContent='No '+N+' voice on this device. Switch to English to listen.';return;}}
  const u=new SpeechSynthesisUtterance(T); if(v){{u.voice=v;u.lang=v.lang;}} u.rate=.92; u.onend=reset; u.onerror=reset;
  speechSynthesis.cancel(); speechSynthesis.speak(u); on=true; b.textContent='⏹ Stop'; m.textContent='';
}};
speechSynthesis.getVoices();
</script>""")
    try:
        components.html(doc, height=52)
    except Exception:   # newer Streamlit versions removed components.html
        st.iframe("data:text/html;base64," + base64.b64encode(doc.encode()).decode(), height=52)

def gemini_diagnose(img):
    key = get_secret("GEMINI_API_KEY")
    if not key: return None, "Add GEMINI_API_KEY in .streamlit/secrets.toml to use AI vision."
    im = img.copy(); im.thumbnail((768, 768)); buf = io.BytesIO(); im.save(buf, "JPEG", quality=85)
    prompt = ("You are a plant pathologist helping smallholder farmers in The Gambia and West Africa. Look at this leaf photo and identify the crop and any disease, pest or nutrient problem. "
              "Reply with JSON only, with keys: is_plant (bool), crop (string), condition (string, 'Healthy' if none), healthy (bool), confidence (number 0 to 1), "
              "cause (one short sentence), treatment (list of up to 5 short, low-cost steps using locally available materials), prevention (list of up to 3 short tips). "
              "If you are unsure, lower the confidence and say so in the cause.")
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}, {"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(buf.getvalue()).decode()}}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2}}
    model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    try:
        r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", params={"key": key}, json=body, timeout=60)
        data = r.json()
        if not (data.get("candidates") and data["candidates"][0].get("content")):
            return None, "Gemini error: " + (data.get("error", {}).get("message") or str(data)[:200])
        text = re.sub(r"^```(?:json)?|```$", "", data["candidates"][0]["content"]["parts"][0]["text"].strip(), flags=re.M).strip()
        return json.loads(text), None
    except Exception as e:
        return None, f"AI vision could not analyze the photo ({e})."

def render_diag(name, cause, steps, conf, healthy, source, prevention=()):
    steps, prevention = list(steps), list(prevention)
    L = ["Cause", "Treatment", "Care steps", "Prevention", "Confidence", "Healthy", "Disease detected"]
    lang = st.session_state.get("lang", "English")
    if lang != "English":
        n = len(steps); t = translate_texts(tuple(L + [cause] + steps + prevention), lang)
        L, cause, steps, prevention = list(t[:7]), t[7], list(t[8:8 + n]), list(t[8 + n:])
    badge = f'<span class="badge b-ok">{esc(L[5])}</span>' if healthy else f'<span class="badge b-bad">{esc(L[6])}</span>'
    col = level_color(conf)
    li = "".join(f"<li><b>{i}</b><span>{esc(x)}</span></li>" for i, x in enumerate(steps, 1))
    pv = ""
    if prevention:
        pv = f'<div class="lbl">{esc(L[3])}</div><ul class="steps">' + "".join(f"<li><b>{i}</b><span>{esc(x)}</span></li>" for i, x in enumerate(prevention, 1)) + "</ul>"
    html(f'<div class="card">{badge} <span class="badge b-warn">{esc(source)}</span><div class="res-t">{esc(name)}</div><div class="res-c">{esc(L[0])}: {esc(cause)}</div>'
         f'<div class="conf"><span>{esc(L[4])}</span><span style="color:{col}">{conf*100:.1f}%</span></div>{bar(conf, col)}'
         f'<div class="lbl">{esc(L[2] if healthy else L[1])}</div><ul class="steps">{li}</ul>{pv}</div>')
    speak_button(f"{name}. {L[0]}: {cause}. " + " ".join(f"{i}. {x}" for i, x in enumerate(steps, 1)))

# ---------------- Ledger ----------------
COST_CATS = ["Seeds", "Fertiliser", "Pesticide", "Labour", "Tools", "Transport", "Other"]
SALE_CATS = ["Harvest sale", "Other income"]
def money(x): return f"D{x:,.0f}"
def add_entry(kind, crop, cat, amount, note, d):
    if sb_on():
        sb("POST", "ledger", body={"d": d.isoformat(), "kind": kind, "crop": crop, "cat": cat, "amount": float(amount), "note": note.strip()}, prefer="return=minimal")
    else:
        c = _db(); c.execute("insert into ledger(d,kind,crop,cat,amount,note) values (?,?,?,?,?,?)",
                             (d.isoformat(), kind, crop, cat, float(amount), note.strip())); c.commit(); c.close()
    _dirty()
    log("Ledger", f"{'Sale' if kind == 'sale' else 'Cost'} {money(amount)}: {crop} {cat.lower()}")

def get_entries():
    def load():
        if sb_on():
            rows = sb("GET", "ledger", {"select": "id,d,kind,crop,cat,amount,note", "order": "d.desc,id.desc"}) or []
            return [dict(id=r["id"], d=dt.date.fromisoformat(r["d"]), kind=r["kind"], crop=r["crop"], cat=r["cat"], amount=float(r["amount"]), note=r.get("note") or "") for r in rows]
        c = _db(); rows = c.execute("select id,d,kind,crop,cat,amount,note from ledger order by d desc, id desc").fetchall(); c.close()
        return [dict(id=i, d=dt.date.fromisoformat(d), kind=k, crop=cr, cat=ct, amount=a, note=n) for i, d, k, cr, ct, a, n in rows]
    return _cached("ledger", load)

def del_entry(eid):
    if sb_on(): sb("DELETE", "ledger", {"id": f"eq.{eid}"})
    else:
        c = _db(); c.execute("delete from ledger where id=?", (eid,)); c.commit(); c.close()
    _dirty()

# ---------------- Sign-in screen (cloud mode only) ----------------
def login_screen():
    html('<div class="hero"><div class="hero-date">Welcome</div><div class="hero-h">FarmAI</div>'
         '<div class="hero-p">Sign in to keep your fields, tasks and farm accounts safe and available on any phone.</div></div>')
    t_in, t_up = st.tabs(["Sign in", "Create account"])
    with t_in:
        with st.form("login_form"):
            e = st.text_input("Email", key="li_email"); p = st.text_input("Password", type="password", key="li_pw")
            go_in = st.form_submit_button("Sign in")
        if go_in:
            if not e.strip() or not p: st.warning("Enter your email and password.")
            else:
                ok, msg = sb_signin(e.strip(), p)
                if ok: st.rerun()
                else: st.error(msg)
        with st.expander("Forgot your password?"):
            fe = st.text_input("Email for the reset link", key="fp_email")
            if st.button("Send reset link", key="fp_go"):
                err = sb_recover(fe.strip()) if fe.strip() else "Enter your email first."
                st.error(err) if err else st.success("Check your email for the reset link.")
    with t_up:
        with st.form("signup_form"):
            e2 = st.text_input("Email", key="su_email"); p2 = st.text_input("Password (at least 6 characters)", type="password", key="su_pw")
            p3 = st.text_input("Repeat password", type="password", key="su_pw2")
            go_up = st.form_submit_button("Create account")
        if go_up:
            if not e2.strip() or len(p2) < 6: st.warning("Enter your email and a password with at least 6 characters.")
            elif p2 != p3: st.warning("The two passwords do not match.")
            else:
                ok, msg = sb_signup(e2.strip(), p2)
                if ok: st.rerun()
                elif msg == "CONFIRM": st.success("Account created. Check your email to confirm it, then sign in.")
                else: st.error(msg)

if sb_on():
    try_restore()
if sb_on() and not sb_token():
    login_screen()
    flush_cookie()
    st.stop()

# ---------------- Sidebar ----------------
NAV = [("🏠", "Home", "Home"), ("🍃", "Disease Detection", "Disease Detection"), ("🌱", "Crop Recommendation", "Crop Recommendation"),
       ("⛅", "Weather Forecast", "Weather Forecast"), ("📈", "Yield Prediction", "Yield Prediction"), ("📅", "Crop Calendar", "Crop Calendar"),
       ("💰", "Season Ledger", "Season Ledger"), ("💬", "Ask AI", "Ask Farming AI"), ("🕘", "History", "History")]
with st.sidebar:
    html('<div class="sb-brand"><div class="sb-logo">🌾</div><div><div class="sb-name">FarmAI</div><div class="sb-tag">Smart farming for The Gambia</div></div></div>')
    for ic, target, label in NAV:
        st.button(f"{ic}  {label}", key=f"nav_{target}", on_click=go, args=(target,), type="primary" if page == target else "secondary")
    html('<div class="sb-sep"></div>')
    if sb_on():
        _em = st.session_state.auth.get("email") or "Signed in"
        html(f'<div class="sb-user"><div class="sb-av">{esc(_em[:1].upper())}</div><div class="sb-em">{esc(_em)}</div></div>')
        st.button("Sign out", key="signout", on_click=sb_signout)
    lang_picker("lang_side")
    _ents = get_entries(); _profit = sum(e["amount"] if e["kind"] == "sale" else -e["amount"] for e in _ents)
    html(f'<div class="sb-stats"><div><b>{len(get_plots())}</b>Plots</div><div><b>{"-" if _profit < 0 else ""}{money(abs(_profit))}</b>Profit</div></div>')
    html('<div class="sb-foot">AI advice is an estimate. Confirm with your local agriculture extension officer before buying chemicals.</div>')

# ---------------- Mobile bottom tab bar (hidden on desktop by CSS) ----------------
TABS = [("🏠", "Home", "Home"), ("🍃", "Disease Detection", "Scan"), ("📅", "Crop Calendar", "Calendar"), ("💬", "Ask AI", "Chat")]
with st.container(key="tabbar"):
    for col, (ic, target, label) in zip(st.columns(len(TABS)), TABS):
        col.button(f"{ic} {label}", key=f"tab_{target}", on_click=go, args=(target,), type="primary" if page == target else "secondary")

# ---------------- Pages ----------------
if page == "Home":
    now = dt.datetime.now()
    greet = "Good morning" if now.hour < 12 else "Good afternoon" if now.hour < 17 else "Good evening"
    html(f'<div class="hero"><div class="hero-date">{now.strftime("%A, %d %B")}</div>'
         f'<div class="hero-h">{greet}, Farmer</div>'
         f'<div class="hero-p">Check a sick plant, choose what to grow, or ask for advice. Everything for your farm in one place.</div></div>')
    lang_picker("lang_home")
    r1 = st.columns(2); r2 = st.columns(2); r3 = st.columns(2); r4 = st.columns(2)
    tile(r1[0], "🍃", "Disease Detection", "Scan a leaf of any crop and get treatment steps.", "Disease Detection", "#DDF1E3")
    tile(r1[1], "🌱", "Crop Recommendation", "Find the best crops for your soil and climate.", "Crop Recommendation", "#FBEFCF")
    tile(r2[0], "⛅", "Weather Forecast", "5-day outlook with farming advice.", "Weather Forecast", "#DCEBF7")
    tile(r2[1], "📈", "Yield Prediction", "Estimate harvest size and date.", "Yield Prediction", "#F3E2D3")
    tile(r3[0], "📅", "Crop Calendar", "Tasks, reminders and rain alerts for each field.", "Crop Calendar", "#DDEFE9")
    tile(r3[1], "💬", "Ask Farming AI", "Get answers to any farming question.", "Ask AI", "#E6E0F5")
    tile(r4[0], "💰", "Season Ledger", "Track costs, sales and profit per crop.", "Season Ledger", "#F6EBC8")
    tile(r4[1], "🕘", "History", "Review your past scans and plans.", "History", "#E4E8E2")
    due = next_tasks(3)
    if due:
        html('<div class="sec">On your farm this week</div>')
        for crop_name, t in due:
            html(f'<div class="row"><div class="ic">{TASK_ICON.get(t["kind"],"🌾")}</div><div class="tx">{esc(t["text"])}<div class="tm">{esc(crop_name)} · {task_label(t)}</div></div></div>')
    rows = recent(3)
    if rows:
        html('<div class="sec">Recent activity</div>')
        history_rows(rows)

elif page == "Disease Detection":
    header("🍃", "Disease Detection", "Upload or capture one leaf. Works for tomato, potato, apple and, with AI vision, any other crop.")
    lang_picker("lang_dis")
    f = st.file_uploader("Leaf photo", type=["jpg", "jpeg", "png"])
    cam = st.camera_input("Take a photo") if st.toggle("Use camera instead") else None
    f = f or cam
    if f:
        img = Image.open(f).convert("RGB")
        st.image(img, use_container_width=True)
        model = load_model()
        b1, b2 = st.columns(2)
        run_local = b1.button("Analyze leaf", type="primary", key="an_local")
        run_ai = b2.button("Other crop? Use AI", key="an_ai")
        if run_local or run_ai:
            local_conf = None
            if run_local and model is not None:
                with st.spinner("Analyzing leaf..."):
                    x = np.expand_dims(np.array(img.resize((224, 224))).astype("float32") / 255.0, 0)
                    pred = model.predict(x, verbose=0)[0]
                    labels = load_labels()
                    top = np.argsort(pred)[::-1][:3]
                    raw = labels.get(int(top[0]), "Unknown"); local_conf = float(pred[top[0]])
                name, cause, steps = SOLUTIONS.get(raw, (raw.replace("___", " – ").replace("_", " "),
                    "Healthy, or a disease not yet in the solutions list.",
                    ["Monitor the plant weekly.", "Keep regular watering and feeding.", "Ask the AI chat for advice if symptoms appear."]))
                render_diag(name, cause, steps, local_conf, raw.lower().endswith("healthy"), "Local model")
                alts = "".join(f'<div class="alt"><span>{esc(labels.get(int(i), i))}</span><span>{pred[i]*100:.1f}%</span></div>' for i in top[1:])
                with st.expander("Other possibilities"):
                    html(alts)
                log("Disease", f"{name} ({local_conf*100:.0f}%)")
            if run_ai or model is None or (local_conf is not None and local_conf < 0.6):
                if model is None and run_local:
                    html('<div class="tip">The local model was not found, so AI vision is analyzing this leaf.</div>')
                elif local_conf is not None:
                    html('<div class="tip">The local model is unsure, so AI vision is taking a second look.</div>')
                with st.spinner("AI vision is analyzing the leaf..."):
                    d, err = gemini_diagnose(img)
                if err:
                    st.error(err)
                elif not d.get("is_plant", True):
                    st.warning("This does not look like a plant leaf. Retake the photo with one leaf filling the frame.")
                else:
                    try: conf = max(0.0, min(1.0, float(d.get("confidence", 0.7))))
                    except Exception: conf = 0.7
                    name = f'{d.get("crop", "Plant")}: {d.get("condition", "Unknown")}'
                    steps = [str(x) for x in (d.get("treatment") or ["Monitor the plant weekly and ask the AI chat for advice."])]
                    render_diag(name, d.get("cause", "Not determined"), steps, conf, bool(d.get("healthy")), "AI vision", [str(x) for x in (d.get("prevention") or [])])
                    if conf < 0.6:
                        html('<div class="tip">Low confidence. Retake the photo in good light, or show it to your local extension officer.</div>')
                    log("Disease", f"{name} ({conf*100:.0f}%, AI)")

elif page == "Crop Recommendation":
    header("🌱", "Crop Recommendation", "Enter your field conditions to see what grows best.")
    with st.container(border=True):
        soil = st.selectbox("Soil type", ["Loamy", "Sandy", "Clay", "Silty"])
        c1, c2 = st.columns(2)
        temp = c1.number_input("Temperature (°C)", 5.0, 45.0, 30.0)
        rain = c2.number_input("Rainfall (mm / month)", 0.0, 500.0, 120.0)
        ph = c1.number_input("Soil pH", 3.5, 9.5, 6.5)
        n = c2.number_input("Nitrogen (N)", 0, 200, 90)
        p = c1.number_input("Phosphorus (P)", 0, 200, 40)
        k = c2.number_input("Potassium (K)", 0, 200, 50)
    if st.button("Get recommendation", type="primary"):
        res = sorted(((suitability(c, soil, temp, rain, ph, n, p, k), name) for name, c in CROPS.items()), reverse=True)[:3]
        html('<div class="sec">Best crops for your field</div>')
        for i, (s, name) in enumerate(res, 1):
            c = CROPS[name]
            fs = factor_scores(c, soil, temp, rain, ph, n, p, k)
            weak = min(fs, key=fs.get)
            why = "All conditions are in the ideal range." if fs[weak] >= 1 else f"Weakest factor: {weak}."
            html(f'<div class="card rank {"first" if i == 1 else ""}"><div class="rank-e">{c["e"]}</div><div class="rank-b">'
                 f'<div class="rank-n"><div>{"🥇 " if i == 1 else ""}{name}</div><span>{s*100:.0f}%</span></div>{bar(s, level_color(s))}'
                 f'<div class="rank-w">{why}</div></div></div>')
        log("Crop", f"Top: {res[0][1]} ({res[0][0]*100:.0f}%)")

elif page == "Weather Forecast":
    header("⛅", "Weather Forecast", "Plan spraying, planting and harvest around the weather.")
    city = st.text_input("Location", "Banjul")
    try:
        data = fetch_weather(city)
        if not data:
            st.warning("Location not found. Check the spelling and try again.")
        else:
            loc, w = data
            cur, day = w["current"], w["daily"]
            cond, ico = WMO.get(cur["weather_code"], ("—", "🌡️"))
            html(f'<div class="wx"><div class="wx-loc">{esc(loc["name"])}, {esc(loc.get("country",""))}</div>'
                 f'<div class="wx-main"><div class="wx-temp">{cur["temperature_2m"]:.0f}°C</div><div class="wx-cond">{ico} {cond}</div></div>'
                 f'<div class="wx-row"><div><b>{cur["relative_humidity_2m"]}%</b>Humidity</div>'
                 f'<div><b>{day["precipitation_probability_max"][0]}%</b>Rain chance today</div></div></div>')
            cards = ""
            for t, mx, pr, wc in zip(day["time"], day["temperature_2m_max"], day["precipitation_probability_max"], day["weather_code"]):
                cards += (f'<div><div class="d">{dt.date.fromisoformat(t).strftime("%a %d")}</div><div class="i">{WMO.get(wc,("—","🌡️"))[1]}</div>'
                          f'<div class="t">{mx:.0f}°</div><div class="r">💧 {pr}%</div></div>')
            html('<div class="sec">Next 5 days</div>')
            html(f'<div class="fc">{cards}</div>')
            rainy = max(day["precipitation_probability_max"][:3])
            tip = ("<b>Rain likely soon.</b> Delay spraying and fertiliser, and prepare drainage." if rainy >= 60
                   else "<b>Mostly dry.</b> Good time for spraying, weeding and harvesting. Check irrigation.")
            html(f'<div class="tip">{tip}</div>')
    except Exception as e:
        st.error(f"Could not load weather. Check your internet connection. ({e})")

elif page == "Yield Prediction":
    header("📈", "Yield Prediction", "Estimate how much you can harvest and when.")
    with st.container(border=True):
        crop = st.selectbox("Crop", list(CROPS))
        soil = st.selectbox("Soil type", ["Loamy", "Sandy", "Clay", "Silty"])
        a1, a2 = st.columns(2)
        area = a1.number_input("Farm size (hectares)", 0.1, 1000.0, 1.0)
        plant = a2.date_input("Planting date", dt.date.today())
        c1, c2 = st.columns(2)
        temp = c1.number_input("Avg temperature (°C)", 5.0, 45.0, 30.0)
        rain = c2.number_input("Rainfall (mm / month)", 0.0, 500.0, 120.0)
        ph = c1.number_input("Soil pH", 3.5, 9.5, 6.5)
        n = c2.number_input("Nitrogen (N)", 0, 200, 90)
        p = c1.number_input("Phosphorus (P)", 0, 200, 40)
        k = c2.number_input("Potassium (K)", 0, 200, 50)
    if st.button("Predict yield", type="primary"):
        c = CROPS[crop]; s = suitability(c, soil, temp, rain, ph, n, p, k)
        per_ha = c["y"] * (0.4 + 0.7 * s)
        harvest = plant + dt.timedelta(days=c["d"])
        html(f'<div class="stats">'
             f'<div class="stat hi"><small>Total for your farm</small><div class="v">{per_ha*area:.1f} t</div><div class="s">on {area:g} ha</div></div>'
             f'<div class="stat"><small>Expected yield</small><div class="v">{per_ha:.1f} t/ha</div><div class="s">range {per_ha*0.8:.1f} – {per_ha*1.2:.1f}</div></div>'
             f'<div class="stat"><small>Estimated harvest</small><div class="v">{harvest.strftime("%d %b %Y")}</div><div class="s">{c["d"]} days after planting</div></div></div>')
        html(f'<div class="card"><div class="conf"><span>{c["e"]} {crop}: growing-condition match</span><span style="color:{level_color(s)}">{s*100:.0f}%</span></div>{bar(s, level_color(s))}'
             f'<div class="note">This is an estimate from typical crop data, not a trained model.</div></div>')
        log("Yield", f"{crop}: {per_ha*area:.1f} t on {area} ha")

    st.button("📅 Save to crop calendar", on_click=add_plot, args=(crop, area, soil, plant), key="save_plot")

elif page == "Crop Calendar":
    header("📅", "Crop Calendar", "Track every field and never miss a task.")
    plots = get_plots()
    loc = st.text_input("Farm location (for rain alerts)", "Banjul", key="farm_loc")
    rainy = rain_soon(loc)
    with st.expander("➕ Add a field", expanded=not plots):
        cc = st.selectbox("Crop", list(CROPS), key="cal_crop")
        c1, c2 = st.columns(2)
        csoil = c1.selectbox("Soil type", ["Loamy", "Sandy", "Clay", "Silty"], key="cal_soil")
        carea = c2.number_input("Farm size (hectares)", 0.1, 1000.0, 1.0, key="cal_area")
        cdate = st.date_input("Planting date", dt.date.today(), key="cal_date")
        st.button("Add to calendar", type="primary", on_click=add_plot, args=(cc, carea, csoil, cdate), key="cal_add")
    if not plots:
        html('<div class="card" style="text-align:center"><div style="font-size:2rem">📅</div><div class="res-t" style="font-size:1.2rem">No fields yet</div>'
             '<div class="res-c">Add a crop and its planting date. FarmAI will list weeding, fertiliser, spraying and harvest dates for you.</div></div>')
    if rainy and plots:
        html('<div class="tip"><b>Rain likely in the next 3 days.</b> Spraying and fertiliser tasks that are due now should wait until the field dries.</div>')
    today = dt.date.today()
    for p in plots:
        c = CROPS[p["crop"]]; tasks = plot_tasks(p)
        elapsed = (today - p["planted"]).days
        prog = max(0.0, min(1.0, elapsed / c["d"]))
        harvest = p["planted"] + dt.timedelta(days=c["d"])
        stage = f"Starts in {-elapsed} days" if elapsed < 0 else f"Day {elapsed} of {c['d']}" if elapsed < c["d"] else "Ready to harvest"
        with st.container(border=True):
            html(f'<div class="pl"><div><div class="pl-n">{c["e"]} {esc(p["crop"])}</div><div class="pl-m">{p["area"]:g} ha · {esc(p["soil"])} · planted {p["planted"].strftime("%d %b %Y")}</div></div>'
                 f'<span class="badge b-ok">{stage}</span></div>{bar(prog, "#1F8A4C")}'
                 f'<div class="note">Harvest around {harvest.strftime("%d %b %Y")}</div>')
            pending = [t for t in tasks if t["status"] != "done"]
            if not pending:
                html('<div class="tip">All tasks are complete. Time to enjoy the harvest! 🎉</div>')
            for t in pending[:4]:
                warn = "Rain is likely. Delay this until the field is dry." if rainy and t["kind"] in ("spray", "fert") and t["status"] in ("late", "due") else ""
                a, b = st.columns([4, 1])
                with a: html(task_row(t, warn))
                b.button("✓ Done", key=f"d{p['id']}_{t['idx']}", on_click=toggle_done, args=(p["id"], t["idx"]))
            with st.expander("Full schedule"):
                for t in tasks: html(task_row(t))
            st.button("Remove field", key=f"rm{p['id']}", on_click=delete_plot, args=(p["id"],))

elif page == "Season Ledger":
    header("💰", "Season Ledger", "Track what you spend and earn on each crop. Amounts are in dalasi (D).")
    entries = get_entries()
    costs = sum(e["amount"] for e in entries if e["kind"] == "cost")
    sales = sum(e["amount"] for e in entries if e["kind"] == "sale")
    profit = sales - costs
    pcol = "#fff" if profit >= 0 else "#FFC9BC"
    html(f'<div class="stats"><div class="stat hi"><small>Profit</small><div class="v" style="color:{pcol}">{"-" if profit < 0 else ""}{money(abs(profit))}</div><div class="s">sales minus costs</div></div>'
         f'<div class="stat"><small>Sales</small><div class="v">{money(sales)}</div></div>'
         f'<div class="stat"><small>Costs</small><div class="v">{money(costs)}</div></div></div>')

    with st.expander("➕ Add an entry", expanded=not entries):
        kind_l = st.radio("Type", ["Cost", "Sale"], horizontal=True, key="le_kind")
        c1, c2 = st.columns(2)
        crop_e = c1.selectbox("Crop", list(CROPS) + ["General farm"], key="le_crop")
        cat = c2.selectbox("Category", COST_CATS if kind_l == "Cost" else SALE_CATS, key="le_cat")
        c3, c4 = st.columns(2)
        amt = c3.number_input("Amount (D)", 0.0, 10_000_000.0, 0.0, step=50.0, key="le_amt")
        ed = c4.date_input("Date", dt.date.today(), key="le_date")
        note = st.text_input("Note (optional)", key="le_note", placeholder="e.g. 2 bags NPK from Serrekunda market")
        if st.button("Save entry", type="primary", key="le_save"):
            if amt <= 0: st.warning("Enter an amount greater than 0.")
            else:
                add_entry("cost" if kind_l == "Cost" else "sale", crop_e, cat, amt, note, ed); st.rerun()

    if not entries:
        html('<div class="card" style="text-align:center"><div style="font-size:2rem">💰</div><div class="res-t" style="font-size:1.2rem">No entries yet</div>'
             '<div class="res-c">Record seed, labour and fertiliser costs, then your harvest sales, to see profit per crop.</div></div>')
    else:
        per = {}
        for e in entries:
            d = per.setdefault(e["crop"], dict(sales=0.0, costs=0.0))
            d["sales" if e["kind"] == "sale" else "costs"] += e["amount"]
        html('<div class="sec">Profit by crop</div>')
        for cname, d in sorted(per.items(), key=lambda x: x[1]["sales"] - x[1]["costs"], reverse=True):
            pr = d["sales"] - d["costs"]
            ha = sum(p["area"] for p in get_plots() if p["crop"] == cname)
            perha = f" · {'-' if pr < 0 else ''}{money(abs(pr) / ha)}/ha" if ha else ""
            clr = "#17703A" if pr >= 0 else "#A63A22"
            ic = CROPS[cname]["e"] if cname in CROPS else "🌾"
            html(f'<div class="row"><div class="ic">{ic}</div><div class="tx">{esc(cname)} · <span style="color:{clr}">{"-" if pr < 0 else "+"}{money(abs(pr))}</span>'
                 f'<div class="tm">Sales {money(d["sales"])} · Costs {money(d["costs"])}{perha}</div></div></div>')
        html('<div class="sec">Recent entries</div>')
        for e in entries[:30]:
            sale = e["kind"] == "sale"
            cc, cx = st.columns([6, 1])
            with cc:
                html(f'<div class="row"><div class="ic">{"📥" if sale else "📤"}</div><div class="tx">{esc(e["cat"])} · {esc(e["crop"])} · '
                     f'<span style="color:{"#17703A" if sale else "#A63A22"}">{"+" if sale else "-"}{money(e["amount"])}</span>'
                     f'<div class="tm">{e["d"].strftime("%d %b %Y")}{" · " + esc(e["note"]) if e["note"] else ""}</div></div></div>')
            cx.button("✕", key=f"le_del{e['id']}", on_click=del_entry, args=(e["id"],))

elif page == "Ask AI":
    header("💬", "Farming AI", "Ask about pests, soil, planting or harvest.")
    SYS = ("You are FarmAI, a practical farming assistant for smallholder farmers in The Gambia and West Africa. "
           "Give short, clear answers with numbered possible causes and simple steps. Prefer low-cost, locally available solutions. "
           "If unsure, say so and suggest visiting the local agriculture extension officer.")
    key = get_secret("GEMINI_API_KEY")
    if not key: st.info("Add GEMINI_API_KEY in .streamlit/secrets.toml to enable the AI chat.")
    lang_picker("lang_chat")
    if st.session_state.lang != "English":
        SYS += f" Always reply in {st.session_state.lang} using simple words. If you are not confident in {st.session_state.lang}, add a short English version after it."
    if not st.session_state.chat:
        html('<div class="lbl">Try asking</div>')
        for i, sug in enumerate(["Why are my groundnut leaves turning yellow?", "When is the best time to plant millet?", "How can I improve sandy soil cheaply?"]):
            st.button(sug, key=f"sug{i}", on_click=ask, args=(sug,))
    voice_q = None
    if hasattr(st, "audio_input"):
        with st.expander("🎤 Ask by voice"):
            au = st.audio_input("Record your question", key="mic")
            if au is not None:
                raw = au.getvalue(); h = hashlib.md5(raw).hexdigest()
                if st.session_state.get("last_mic") != h:
                    st.session_state.last_mic = h
                    with st.spinner("Listening..."):
                        txt, err = gemini_transcribe(raw)
                    if err: st.error(err)
                    else: voice_q = txt
    else:
        st.caption("Update Streamlit to 1.40 or newer to ask by voice.")
    for m in st.session_state.chat:
        with st.chat_message("user" if m["role"] == "user" else "assistant"):
            st.write(m["text"])
            if m["role"] != "user": speak_button(m["text"])
    q = st.chat_input("Type your question…") or voice_q or st.session_state.pending
    st.session_state.pending = None
    if q and key:
        st.session_state.chat.append({"role": "user", "text": q}); st.chat_message("user").write(q)
        model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
        body = {"system_instruction": {"parts": [{"text": SYS}]},
                "contents": [{"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["text"]}]} for m in st.session_state.chat[-10:]]}
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
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
            st.write(ans)
            speak_button(ans)
        st.session_state.chat.append({"role": "model", "text": ans})
        log("Chat", q[:80])
    if st.session_state.chat:
        st.button("Clear conversation", on_click=lambda: st.session_state.update(chat=[]), key="clear")

elif page == "History":
    header("🕘", "History", "Your latest scans, plans and questions.")
    rows = recent(50)
    if not rows:
        html('<div class="card" style="text-align:center"><div style="font-size:2rem">🌱</div><div class="res-t" style="font-size:1.2rem">Nothing saved yet</div>'
             '<div class="res-c">Scan a leaf or get a crop recommendation and it will show up here.</div></div>')
        st.button("Scan a leaf", on_click=go, args=("Disease Detection",), type="primary", key="empty_cta")
    else:
        history_rows(rows)

flush_cookie()