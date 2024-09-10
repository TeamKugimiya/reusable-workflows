import json
from pathlib import Path
from loguru import logger

# Path ENVs
WORKDIR_FOLDER_PATH = Path(".workdir")

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
    modid_to_folder()

main()