### Some unuse function
### Archive at here, maybe someday will use again?

## 03_paratranz_extract.py

# def remove_utf8(path: Path):
#     logger.info("Remove ut8 folder...")
#     shutil.rmtree(path)

# def duplicate_filename_fix(raw_workdir_path: Path):
#     logger.info("Fixing duplicate json...")
#     for file_path in raw_workdir_path.rglob("*.json.json"):
#         new_file_name = file_path.name.replace(".json.json", ".json")
#         new_file_path = file_path.with_name(new_file_name)
#         logger.success(f"Renamed {new_file_name}.")
#         logger.debug(f"- path {new_file_path}")
#         file_path.rename(new_file_path)

## 04_paratranz_language.py

# def convert_mc_language_json_formate(path: Path):
#     def load_json(path: Path) -> dict:
#         try:
#             data = json.loads(path.read_text())
#         except Exception as e:
#             logger.error("Loading json has an error:")
#             logger.error(f"| path: {path}")
#             logger.error(f"| info: {e}")
#             data = {}
#         return data

#     data = load_json(path)
#     converted_data = {}

#     for i in data:
#         key = i["key"]
#         translation = i.get("translation", "")
#         original = i.get("original", "")

#         if not translation:
#             logger.warning(f"Key {key} is empty! BYPASS")
#             continue

#         if translation == original:
#             logger.warning(f"Key {key} translate is equal with original. BYPASS")
#             continue

#         converted_data[key] = translation

#     if len(converted_data) == 0:
#         logger.info(f"{path.name} is empty. Deleted.")
#         path.unlink()
#     else:
#         with open(path, "w", encoding="utf8") as f:
#             json.dump(converted_data, f, indent=2, ensure_ascii=False)
#         logger.success(f"Convented {path.name}.")

# def format_language_files():
#     workdir_path = list(WORKDIR_FOLDER_PATH.joinpath("MultiVersions").rglob("*.json"))

#     logger.info("Convert Para format to Minecraft Lang")
#     for i in workdir_path:
#         convert_mc_language_json_formate(i)
