import json
import os
import re
import asyncio

from flask import Flask, jsonify, render_template, request
from copilot import CopilotClient

app = Flask(__name__)

TEXTS_BASE_DIR = os.environ.get(
    "TEXTS_BASE_DIR",
    os.path.join(os.path.dirname(__file__), "..", "..", "texts"),
)

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
TRANSLATION_TIMEOUT_SECONDS = 120
TRANSLATION_PROMPT = """Eres un traductor experto de hebreo bíblico a español. Tu tarea es generar una traducción interlineada (palabra por palabra o grupo de palabras) de un texto en hebreo bíblico.

REGLAS ESTRICTAS:
1. La traducción debe ser INTERLINEADA: cada fila tiene una o más palabras en hebreo y su traducción al español.
2. La traducción en español debe ser LEGIBLE como texto fluido si se leen solo las traducciones en orden. Es decir, al concatenar todas las traducciones debe formarse una oración coherente en español.
3. A veces necesitarás agrupar 2 o más palabras hebreas en una sola fila para que la traducción al español sea natural. Por ejemplo, una preposición + sustantivo hebreos pueden traducirse juntos.
4. Una palabra hebrea puede traducirse como varias palabras en español (ej: בְּרֵאשִׁית → "En el principio").
5. Si necesitas agregar palabras auxiliares en español que NO son traducción directa del hebreo sino que ayudan a la comprensión, ponlas entre corchetes []. Por ejemplo: "[que]", "[el cual]", "[es decir]".
6. Proporciona la transliteración fonética de cada entrada hebrea.
7. NO incluyas metadatos estructurales (book, part, chapter, etc.), solo las palabras del texto.

FORMATO DE SALIDA:
Devuelve EXCLUSIVAMENTE un JSON array donde cada elemento tiene:
- "original": texto en hebreo (una o más palabras)
- "translation": traducción al español
- "phonetics": transliteración fonética

Ejemplo de salida:
[
  {{"original": "בְּרֵאשִׁית", "translation": "En el principio", "phonetics": "Bereshit"}},
  {{"original": "בָּרָא", "translation": "creó", "phonetics": "bara"}},
  {{"original": "אֱלֹהִים", "translation": "Dios", "phonetics": "Elohim"}},
  {{"original": "אֵת הַשָּׁמַיִם", "translation": "los cielos", "phonetics": "et hashamayim"}},
  {{"original": "וְאֵת הָאָרֶץ", "translation": "y la tierra", "phonetics": "ve'et ha'aretz"}}
]

TEXTO HEBREO A TRADUCIR:
{hebrew_text}"""


def get_copilot_client():
    token = GITHUB_TOKEN
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable is not set.")
    return CopilotClient({"github_token": token})


def _extract_json_array(content: str) -> list[dict]:
    json_match = re.search(r"\[.*\]", content, re.DOTALL)
    if json_match:
        content = json_match.group(0)
    return json.loads(content)


def _get_event_type_string(event) -> str:
    event_type = getattr(event, "type", "")
    return getattr(event_type, "value", str(event_type))


async def _translate_hebrew_async(hebrew_text: str, model: str) -> list[dict]:
    client = get_copilot_client()
    prompt = TRANSLATION_PROMPT.format(hebrew_text=hebrew_text)
    await client.start()
    try:
        session = await client.create_session({"model": model})
        try:
            event = await session.send_and_wait(
                {"prompt": prompt}, timeout=TRANSLATION_TIMEOUT_SECONDS
            )
            content = ""
            if event and _get_event_type_string(event) == "assistant.message":
                data = getattr(event, "data", None)
                content = (getattr(data, "content", "") or "").strip()

            if not content:
                # Depending on SDK/CLI event timing, send_and_wait can resolve on a non-message
                # event (for example, session idle). In that case, recover the last assistant message.
                for message in reversed(await session.get_messages()):
                    if _get_event_type_string(message) == "assistant.message":
                        data = getattr(message, "data", None)
                        content = (getattr(data, "content", "") or "").strip()
                        if content:
                            break

            if not content:
                raise ValueError("No assistant message content returned by Copilot SDK.")

            return _extract_json_array(content)
        finally:
            await session.disconnect()
    finally:
        await client.stop()


