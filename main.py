#@alireza dehghanpour 
#ad100000@uni-bremen.de
# .............................libraries..................................#
import flet as ft
import requests
import json
import re
import string
from jsonschema import validate, ValidationError

# .............................llm..................................#
#API_URL = "http://127.0.0.1:8000/v1/chat/completions"
API_URL = "http://host.docker.internal:8000/v1/chat/completions"


# .............................json..................................#
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "id_number": {"type": "integer"},
        "age": {"type": "integer", "minimum": 0, "maximum": 150},
        "gender": {"type": "string", "enum": ["male", "female", "other"]},
        "nationality": {"type": "string"},
        "consent": {"type": "boolean"},
        "smoke": {"type": "boolean"},
        "allergy": {"type": "string"},
        "comments": {"type": "string"}
    },
    "required": ["name", "id_number", "age", "gender", "nationality", "consent", "smoke", "allergy"]
}

# .............................extract text..................................#
def extract_json_from_text(text):
    try:
        start = text.find("{")
        end = text.rfind("}")
        while start != -1 and end != -1 and end > start:
            candidate = text[start:end + 1]
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                end = text.rfind("}", 0, end)
        return "{}"
    except Exception:
        return "{}"

# .............................convert to BL..................................#
def smart_bool(value):
    if isinstance(value, bool):
        return value
    if not isinstance(value, str):
        return False

    val = value.strip().lower()
    val = val.translate(str.maketrans("", "", string.punctuation))  # remove punctuation

    true_values = [
        "true", "yes", "y", "1", "smoker", "i smoke",
        "currently smoking", "regular smoker", "daily smoker",
        "active smoker", "yes i smoke", "i am a smoker"
    ]
    false_values = [
        "false", "no", "n", "0", "non-smoker", "non smoker",
        "never smoked", "does not smoke", "no smoking", "not smoking",
        "dont smoke", "do not smoke", "not a smoker", "never smoke",
        "i am a nonsmoker", "i am a non smoker", "im not a smoker"
    ]

    if val in true_values:
        return True
    if val in false_values:
        return False

    if re.search(r"\bi\s+do\s+not\s+smoke\b", val): return False
    if re.search(r"\bi\s+don[’']?t\s+smoke\b", val): return False
    if re.search(r"\bi\s+am\s+not\s+a\s+smoker\b", val): return False
    if re.search(r"\bi\s+am\s+(a\s+)?non[-\s]?smoker\b", val): return False
    if re.search(r"\bi\s+smoke\b", val): return True
    if re.search(r"\bi\s+am\s+a\s+smoker\b", val): return True

    return False

