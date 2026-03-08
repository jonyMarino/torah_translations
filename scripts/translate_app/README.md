# translate_app

Flask web application for generating interlinear Hebrew–Spanish translations using the GitHub Copilot (GitHub Models) AI SDK. The translations are saved as TSV files (`.csv`) compatible with the `texts/` folder structure of this repository.

## Requirements

- Python 3.10+
- A **GitHub token** with access to [GitHub Models](https://github.com/marketplace/models) (set as `GITHUB_TOKEN` environment variable)

## Installation

```bash
cd scripts/translate_app
pip install -r requirements.txt
```

## Configuration

| Variable | Description | Default |
|---|---|---|
| `GITHUB_TOKEN` | GitHub personal access token for GitHub Models API | *(required)* |
| `TEXTS_BASE_DIR` | Absolute path to the `texts/` root directory | `../../texts` relative to `app.py` |

## Running

```bash
export GITHUB_TOKEN=your_github_token_here
python app.py
```

Then open <http://localhost:5000> in your browser.

## Usage

1. **Paste Hebrew text** into the large text area.
2. **Select the AI model** (`gpt-4o`, `gpt-4o-mini`, `o3-mini`, …).
3. *(Optional)* Fill in metadata fields: book name, parashah, chapter, initial verse.
4. Set the **destination folder** inside `texts/` (e.g. `genesis` or `bamidbar/naso`) and the **output filename** (without extension, e.g. `bereshit`).
5. Click **Traducir** — the app calls the AI model and shows a preview table.
6. Click **Guardar TSV** — the file is written to `texts/{folder}/{filename}.csv`.

## Output format

The generated `.csv` file is tab-separated with the following columns:

```
original	translation	phonetics	format	notes
```

Metadata rows (book, part, chapter, subchapter, intro) are prepended automatically based on the optional fields you fill in, followed by one row per translated word/phrase with an empty `format` column.

## Example

Input: `בְּרֵאשִׁית בָּרָא אֱלֹהִים אֵת הַשָּׁמַיִם וְאֵת הָאָרֶץ`

Generated `texts/genesis/bereshit.csv` (excerpt):

```
original	translation	phonetics	format	notes
LIBRO DE GÉNESIS			book	
PARASHAT BERESHIT	PARASHAT BERESHIT		part	
CAPÍTULO 1	CAPÍTULO 1		chapter	
א	1		subchapter	
En el principio Dios creó los cielos y la tierra.			intro	
בְּרֵאשִׁית	En el principio	Bereshit		
בָּרָא	creó	bara		
אֱלֹהִים	Dios	Elohim		
```
