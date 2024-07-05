import os

def generate_include_list(include_list):
    for i in include_list:
        print(f"['{i}']\n")
        print("force_include = true")

def main():
    force_include_files_str = os.environ.get("force_include_files")

    if force_include_files_str is not None:
        include_list = force_include_files_str.split(',')
        generate_include_list(include_list)

main()
