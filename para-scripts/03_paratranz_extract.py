import shutil
from pathlib import Path
from loguru import logger

# Path ENVs
WORKDIR_FOLDER_PATH = Path(".workdir")
WORKDIR_FILE_PATH = WORKDIR_FOLDER_PATH.joinpath("para_translation_artifact.zip")

def archive_extract(archive_path: Path, extract_dest: Path):
    logger.info("Extract archive...")
    shutil.unpack_archive(archive_path, extract_dest)
    logger.success("Extracted!")

def fix_paths(workdir_path: Path, correct_path: Path, remove_path: Path):
    logger.info("Correctly MultiVersions Path...")
    shutil.move(workdir_path, correct_path)
    shutil.rmtree(remove_path)
    logger.success("Done!")

def remove_utf8(path: Path):
    logger.info("Remove ut8 folder...")
    shutil.rmtree(path)

def main():
    archive_extract(WORKDIR_FILE_PATH, WORKDIR_FOLDER_PATH)
    remove_utf8(WORKDIR_FOLDER_PATH.joinpath("utf8"))
    fix_paths(WORKDIR_FOLDER_PATH.joinpath("raw/MultiVersions"), WORKDIR_FOLDER_PATH.joinpath("MultiVersions"), WORKDIR_FOLDER_PATH.joinpath("raw"))

main()