import subprocess
import re
import os
from collections import OrderedDict
import json


def run_equery_depgraph(pkg):
    pkg = pkg.replace('_','/',1)
    print(f"pkg: {pkg}")
    command = f"emerge -pv {pkg}"
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        if "The following USE changes are necessary to proceed" in e.stderr:
                print(f"Package {pkg} needs USE flag")
        use_changes = parse_emerge_output(e.stderr)
        update_package_use_custom(use_changes)
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            print('good')
            return result.stdout
        except:
            if "have been masked." in e.stderr:
                print(f"Package {pkg} is masked.")
                return 1
            if "The following USE changes are necessary to proceed" in e.stderr:
                print(f"Package {pkg} STILL needs USE flag")
                return 2
            print(f"Error running equery: {e}")
            return None

def parse_emerge_output(output):
    use_changes = re.findall(r'>=([^\s]+)\s+([^\n]+)', output)
    use_changes = [(re.sub(r'-[0-9.]+(?:-r[0-9]+)?$', '', package), flags) for package, flags in use_changes]
    print(use_changes)
    return use_changes


def update_package_use_custom(use_changes):
    package_use_dir = '/etc/portage/package.use'
    custom_file_path = os.path.join(package_use_dir, 'custom')
    
    if not os.path.exists(package_use_dir):
        os.makedirs(package_use_dir)
    
    if not os.path.exists(custom_file_path):
        open(custom_file_path, 'a').close()
    
    with open(custom_file_path, 'r+') as f:
        content = f.read()
        for package, flags in use_changes:
            if package not in content:
                f.write(f"{package} {flags}\n")
                print(f"Added to {custom_file_path}: {package} {flags}")
            else:
                print(f"Package {package} already exists in {custom_file_path}")
    

    


def parse_depgraph(content):
    lines = content.split('\n')
    dependencies = []
    for line in lines[1:]:
        match = re.search(r"(\w+-[\w+/-]+?)(?:-\d[\w\._-]*)", line)
        if match:
            dependencies.append(match.group(1))

    return dependencies

def print_analysis(data):
    for version, info in data.items():
        print(f"Vim version: {version}")
        print(f"Total dependencies: {len(info['dependencies'])}")
        print(f"Package count: {info['package_count']}")
        print("\nDependencies:")
        for dep in sorted(set(info['dependencies'])):
            print(f"  - {dep}")
        print("\n" + "="*50 + "\n")
        return

def analyse_neither():
    failed = []
    successed = []
    with open('./portage-lists/neither.json') as neither_pkgs_files:
        neither_pkgs = json.load(neither_pkgs_files) 
    for pkg in neither_pkgs:
        if neither_pkgs[pkg] == 'N':
            failed.append(pkg)
        if neither_pkgs[pkg] == 'Y':
            successed.append(pkg)
    
    return failed, successed

def preprocessed_notinstalled_pkgs():
    notinstalled = []
    with open('./portage-lists/notinstalled.list', 'r') as notinstalled_file:
        for i in notinstalled_file:
            notinstalled.append(i[:-1])
    return notinstalled

def preprocessed_notinstalled_pkgs():
    installed = []
    with open('./portage-lists/installed.list', 'r') as installed_file:
        for i in installed_file:
            installed.append(i[:-1])
    return installed
    
def main():
    failed_pkgs, successed_pkgs = analyse_neither()
    
    notinstalled_pkgs = preprocessed_notinstalled_pkgs()
    installed_pkgs = preprocessed_notinstalled_pkgs()
    
    failed_pkgs.extend(notinstalled_pkgs)
    successed_pkgs.extend(installed_pkgs)
    
    error_dict = {}
    error_list = []
    mask_list = []
    use_list = []
    for pkg in failed_pkgs:
        content = run_equery_depgraph(pkg)
        if content == 1:
            mask_list.append(pkg)
            continue
        if content == 2:
            use_list.append(pkg)
            continue
        if content == None:
            error_list.append(pkg)
            print(f"Package {pkg} cannot be merged.")
        else:
            parsed_data = parse_depgraph(content)
            for i in parsed_data:
                if i.replace('/','_') not in successed_pkgs:
                    if i in error_dict:
                        error_dict[i] += 1
                    else:
                        error_dict[i] = 1

    sorted_dict = OrderedDict(sorted(error_dict.items(), key=lambda item: item[1], reverse=True))
    
    with open('./portage-lists/error.list', 'w') as file:
        for i in error_list:
            file.write(i+'\n')
    with open('./portage-lists/mask.list', 'w') as file:
        for i in mask_list:
            file.write(i+'\n')
            
    with open('./portage-lists/use.list', 'w') as file:
        for i in use_list:
            file.write(i+'\n')
    with open('./portage-lists/depedencies_pkgs.json', 'w') as file:
        json.dump(sorted_dict, file, indent=4)
    
if __name__ == "__main__":
    main()
