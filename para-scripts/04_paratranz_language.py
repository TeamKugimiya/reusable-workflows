import json
from pathlib import Path
from loguru import logger

# Path ENVs
WORKDIR_FOLDER_PATH = Path(".workdir")

def convert_mc_language_json_formate(path: Path):
    data = json.loads(path.read_text())
    converted_data = {}

    for i in data:
        key = i["key"]
        translation = i.get("translation", "")
        original = i.get("original", "")

        if not translation:
            logger.warning(f"Key {key} is empty! BYPASS")
            continue

        if translation == original:
            logger.warning(f"Key {key} translate is equal with original. BYPASS")
            continue

        converted_data[key] = translation

    if len(converted_data) == 0:
        logger.info(f"{path.name} is empty. Deleted.")
        path.unlink()
    else:
        with open(path, "w", encoding="utf8") as f:
            json.dump(converted_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Convented {path.name}.")

def format_lang_files():
    workdir_path = list(WORKDIR_FOLDER_PATH.joinpath("MultiVersions").rglob("*.json"))

    logger.info("---=== Convert Para format to Minecraft Lang ===---")
    for i in workdir_path:
        convert_mc_language_json_formate(i)
    logger.info("---=============================================---")

def main():
    format_lang_files()

main()