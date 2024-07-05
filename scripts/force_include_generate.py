import os

def generate_include_list(include_list):
    with open(os.environ["GITHUB_STEP_SUMMARY"], "w") as env:
        for i in include_list:
            env.write(f"['{i}']\n")
            env.write("force_include = true")

def main():
    force_include_files_str = os.environ.get("force_include_files")

    if force_include_files_str:
        include_list = force_include_files_str.split(',')
        generate_include_list(include_list)
        print(include_list)

main()
