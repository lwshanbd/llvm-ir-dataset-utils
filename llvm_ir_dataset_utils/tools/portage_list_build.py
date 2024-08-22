import subprocess
import re
import json
import os
import sys


def parse_emerge_output(output):
    use_changes = re.findall(r'>=([^\s]+)\s+([^\n]+)', output)
    use_changes = [(re.sub(r'-[0-9.]+(?:-r[0-9]+)?$', '', package), flags) for package, flags in use_changes]
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
                
                
def run_emerge_pretend_again(package_name):
    try:
        result = subprocess.run(
            ['emerge', '-pv', '--autounmask-write=y', package_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError:
        update_command = ['etc-update', '--automode', '-5']
        subprocess.run(update_command)
        return None
    
def run_emerge_pretend(package_name):
    while True:
        try:
            result = subprocess.run(
                ['emerge', '-pv', '--autounmask-write=y', package_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            if "have been masked." in e.stderr:
                return 1
            use_changes = parse_emerge_output(e.stderr)
            update_package_use_custom(use_changes)
            continue

def extract_package_names(output):
    pattern = re.compile(r'(\S+?/\S+?)(?=-\d+(?:\.\d+)*(?:[-:_][a-zA-Z0-9.]+)*)')
    matches = pattern.findall(output)
    
    cleaned_matches = []
    for match in matches:
        if '/' in match and not match.endswith('/'):
            cleaned_matches.append(match)
    
    return cleaned_matches

def create_json_file(package):
    _ , name = package.split('/')
    name_with_slash = package.replace('/', '_')
    json_content = {
        "sources": [],
        "folder_name": name_with_slash,
        "build_system": "portage",
        "package_name": name,
        "package_spec": package
    }

    json_filename = f"/data/database/json/portage_{name_with_slash}.json"
    os.makedirs(os.path.dirname(json_filename), exist_ok=True)

    with open(json_filename, 'w') as json_file:
        json.dump(json_content, json_file, indent=2)

    return json_filename

def run_corpus_command(json_filename):
    command = [
        'python3', './llvm_ir_dataset_utils/tools/corpus_from_description.py',
        '--source_dir=/data/database-1/source',
        '--corpus_dir=/data/database-1/corpus',
        '--build_dir=/data/database-1/build',
        f'--corpus_description={json_filename}'
    ]
    try:
        subprocess.run(command, check=True)
        return 0
    except subprocess.CalledProcessError:
        return 1

def build(target_package):
    installed_packages = []
    # Skip finished packages.
    with open('../../corpus_descriptions_test/finished.list', 'r') as installed_list:
        for i in installed_list:
            installed_packages.append(i[:-1])

    output = run_emerge_pretend(target_package)
    if output == 1:
        print(f"{target_package} has been masked")
        return
    if output:
        package_names = extract_package_names(output)
        if target_package.replace('/', '_') in installed_packages or \
            os.path.exists('/data/database-1/corpus/' + target_package.replace('/', '_')):
            return
        for package in package_names:
            package_use_dir = '/etc/portage/package.use'
            custom_file_path = os.path.join(package_use_dir, 'custom')
            if os.path.exists(custom_file_path):
                os.remove(custom_file_path)
            name_with_slash = package.replace('/', '_')
            if name_with_slash in installed_packages or os.path.exists('/data/database-1/corpus/' + name_with_slash):
                renew_command = ['emerge', '--quiet']
                renew_command.append(package)
                try:
                    subprocess.run(renew_command, check=True)
                except subprocess.CalledProcessError:
                    print("Error to build depedency.")
                continue
            json_filename = create_json_file(package)
            run_corpus_command(json_filename)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(0)

    try:
        a = int(sys.argv[1])
        b = int(sys.argv[2])
    except ValueError:
        print("Please provide integer values for <a> and <b>.")
        sys.exit(1)
        
    with open('../../corpus_descriptions_test/portage_pkg.list', 'r') as file:
        for i, package_name in enumerate(file):
            if i < a:
                continue
            if i >= b:
                break
            package_name = package_name.strip()
            package_name = package_name.replace('_','/',1)
            build(package_name)