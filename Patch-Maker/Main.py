import os
import sys
import shutil
import tempfile
import zipfile
import yaml
import filecmp

# Simple Loader
def simple_loader(file_path):
    with open(file_path) as file:
        data = yaml.safe_load(file)
        return data
    
# TempDir Maker
def temp_dirs():
    tempdir_client = tempfile.mkdtemp()
    tempdir_server = tempfile.mkdtemp()

    return {
        "tempdir_client_path": tempdir_client,
        "tempdir_server_path": tempdir_server
    }

# Copy Patch Files to Temporary Dir 
def patch_copy(yaml_dict, tempdir_path):
    for item in yaml_dict:
        item_path = os.path.join(os.getcwd(), item)
        item_dest_path = os.path.join(tempdir_path, item)
        if os.path.exists(item_path):
            if os.path.isfile(item_path):
                os.makedirs(os.path.dirname(item_dest_path), exist_ok=True)
                shutil.copy(item_path, item_dest_path)
            elif os.path.isdir(item_path):
                parent_dir = os.path.join(item_dest_path, os.pardir)
                os.makedirs(parent_dir, exist_ok=True)
                shutil.copytree(item_path, item_dest_path, dirs_exist_ok=True)
        else:
            print(f"警告！此檔案或資料夾不存在：{item_path}")
            sys.exit(1)

# Verify Patch Copy
def verify_patch(source_path, dest_path):
    if not os.path.exists(source_path):
        print(f"警告！原始檔案或資料夾不存在：{source_path}")
        sys.exit(1)

    if not os.path.exists(dest_path):
        print(f"警告！目標檔案或資料夾不存在：{dest_path}")
        sys.exit(1)

    if os.path.isfile(source_path):
        if not filecmp.cmp(source_path, dest_path):
            print(f"警告！此檔案有差異：{source_path}")
            sys.exit(1)
    elif os.path.isdir(source_path):
        result = filecmp.dircmp(source_path, dest_path)
        if result.diff_files:
            print("警告！以下檔案有差異：")
            for file in result.diff_files:
                print(file)
            sys.exit(1)

        if result.left_only:
            print("警告！以下檔案在目的資料夾不存在：")
            for file in result.left_only:
                print(file)
            sys.exit(1)

        if result.right_only:
            print("警告！以下檔案在原始資料夾不存在：")
            for file in result.right_only:
                print(file)
            sys.exit(1)

# Make ZIP from Temporary Dir
def make_patch(tempdir_path, file_name):
    zip_filepath = os.path.join(os.getcwd(), file_name)
    with zipfile.ZipFile(zip_filepath, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(tempdir_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, tempdir_path))

# Clean up
def chore_temporary_dir(temp_dir):
    shutil.rmtree(temp_dir)

def main(Debug):
    temp_dirs_data = temp_dirs()
    yaml_dict = simple_loader(".github/configs/config.yml")
    if Debug:
        yaml_dict = simple_loader("config.yml")
        print(temp_dirs_data)
        print(yaml_dict)

    # Patch File Name
    modpack_prefix = yaml_dict["modpack-name"]
    modpack_version = os.environ.get("version", "Unknown")
    client_patch_file = f"{modpack_prefix}-Patches-Client-{modpack_version}.zip"
    server_patch_file = f"{modpack_prefix}-Patches-Server-{modpack_version}.zip"

    # Make Client Patch
    print(f"製作用戶端補丁 {client_patch_file}")
    patch_copy(yaml_dict["client-patch"], temp_dirs_data["tempdir_client_path"])
    for i in yaml_dict["client-patch"]:
        verify_patch(os.path.join(os.getcwd(), i), os.path.join(temp_dirs_data["tempdir_client_path"], i))
    make_patch(temp_dirs_data["tempdir_client_path"], client_patch_file)

    # Make Server Patch
    if yaml_dict["server-patch"]:
        print(f"製作伺服器補丁 {server_patch_file}")
        patch_copy(yaml_dict["server-patch"], temp_dirs_data["tempdir_server_path"])
        for i in yaml_dict["server-patch"]:
            verify_patch(os.path.join(os.getcwd(), i), os.path.join(temp_dirs_data["tempdir_server_path"], i))
        make_patch(temp_dirs_data["tempdir_server_path"], server_patch_file)
    else:
        print("伺服器補丁未指定，忽略...")

    # Chore
    chore_temporary_dir(temp_dirs_data["tempdir_client_path"])
    chore_temporary_dir(temp_dirs_data["tempdir_server_path"])

if __name__ == '__main__':
    main(Debug=False)
