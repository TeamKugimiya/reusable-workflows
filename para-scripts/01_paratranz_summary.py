import os
from utils import paratranz_get_artifact_info
from loguru import logger

# ParaTranz ENVs
API_TOKEN = os.environ.get("API_TOKEN")
PROJECT_ID = os.environ.get("PROJECT_ID")

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
    artifact_info = paratranz_get_artifact_info(API_TOKEN, PROJECT_ID)
    paratranz_generate_summary(artifact_info)

main()
