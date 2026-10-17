"""Shared farm logic: crop schedules, task status and the daily reminder text.
Used by app.py (Streamlit) and reminders.py (daily job), so both always agree."""
import datetime as dt

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

RAIN_SENSITIVE = ("spray", "fert")

def compute_tasks(crop, planted, done=(), today=None):
    """Tasks for one plot with a status: done, late, due (today or next 2 days) or up."""
    today = today or dt.date.today(); out = []
    for idx, (off, kind, text) in enumerate(SCHEDULE[crop]):
        due = planted + dt.timedelta(days=off)
        if idx in done or (kind == "plant" and due <= today): status = "done"
        elif due < today: status = "late"
        elif due <= today + dt.timedelta(days=2): status = "due"
        else: status = "up"
        out.append(dict(idx=idx, due=due, kind=kind, text=text, status=status))
    return out

def build_message(plots, rain_pct=None, today=None, max_overdue_days=3):
    """Morning reminder text, or None when there is nothing to say.
    plots: list of dicts with crop, planted (date) and done (set of task indexes)."""
    today = today or dt.date.today(); tomorrow = today + dt.timedelta(days=1)
    now, soon, late = [], [], []; rain_hit = False
    for p in plots:
        if p["crop"] not in SCHEDULE: continue
        label = f"{p['crop']} (planted {p['planted'].strftime('%d %b')})"
        for t in compute_tasks(p["crop"], p["planted"], p.get("done", ()), today):
            if t["status"] == "done": continue
            gap = (today - t["due"]).days
            if t["due"] == today: now.append(f"• {label}: {t['text']}")
            elif t["due"] == tomorrow: soon.append(f"• {label}: {t['text']}")
            elif 0 < gap <= max_overdue_days: late.append(f"• {label}: {t['text']} ({gap} day{'s' if gap != 1 else ''} late)")
            else: continue
            if t["kind"] in RAIN_SENSITIVE: rain_hit = True
    if not (now or soon or late): return None
    parts = ["🌾 FarmAI reminder"]
    for title, items in (("Today", now), ("Tomorrow", soon), ("Overdue", late)):
        if items: parts.append(title + "\n" + "\n".join(items))
    if rain_pct is not None and rain_pct >= 60 and rain_hit:
        parts.append(f"🌧️ Rain is likely ({rain_pct:.0f}%). Delay spraying and fertiliser until the field is dry.")
    return "\n\n".join(parts)
