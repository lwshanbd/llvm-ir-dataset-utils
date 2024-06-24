import subprocess
import re
import json
import os

def run_emerge_pretend(package_name):
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
        print(f"Error running emerge: {e.stderr}")
        return None

def extract_package_names(output):
    pattern = re.compile(r'(\S+?/\S+?)(?=-\d)')
    matches = pattern.findall(output)
    return matches

def create_json_file(package):
    category, name = package.split('/')
    json_content = {
        "sources": [],
        "folder_name": name,
        "build_system": "portage",
        "package_name": name,
        "package_spec": package
    }

    json_filename = f"/data/database/json/portage_{name}.json"
    os.makedirs(os.path.dirname(json_filename), exist_ok=True)

    with open(json_filename, 'w') as json_file:
        json.dump(json_content, json_file, indent=2)

    return json_filename

def run_corpus_command(json_filename):
    command = [
        'python3', './llvm_ir_dataset_utils/tools/corpus_from_description.py',
        '--source_dir=/data/database/source',
        '--corpus_dir=/data/database/corpus',
        '--build_dir=/data/database/build',
        f'--corpus_description={json_filename}'
    ]
    try:
        print(command)
        subprocess.run(command, check=True)
        print(f"Successfully ran command for {json_filename}")
    except subprocess.CalledProcessError as e:
        print(f"Error running command for {json_filename}: {e}")

def build(package_name):
    
    output = run_emerge_pretend(package_name)
    print(output)
    if output:
        package_names = extract_package_names(output)
        print(package_names)
        for package in package_names:
            name = package.split('/')[1]
            package_path = '/data/database/corpus/' + name
            if os.path.exists(package_path):
                continue
            json_filename = create_json_file(package)
            run_corpus_command(json_filename)

if __name__ == "__main__":
    with open('corpus_descriptions_test/tmp1.list', 'r') as file:
        for i, package_name in enumerate(file):
            if i >= 50:
                break
            package_name = package_name.strip()
            build(package_name)
            
'''
python ./llvm_ir_dataset_utils/tools/corpus_from_description.py \
  --source_dir=/p/lustre3/shan4/database/source \
  --corpus_dir=/p/lustre3/shan4/database/corpus \
  --build_dir=/p/lustre3/shan4/database/build \
  --corpus_description=./corpus_descriptions_test/portage_hello.json

python ./llvm_ir_dataset_utils/tools/corpus_from_description.py \
  --source_dir=/data/database/source \
  --corpus_dir=/data/database/corpus \
  --build_dir=/data/database/build \
  --corpus_description=./corpus_descriptions_test/portage_hello.json

['llvm-objcopy --dump-section=.llvmcmd=$DATA/database/corpus/yasm/yasm-1.3.0/genmacro.o.cmd $DATA/database/build/yasm-build/portage/dev-lang/yasm-1.3.0-r1/work/yasm-1.3.0/genmacro.o /dev/null']  

['llvm-objcopy --dump-section=.llvmbc=$DATA/database/corpus/yasm/yasm-1.3.0/genmacro.o.cmd $DATA/database/build/yasm-build/portage/dev-lang/yasm-1.3.0-r1/work/yasm-1.3.0/genmacro.o /dev/null']  
  
'''