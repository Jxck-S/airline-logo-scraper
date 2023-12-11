import os

# Get a list of all subdirectories in the current working directory
subdirectories = [sub_dir for sub_dir in os.listdir() if os.path.isdir(sub_dir)]

# Count the number of files in each subdirectory
for sub_dir in subdirectories:
    file_count = len([name for name in os.listdir(sub_dir) if os.path.isfile(os.path.join(sub_dir, name))])
    print(f"{file_count} files in {sub_dir}")