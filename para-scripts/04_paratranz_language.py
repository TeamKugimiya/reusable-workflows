import json
from pathlib import Path
from loguru import logger

# Path ENVs
WORKDIR_FOLDER_PATH = Path(".workdir")

def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text())
    except Exception as e:
        logger.error("Loading json has an error:")
        logger.error(f"| path: {path}")
        logger.error(f"| info: {e}")
        data = {}
    return data

def convert_mc_language_json_formate(path: Path):
    data = load_json(path)
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
        logger.success(f"Convented {path.name}.")

def format_language_files():
    workdir_path = list(WORKDIR_FOLDER_PATH.joinpath("MultiVersions").rglob("*.json"))

    logger.info("Convert Para format to Minecraft Lang")
    for i in workdir_path:
        convert_mc_language_json_formate(i)

def modid_to_folder():
    workdir_path = list(WORKDIR_FOLDER_PATH.joinpath("MultiVersions").rglob("*.json"))

    logger.info("ModID Folderize")
    for i in workdir_path:
        mod_id = i.stem
        mod_path = i.parent/mod_id/'lang'
        mod_file = mod_path/'zh_tw.json'
        logger.debug(f"mod_id: {mod_id}")
        logger.debug(f"mod_path: {mod_path}")
        logger.debug(f"mod_file: {mod_file}")

        mod_path.mkdir(parents=True, exist_ok=True)
        i.rename(mod_file)

        logger.success(f"Fixed {mod_id} folder.")

def main():
    format_language_files()
    modid_to_folder()

main()