import os

packages = []


def get_packages(parent_directory):
  valid_dirs_count = 0
  for first_level_subdir in os.listdir(parent_directory):
    first_level_path = os.path.join(parent_directory, first_level_subdir)
    if os.path.isdir(first_level_path):
      for second_level_subdir in os.listdir(first_level_path):
        second_level_path = os.path.join(first_level_path, second_level_subdir)
        if os.path.isdir(second_level_path):
          files = os.listdir(second_level_path)
          if any(file.endswith('.ebuild') for file in files):
            valid_dirs_count += 1
            packages.append(second_level_path[2:])


def processEbuild_cpp(file):
  with open(file, 'r', encoding='utf-8') as f:
    for line in f:
      if "toolchain-funcs" in line and "inherit" in line:
        return True
      elif "cmake" in line:
        return True
      elif "emake" in line:
        return True
      elif "CFLAGS" in line:
        return True
      elif "CXXFLAGS" in line:
        return True
      elif "toolchain" in line:
        return True
      elif "meson" in line:
        return True
  return False


def processEbuild_trunk(file):
  with open(file, 'r', encoding='utf-8') as f:
    for line in f:
      if "KEYWORDS" in line and "amd64 " in line and "~amd64 " not in line:
        return True
  return False


def readpackage(package):
  files = os.listdir(package)
  for file in files:
    if file.endswith('.ebuild'):
      with open(os.path.join(package, file), 'r', encoding='utf-8') as f:
        for line in f:
          print(line[:-1])
      return


def main():
  ebuild_directory = "./"
  get_packages(ebuild_directory)
  cpp_pkgs = []
  for pkg in packages:
    files = os.listdir(pkg)
    for file in files:
      if file.endswith('.ebuild'):
        if processEbuild_trunk(os.path.join(pkg, file)):
          if processEbuild_cpp(os.path.join(pkg, file)):
            cpp_pkgs.append(pkg)
            continue

  cpp_pkgs = list(set(cpp_pkgs))
  with open(
      "../../corpus_descriptions_test/portage_pkg.list", 'w',
      encoding='utf-8') as f:
    for i in cpp_pkgs:
      f.write(i + "\n")


if __name__ == "__main__":
  main()
