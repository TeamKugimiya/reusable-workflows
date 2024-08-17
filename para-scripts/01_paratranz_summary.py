import os
import sys
import json
import requests
from loguru import logger

API_URL = "https://paratranz.cn/api"
API_TOKEN = os.environ.get("API_TOKEN")
PROJECT_ID = os.environ.get("PROJECT_ID")

def paratranz_get_artifact_info():
    headers = {
        "Authorization": f"{API_TOKEN}",
        "User-Agent": "ParaTranslationPack GitHub Action Script | Made by Efina"
    }
    response = requests.get(f"{API_URL}/projects/{PROJECT_ID}/artifacts", headers=headers)

    if response.ok:
        data = json.loads(response.content)
        logger.debug(data)
        return data
    else:
        logger.error("Response error: " + str(response.status_code))
        sys.exit(1)

def paratranz_generate_summary(artifact_data: dict):
    logger.info("Generate artifact info summary...")

    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary_env:
        summary_env.write("# 🚧 Artifact Info\n")
        summary_env.write(f"- ID: ``{artifact_data['id']}``\n")
        summary_env.write(f"- Created At: ``{artifact_data['createdAt']}``\n")
        summary_env.write(f"- Total Strings: ``{artifact_data['total']}``\n")
        summary_env.write(f"- Translated Strings: ``{artifact_data['translated']}``\n")
        summary_env.write(f"- Disputed Strings: ``{artifact_data['disputed']}``")
        summary_env.close()

def main():
    artifact_info = paratranz_get_artifact_info()
    paratranz_generate_summary(artifact_info)

main()
