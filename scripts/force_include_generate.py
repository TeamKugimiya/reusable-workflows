import os

def generate_include_list(include_list):
    with open(os.environ["GITHUB_STEP_SUMMARY"], "w") as env:
        for i in include_list:
            env.write(f"['{i}']\n")
            env.write("force_include = true")

    print("Force Inlucde Files:")
    for i in include_list:
        print(f"['{i}']")
        print("force_include = true")

def main():
    include_list = list(os.environ.get("force_include_files"))

    if include_list is not None:
        generate_include_list(include_list)
    else:
        print("Array is Empty!")

main()
