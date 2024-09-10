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

def fix_paths(workdir_path: Path, correct_path: Path):
    logger.info("Correctly MultiVersions Path...")
    shutil.move(workdir_path, correct_path)
    logger.success("Done!")

def remove_dir(path: Path):
    if path.exists():
        logger.info(f"Cleanup {path} dir...")
        shutil.rmtree(path)
    else:
        logger.warning(f"{path} is not exist!")

def main():
    archive_extract(WORKDIR_FILE_PATH, WORKDIR_FOLDER_PATH)
    fix_paths(WORKDIR_FOLDER_PATH.joinpath("utf8/MultiVersions"), WORKDIR_FOLDER_PATH.joinpath("MultiVersions"))
    remove_dir(WORKDIR_FOLDER_PATH.joinpath("utf8"))
    remove_dir(WORKDIR_FOLDER_PATH.joinpath("raw"))

main()