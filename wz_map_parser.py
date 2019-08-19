import configparser
import glob
import os
import zipfile
import shutil
import json
import sys
import argparse
import logging
import re

# The INPUT_FOLDER is the only variable that needs to be set by the user. Should be a directory of Warzone maps.
INPUT_FOLDER = f"F:\\Desktop\\FLAME_INPUT\\CONVERSION\\INPUT\\"


OUTPUT_FOLDER = f"{INPUT_FOLDER}OUTPUT\\"
TEMP_FOLDER = f"{INPUT_FOLDER}TEMP\\"
MAP_LIST = glob.glob(f"{INPUT_FOLDER}*.wz")
MAP_FILES = ["struct", "feature", "droid"]
listopts = ['position', 'rotation']


# LOGGING
logFormatter = logging.Formatter("%(levelname)s %(asctime)s %(processName)s %(message)s")
fileHandler = logging.FileHandler("{0}".format(f"{INPUT_FOLDER}\\log.txt"))
fileHandler.setFormatter(logFormatter)
rootLogger = logging.getLogger()
rootLogger.addHandler(fileHandler)
rootLogger.setLevel(logging.INFO)
logging.info("Logging begin")

# .ini READER
config = configparser.ConfigParser()
config.optionxform = str

def is_number(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def clear_dir(dir_path):
    if os.path.isdir(dir_path):
        shutil.rmtree(dir_path, ignore_errors=True)

def unzip_maps():
    print("Unzipping maps")
    for each_file in MAP_LIST:
        with zipfile.ZipFile(each_file, 'r') as zip_ref:
            zip_ref.extractall(TEMP_FOLDER)
    shutil.copytree(f"{TEMP_FOLDER}\\multiplay\\maps", OUTPUT_FOLDER)

def parse_authors():
    print("Extracting author information")
    author_list = glob.glob(f"{TEMP_FOLDER}\\*.lev")
    for each_file in author_list:
        with open(each_file) as f:
            # Author information is first 4 lines of xplayers.lev
            map_name = os.path.basename(each_file).rstrip()
            flame_version = f.readline().rstrip()
            date_created = f.readline().rstrip()
            author = f.readline().rstrip()
            license = f.readline().rstrip()

            # The remainder of the file needs to be pasted into addon.lev
            data = f.readlines()

        with open(f"{OUTPUT_FOLDER}\\AUTHORS.txt", "a") as myfile:
            myfile.write(f"{map_name}  {author}  {date_created}  {flame_version}  {license}\n")
        with open(f"{OUTPUT_FOLDER}\\addon.lev", "a") as myfile:
            for each_line in range(len(data)):
                myfile.write(f"{data[each_line].rstrip()}\n")

def convert_ini_to_json():
    for each_map in os.listdir(OUTPUT_FOLDER):
        map_dir = f"{OUTPUT_FOLDER}{each_map}"
        if os.path.isdir(map_dir):
            map_name = os.path.basename(each_map).rstrip()
            print(f"converting {map_name} from .ini to .json")
            for each_file in MAP_FILES:
                FILE_TO_CONVERT =f"{OUTPUT_FOLDER}{map_name}\\{each_file}.ini"

                # Some feature.ini files have health attributes with % signs. These need to be removed before parsing.
                if os.path.exists(FILE_TO_CONVERT):
                    with open(FILE_TO_CONVERT, 'r') as infile:
                        data = infile.read()
                        data = data.replace("%", "")
                    with open(FILE_TO_CONVERT, 'w') as outfile:
                        outfile.write(data)

                config.read(FILE_TO_CONVERT)
                data = {}
                try:
                    for section in config.sections():
                        entry = {}
                        for opt in config.items(section):
                            key = opt[0]
                            value = opt[1]
                            if value.startswith('"') and value.endswith('"'):
                                value = value[1:-1]
                            value = value.split(',')
                            accum = []
                            for result in value:  # convert numbers
                                if is_number(result):
                                    accum.append(int(result))
                                else:
                                    accum.append(result)
                            if key in listopts:
                                entry[key] = accum
                            else:
                                entry[key] = accum[0]
                            if opt[0] == 'name':
                                entry['id'] = opt[1]
                        data[section] = entry

                    for section in config.sections():
                        config.remove_section(section)

                    output_data = json.dumps(data, indent=4, separators=(',', ': '), sort_keys=True)
                    output_file = f"{OUTPUT_FOLDER}{map_name}\\{each_file}.json"
                    with open(output_file, 'w') as f:
                        f.write(output_data)
                except Exception as e:
                    logging.error(f"{map_name}\n{str(e)}")
                    continue

def remove_extra_files():
    print("Removing old .ini files that are no longer used")
    for root, dirs, files in os.walk(OUTPUT_FOLDER):
        for currentFile in files:
            exts = ('.ini')
            if currentFile.lower().endswith(exts):
                os.remove(os.path.join(root, currentFile))

if __name__ == "__main__":
    clear_dir(OUTPUT_FOLDER)
    unzip_maps()
    parse_authors()
    convert_ini_to_json()
    remove_extra_files()
    clear_dir(TEMP_FOLDER)

