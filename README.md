# Nuclear Medicine Intake App (LLM + Flet)

This is a simple form-based app designed for a Nuclear Medicine research task. It uses a local LLM to extract structured information from free-text input.

---

##  Features

- Form implemented using [Flet](https://flet.dev)
- Fields:
  - Numeric: Age, ID Number
  - Short Text: Name, Nationality
  - Long Text: Comments, Allergy
  - Closed: Gender (Male, Female, Other)
  - Binary: Consent, Smoke
  - Free Text Input: for LLM processing
- Automatic form population via local LLM (TinyLlama using vLLM)
- Output JSON validated using `jsonschema`
- Dockerized for easy execution

---

##  How to Run (Docker)

```bash
docker build -t medical-form-app .
docker run -p 8550:8550 medical-form-app