# .............................LLM response..................................#
def send_to_llm(text):
    try:
        prompt = f"""
From the text below, extract these fields and return ONLY a valid JSON object with the exact keys shown below.

Required fields:
- name (first name only)
- id_number (integer)
- age (integer)
- gender ("male", "female", or "other")
- nationality (string)
- consent (true/false)
- smoke (true/false)
- allergy (string, comma-separated if more than one)
- comments (string)

DO NOT include markdown, explanation, or code.
RETURN ONLY a pure JSON object as output.

Input text:
{text}
"""
        response = requests.post(
            API_URL,
            headers={"Content-Type": "application/json"},
            json={
                "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=20
        )
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"ERROR: {e}"

# .............................app..................................#
def main(page: ft.Page):
    page.title = "Medical Intake Form"
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 0

    name = ft.TextField(label="Name", expand=True)
    id_number = ft.TextField(label="ID Number", keyboard_type="number", expand=True)
    age = ft.TextField(label="Age", keyboard_type="number", expand=True)
    nationality = ft.TextField(label="Nationality", expand=True)
    gender = ft.Dropdown(label="Gender", options=[
        ft.dropdown.Option("Male"),
        ft.dropdown.Option("Female"),
        ft.dropdown.Option("Other")
    ], expand=True)
    smoke = ft.Switch(label="Do you smoke?")
    allergy = ft.TextField(label="Allergy", multiline=True, min_lines=1, expand=True)
    consent = ft.Switch(label="Consent given?")
    comments = ft.TextField(label="Comments", multiline=True, min_lines=2, expand=True)
    free_text = ft.TextField(label="Free Text Input", multiline=True, min_lines=3, expand=True)
    result = ft.Text(value="", selectable=True, color=ft.Colors.RED)

# .............................autto fill func..................................#
    def autofill(e):
        attempts = 0
        data = {}
        error_message = ""

        while attempts < 3:
            raw_output = send_to_llm(free_text.value)
            print(f"RAW OUTPUT (attempt {attempts + 1}):\n", raw_output)
            extracted_json = extract_json_from_text(raw_output)
            print("CLEANED JSON:\n", extracted_json)

            try:
                parsed = json.loads(extracted_json)
                parsed = {k.lower(): v for k, v in parsed.items()}
                parsed["consent"] = smart_bool(parsed.get("consent", False))
                parsed["smoke"] = smart_bool(parsed.get("smoke", False))
                if isinstance(parsed.get("gender"), str):
                    parsed["gender"] = parsed["gender"].lower()
                if isinstance(parsed.get("allergy"), list):
                    parsed["allergy"] = ", ".join(parsed["allergy"])

                validate(instance=parsed, schema=schema)
                data = parsed
                break

            except ValidationError as ve:
                error_message = f"Validation error: {ve.message}"
            except Exception as ex:
                error_message = f"Parsing error: {ex}"

            attempts += 1

        if data:
            name.value = data.get("name", "")
            id_number.value = str(data.get("id_number", ""))
            age.value = str(data.get("age", ""))
            nationality.value = data.get("nationality", "")
            gender.value = data.get("gender", "").capitalize()
            smoke.value = data.get("smoke", False)
            allergy.value = data.get("allergy", "")
            consent.value = data.get("consent", False)
            comments.value = data.get("comments", "")
            result.value = "Form auto-filled successfully."
            result.color = ft.Colors.GREEN
        else:
            result.value = f"Failed after 3 attempts. Last error: {error_message}"
            result.color = ft.Colors.RED

        page.update()

# .............................save..................................#
    def save_form(e):
        try:
            with open("form_data.json", "w") as f:
                json.dump({
                    "name": name.value,
                    "id_number": id_number.value,
                    "age": age.value,
                    "gender": gender.value,
                    "nationality": nationality.value,
                    "consent": consent.value,
                    "smoke": smoke.value,
                    "allergy": allergy.value,
                    "comments": comments.value,
                }, f)
            result.value = "Form saved to file."
            result.color = ft.Colors.GREEN
        except Exception as ex:
            result.value = f"Save error: {ex}"
            result.color = ft.Colors.RED
        page.update()

    form_controls = ft.Column([
        ft.Text("Patient Intake Form", size=24, weight=ft.FontWeight.BOLD),
        name, id_number, age, gender, nationality,
        consent, smoke, allergy, comments,
        free_text,
        ft.Row([
            ft.ElevatedButton("Auto-fill with LLM", on_click=autofill),
            ft.ElevatedButton("Save Form", on_click=save_form),
        ], alignment=ft.MainAxisAlignment.END),
        result
    ], spacing=10)

    form_container = ft.Container(
        content=form_controls,
        padding=25,
        width=500,
        bgcolor=ft.colors.with_opacity(0.99, ft.Colors.WHITE),        
               border_radius=10,
        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12)
    )


    background = ft.Container(
        content=ft.Image(src="/medical.jpg", fit=ft.ImageFit.COVER, expand=True),
        expand=True
    )


    page.add(
        ft.Stack([
            background,
            ft.Container(form_container, alignment=ft.alignment.center)
        ])
    )

#ft.app(target=main, view=ft.WEB_BROWSER, port=8550)
ft.app(target=main, view=ft.WEB_BROWSER, port=8550, assets_dir="assets")


