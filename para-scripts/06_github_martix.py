from utils import load_tomldata, github_write_step_output
from pathlib import Path
from loguru import logger

CONFIG_PATH = Path(".github/configs/versions.toml")

def matrix_generate(version_data: dict) -> dict:
    martix_versions = {"include": [{"version": v["mc_version"]} for v in version_data["versions"]]}
    logger.debug(martix_versions)
    return martix_versions

def main():
    config_data = load_tomldata(CONFIG_PATH)
    martix_json = matrix_generate(config_data)
    github_write_step_output("martix_json", martix_json)
    # output = json.dumps(result, separators=(",", ":"), ensure_ascii=False).replace("'", "\"")  # noqa: E501

main()
