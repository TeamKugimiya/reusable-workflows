import os
import pytz
from loguru import logger
from pathlib import Path
from datetime import datetime
from utils import paratranz_get_artifact_info

# ParaTranz ENVs
API_TOKEN = os.environ.get("API_TOKEN")
PROJECT_ID = os.environ.get("PROJECT_ID")

def timestamp_format(timestamp: str):
    dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
    tz_taipei = pytz.timezone("Asia/Taipei")
    dt_taipei = dt.replace(tzinfo=pytz.utc).astimezone(tz_taipei)
    formatted_date = dt_taipei.strftime("%Y/%m/%d")
    logger.debug(formatted_date)
    formatted_time = dt_taipei.strftime("%Y/%m/%d %H:%M:%S")
    logger.debug(formatted_time)
    return formatted_date, formatted_time

def calculate_completion_percentage(total_strings: int, translated_strings: int) -> float:
    if total_strings == 0:
        return 0 
    completion_percent = (translated_strings / total_strings) * 100
    return completion_percent

def paratranz_gh_generate_summary(artifact_data: dict):
    logger.info("Generate artifact info summary...")

    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary_env:
        summary_env.write("# 🚧 Artifact Info\n")
        summary_env.write(f"- ID: ``{artifact_data['id']}``\n")
        summary_env.write(f"- Created At: ``{artifact_data['createdAt']}``\n")
        summary_env.write(f"- Total Strings: ``{artifact_data['total']}``\n")
        summary_env.write(f"- Translated Strings: ``{artifact_data['translated']}``\n")
        summary_env.write(f"- Disputed Strings: ``{artifact_data['disputed']}``")
        summary_env.close()

def paratranz_modrinth_generate_summary(artifact_data: dict):
    logger.info("Generate modrinth summary...")

    date_date, date_time = timestamp_format(artifact_data['createdAt'])
    completion_percent = calculate_completion_percentage(artifact_data['total'], artifact_data['translated'])

    summary = f"""## 🌏 {date_date}
- Para 建構時間：`{date_time}`
- 總詞條數：`{artifact_data['total']}`
- 已翻譯條數：`{artifact_data['translated']}`
- 有疑問條數：`{artifact_data['disputed']}`
- 翻譯完成度：**{completion_percent:.2f}%**
"""
    logger.debug(summary)
    return summary

def write_file(path: Path, data: str):
    logger.info("Write a txt...")
    path.write_text(data)

def main():
    artifact_info = paratranz_get_artifact_info(API_TOKEN, PROJECT_ID)
    paratranz_gh_generate_summary(artifact_info)
    modrinth_summary = paratranz_modrinth_generate_summary(artifact_info)
    write_file(Path("modrinth_summary.txt"), modrinth_summary)

main()
