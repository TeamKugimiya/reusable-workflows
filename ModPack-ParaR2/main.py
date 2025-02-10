import os
import sys
import json
import shutil
from pathlib import Path
from loguru import logger

from paratranz_py import ParaTranz

PROJECT_ID = os.getenv("PROJECT_ID")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")

DATA_PATH = Path("data")
WORKDIR = Path("workdir")
PACK_FORMAT = int(os.getenv("PACK_FORMAT"))
PACK_DESCRIPTION = os.getenv("PACK_DESCRIPTION")

def verify_env():
    """
    驗證環境變數
    - 驗證 PROJECT_ID, AUTH_TOKEN, PACK_FORMAT 是否存在
    """
    logger.info("Checking environment variables...")
    if not PROJECT_ID or not AUTH_TOKEN:
        logger.error("PROJECT_ID or AUTH_TOKEN environment variable is not set.")
        sys.exit(1)
    if not PACK_FORMAT:
        logger.error("PACK_FORMAT environment variable is not set.")
        sys.exit(1)

def para_download():
    """
    下載並解壓縮資料
    - 從 ParaTranz 下載資料並解壓縮到 data 資料夾
    """
    para = ParaTranz(AUTH_TOKEN)

    logger.info(f"Downloading artifact and extract to {DATA_PATH.absolute()}...")
    para.artifacts.download_artifacts(PROJECT_ID, extract_path=DATA_PATH)

def move_assets_folder():
    """
    移動資料夾
    - 將 data/assets 資料夾移動到 workdir
    """
    WORKDIR.mkdir()
    data_assets_path = DATA_PATH.joinpath("utf8/assets")
    try:
        logger.info("Moving data folder to workdir...")
        shutil.move(data_assets_path, WORKDIR)
        logger.success("Move Success!")
        shutil.rmtree(DATA_PATH)
    except Exception as e:
        logger.error(f"Move Failed! Error: {str(e)}")
        sys.exit(1)

def create_pack_mcmeta():
    """
    生成 pack.mcmeta
    - 生成 pack.mcmeta 檔案
    """
    logger.info("Creating pack.mcmeta...")
    PACK_PATH = WORKDIR.joinpath("pack.mcmeta")
    data_mcmeta = {
      "pack": {
        "pack_format": PACK_FORMAT,
        "description": PACK_DESCRIPTION
      }
    }
    data_mcmeta_json = json.dumps(data_mcmeta, indent=2, ensure_ascii=False)
    logger.info("Writing pack.mcmeta...")
    logger.info(data_mcmeta_json)
    PACK_PATH.write_text(data_mcmeta_json)

def convert_lang():
    """
    轉換 en_us.json 到 zh_tw.json
    - 將 lang 底下的 en_us.json 轉換成 zh_tw.json
    """
    logger.info("Converting en_us.json to zh_tw.json...")
    ASSETS_PATH = WORKDIR.joinpath("assets")
    for i in ASSETS_PATH.glob("**/lang/en_us.json"):
        i.rename(i.parent.joinpath("zh_tw.json"))
    logger.success("Convert Success!")

def main():
    verify_env()
    para_download()
    move_assets_folder()
    create_pack_mcmeta()
    convert_lang()
    logger.success("Script Finished!")

main()
