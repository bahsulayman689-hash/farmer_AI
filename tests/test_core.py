import base64
import io
from types import SimpleNamespace

import pytest
from PIL import Image

from agropulse import core


def make_image(fmt=None, color=(10, 120, 40), size=(4, 4)):
    """Build a small in-memory PIL image, optionally round-tripped through `fmt`."""
    img = Image.new("RGB", size, color)
    if fmt is None:
        return img
    buffer = io.BytesIO()
    img.save(buffer, format=fmt)
    buffer.seek(0)
    return Image.open(buffer)


class FakeCompletions:
    def __init__(self, content):
        self.content = content
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))]
        )


class FakeClient:
    def __init__(self, content="### 🔍 Diagnosis: Tomato — Early Blight"):
        self.chat = SimpleNamespace(completions=FakeCompletions(content))


@pytest.mark.parametrize(
    "tier, expected",
    [
        (core.FREE_TIER, False),
        (core.PRO_TIER, True),
        ("Some Future Enterprise Plan", True),
    ],
)
def test_is_pro_tier(tier, expected):
    assert core.is_pro_tier(tier) is expected


def test_free_and_pro_tier_labels_are_distinct():
    assert core.FREE_TIER != core.PRO_TIER


def test_encode_image_returns_decodable_base64_png():
    encoded = core.encode_image(make_image("PNG"))

    decoded = base64.b64decode(encoded, validate=True)
    assert decoded.startswith(b"\x89PNG\r\n\x1a\n")
    assert Image.open(io.BytesIO(decoded)).size == (4, 4)


def test_encode_image_defaults_to_jpeg_when_format_is_unknown():
    img = make_image()
    assert img.format is None

    decoded = base64.b64decode(core.encode_image(img), validate=True)
    assert Image.open(io.BytesIO(decoded)).format == "JPEG"


def test_encode_image_preserves_source_format():
    decoded = base64.b64decode(core.encode_image(make_image("PNG")), validate=True)
    assert Image.open(io.BytesIO(decoded)).format == "PNG"


def test_encode_image_is_deterministic():
    img = make_image("PNG")
    assert core.encode_image(img) == core.encode_image(img)


def test_encode_image_propagates_save_errors():
    class Unsaveable:
        format = "PNG"

        def save(self, buffer, format):
            raise OSError("cannot write mode P as PNG")

    with pytest.raises(OSError):
        core.encode_image(Unsaveable())


def test_build_diagnosis_messages_shape_and_roles():
    messages = core.build_diagnosis_messages("QUJD")

    assert [m["role"] for m in messages] == ["system", "user"]
    assert messages[0]["content"] == core.SYSTEM_PROMPT

    text_part, image_part = messages[1]["content"]
    assert text_part == {"type": "text", "text": core.USER_PROMPT}
    assert image_part["type"] == "image_url"
    assert image_part["image_url"]["url"] == "data:image/jpeg;base64,QUJD"


def test_user_prompt_requests_the_expected_report_sections():
    assert "### 🔍 Diagnosis:" in core.USER_PROMPT
    assert "1. Immediate Field Intervention Strategy" in core.USER_PROMPT
    assert "2. Accelerated Growth Protocol" in core.USER_PROMPT


def test_extract_plan_reads_first_choice_content():
    response = SimpleNamespace(
        choices=[
            SimpleNamespace(message=SimpleNamespace(content="first")),
            SimpleNamespace(message=SimpleNamespace(content="second")),
        ]
    )
    assert core.extract_plan(response) == "first"


def test_extract_plan_raises_when_no_choices_returned():
    with pytest.raises(IndexError):
        core.extract_plan(SimpleNamespace(choices=[]))


def test_diagnose_returns_generated_plan():
    client = FakeClient("### 🔍 Diagnosis: Maize — Rust")

    assert core.diagnose(client, make_image("PNG")) == "### 🔍 Diagnosis: Maize — Rust"


def test_diagnose_sends_model_temperature_and_encoded_image():
    client = FakeClient()
    img = make_image("PNG")

    core.diagnose(client, img)

    kwargs = client.chat.completions.kwargs
    assert kwargs["model"] == core.MODEL
    assert kwargs["temperature"] == core.TEMPERATURE
    expected_url = f"data:image/jpeg;base64,{core.encode_image(img)}"
    assert kwargs["messages"][1]["content"][1]["image_url"]["url"] == expected_url


def test_diagnose_propagates_api_errors():
    class FailingClient:
        def __init__(self):
            self.chat = SimpleNamespace(completions=self)

        def create(self, **kwargs):
            raise RuntimeError("rate limited")

    with pytest.raises(RuntimeError, match="rate limited"):
        core.diagnose(FailingClient(), make_image("PNG"))
