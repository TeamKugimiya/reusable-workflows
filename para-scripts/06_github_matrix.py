from utils import load_tomldata, github_write_step_output
from pathlib import Path
from loguru import logger

CONFIG_PATH = Path(".github/configs/versions.toml")

def matrix_generate(version_data: dict) -> dict:
    matrix_versions = {
        "include": [
            {
                "version": v.get("mc_version"),
                "pack_format": v.get("mc_pack_format"),
                "supported_formats_min": v.get("mc_supported_formats_min")
            }
            for v in version_data.get("versions", [])
        ]
    }
    logger.debug(matrix_versions)
    return matrix_versions

def main():
    config_data = load_tomldata(CONFIG_PATH)
    matrix_json = matrix_generate(config_data)
    # github_write_step_output("matrix_json", matrix_json)
    # output = json.dumps(result, separators=(",", ":"), ensure_ascii=False).replace("'", "\"")  # noqa: E501

main()