def translate_hebrew(hebrew_text: str, model: str) -> list[dict]:
    return asyncio.run(_translate_hebrew_async(hebrew_text, model))


def build_tsv(
    words: list[dict],
    book: str = "",
    part: str = "",
    chapter: str = "",
    subchapter: str = "",
) -> str:
    rows = ["\t".join(["original", "translation", "phonetics", "format", "notes"])]

    def add_row(original="", translation="", phonetics="", fmt="", notes=""):
        rows.append(f"{original}\t{translation}\t{phonetics}\t{fmt}\t{notes}")

    if book:
        add_row(original=book, fmt="book")
    if part:
        add_row(original=part, translation=part, fmt="part")
    if chapter:
        add_row(original=chapter, translation=chapter, fmt="chapter")
    if subchapter:
        add_row(original=subchapter, fmt="subchapter")

    intro_text = " ".join(w.get("translation", "") for w in words)
    add_row(original=intro_text, fmt="intro")

    for word in words:
        add_row(
            original=word.get("original", ""),
            translation=word.get("translation", ""),
            phonetics=word.get("phonetics", ""),
        )

    return "\n".join(rows) + "\n"


def save_tsv(tsv_content: str, folder: str, filename: str) -> str:
    safe_folder = os.path.normpath(folder).lstrip("/")
    safe_filename = os.path.basename(filename)
    texts_base = os.path.realpath(TEXTS_BASE_DIR)
    dest_dir = os.path.realpath(os.path.join(texts_base, safe_folder))
    if not dest_dir.startswith(texts_base + os.sep) and dest_dir != texts_base:
        raise ValueError(f"Invalid folder path: '{folder}' resolves outside the texts directory.")
    os.makedirs(dest_dir, exist_ok=True)
    filepath = os.path.join(dest_dir, f"{safe_filename}.csv")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(tsv_content)
    return filepath


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/translate", methods=["POST"])
def translate():
    data = request.get_json(force=True)
    hebrew_text = data.get("hebrew_text", "").strip()
    model = data.get("model", "gpt-4o")

    if not hebrew_text:
        return jsonify({"error": "No Hebrew text provided."}), 400
    if not GITHUB_TOKEN:
        return jsonify({"error": "GITHUB_TOKEN is not configured on the server."}), 500

    try:
        words = translate_hebrew(hebrew_text, model)
    except ValueError as e:
        return jsonify({"error": str(e)}), 500
    except json.JSONDecodeError as e:
        return jsonify({"error": f"Failed to parse model response as JSON: {e}"}), 500
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": f"Translation error: {e}"}), 500

    return jsonify({"words": words})


@app.route("/save", methods=["POST"])
def save():
    data = request.get_json(force=True)
    words = data.get("words", [])
    folder = data.get("folder", "").strip()
    filename = data.get("filename", "").strip()
    book = data.get("book", "").strip()
    part = data.get("part", "").strip()
    chapter = data.get("chapter", "").strip()
    subchapter = data.get("subchapter", "").strip()

    if not words:
        return jsonify({"error": "No translation data to save."}), 400
    if not folder:
        return jsonify({"error": "Destination folder is required."}), 400
    if not filename:
        return jsonify({"error": "Output filename is required."}), 400

    try:
        tsv = build_tsv(words, book=book, part=part, chapter=chapter, subchapter=subchapter)
        filepath = save_tsv(tsv, folder, filename)
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": f"Failed to save file: {e}"}), 500

    return jsonify({"message": f"File saved: {filepath}", "path": filepath})


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug, port=5000)
