"""Pure, UI-independent logic for the AgroPulse.ai diagnostic suite."""

import base64
import io

MODEL = "gpt-4o-mini"
TEMPERATURE = 0.2

FREE_TIER = "Free Plan (1 Scan/Day)"
PRO_TIER = "Pro Farmer ($29/mo - Unlimited)"

SYSTEM_PROMPT = (
    "You are a senior plant pathologist and expert commercial agronomist. "
    "Provide clean, highly accurate, actionable advice based on images."
)

USER_PROMPT = """
Analyze this plant image. Act as a deep learning classifier and tell the farmer exactly what disease or issue you see.

Format your final response using this exact clean structure:

### 🔍 Diagnosis: [Write the Plant Name and the Detected Disease/Issue Here]

### 🛑 1. Immediate Field Intervention Strategy
(Provide specific spray ratios, organic alternatives, or pruning steps to kill this issue immediately)

### 🚀 2. Accelerated Growth Protocol
(Provide exact N-P-K fertilizer shifts, soil remedies, or watering cadences to make this plant grow faster during recovery)
"""


def is_pro_tier(tier):
    """Return True when the selected plan tier grants unlimited inferences."""
    return tier != FREE_TIER


def encode_image(img):
    """Serialize a PIL image to a base64 string, defaulting to JPEG."""
    buffer = io.BytesIO()
    img.save(buffer, format=img.format if img.format else "JPEG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def build_diagnosis_messages(base64_image):
    """Build the chat messages payload for the OpenAI Vision request."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": USER_PROMPT},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                },
            ],
        },
    ]


def extract_plan(response):
    """Pull the generated agronomist plan out of a chat completion response."""
    return response.choices[0].message.content


def diagnose(client, img):
    """Encode `img`, run it through the Vision model and return the plan text."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=build_diagnosis_messages(encode_image(img)),
        temperature=TEMPERATURE,
    )
    return extract_plan(response)
