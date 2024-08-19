import os
import json
import pytz
from pathlib import Path
from loguru import logger
from utils import setup_dir
from datetime import datetime, timedelta, timezone

## Pack mcmeta data
MC_PACK_FORMAT = os.environ.get("mc_pack_format")
MC_SUPPORTED_FORMATS_MIN = os.environ.get("mc_supported_formats_min")
MC_SUPPORTED_FORMATS_MAX = os.environ.get("mc_supported_formats_max")
DESCRIPTION = [ "§3§lPara§r §f翻譯包｜§7", "\n§3感謝所有參與專案的貢獻者！" ]

## File path
PACK_PATH = Path("pack/assets")
PACK_MCMETA_PATH = PACK_PATH.parents[0].joinpath("pack.mcmeta")

def current_date() -> str:
    tz = pytz.timezone("Asia/Taipei")
    current_time = datetime.now(tz)
    logger.debug(current_time)
    formatted_time = current_time.strftime("%Y/%m/%d-%H:%M")
    logger.debug(formatted_time)
    return formatted_time

def generate_mcmeta(pack_format: int, supported_format_min: int, supported_format_max: int) -> json:
    pack_mcmeta = {
        "pack": {
            "pack_format": int(pack_format),
            "supported_formats": {
                "min_inclusive": int(supported_format_min),
                "max_inclusive": int(supported_format_max)
            },
            "description": [
                DESCRIPTION[0] + current_date(),
                DESCRIPTION[1]
            ]
        }
    }
    json_data = json.dumps(pack_mcmeta, ensure_ascii=False)
    logger.debug(json_data)
    return json_data

def create_mcmeta_file(mcmeta_json: json, file_path: Path):
    file_path.write_text(mcmeta_json)

def main():
    setup_dir(PACK_PATH, "Pack assets")
    mcmeta_data = generate_mcmeta(MC_PACK_FORMAT, MC_SUPPORTED_FORMATS_MIN, MC_SUPPORTED_FORMATS_MAX)
    create_mcmeta_file(mcmeta_data, PACK_MCMETA_PATH)

main()
