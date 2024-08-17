import shutil
from pathlib import Path
from loguru import logger

# Path ENVs
WORKDIR_FOLDER_PATH = Path(".workdir")
WORKDIR_FILE_PATH = WORKDIR_FOLDER_PATH.joinpath("para_translation_artifact.zip")

def archive_extract(archive_path: Path, extract_dest: Path):
    logger.info("Extract archive...")
    shutil.unpack_archive(archive_path, extract_dest)
    logger.info("Extracted!")

def fix_paths(workdir_path: Path, correct_path: Path, remove_path: Path):
    logger.info("Correctly MultiVersions Path...")
    shutil.move(workdir_path, correct_path)
    shutil.rmtree(remove_path)
    logger.info("Done!")

def main():
    archive_extract(WORKDIR_FILE_PATH, WORKDIR_FOLDER_PATH)
    fix_paths(WORKDIR_FOLDER_PATH.joinpath("utf8/MultiVersions"), WORKDIR_FOLDER_PATH.joinpath("MultiVersions"), WORKDIR_FOLDER_PATH.joinpath("utf8"))

main()