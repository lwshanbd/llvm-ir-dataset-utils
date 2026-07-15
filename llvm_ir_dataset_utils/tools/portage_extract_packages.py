"""Generate a Portage package list of C/C++ packages for corpus building.

Scans a Portage ebuild repository and selects packages that (a) look like they
build C/C++/native code and (b) are keyworded for amd64. The result is one
``category/package`` atom per line, suitable for feeding into
``portage_list_build.py``.

Because the repository is scanned live, category moves are handled for free:
a package that moved (for example ``sys-devel/llvm`` -> ``llvm-core/llvm``)
appears under its current name.

Example:

  python3 llvm_ir_dataset_utils/tools/portage_extract_packages.py \\
      --repo=/var/db/repos/gentoo \\
      --output=corpus_descriptions_test/portage_pkg.list \\
      --keywords=stable-testing
"""

import argparse
import os

# Top-level entries in a Portage repository that are not package categories.
NON_PACKAGE_DIRS = {
    'metadata', 'profiles', 'eclass', 'licenses', 'scripts', 'distfiles',
    'virtual', '.git'
}

# Markers in an ebuild that indicate it compiles C/C++/native code. This is a
# heuristic: it favours recall (build systems and toolchain usage) over
# precision. Non-native packages that slip through simply extract no bitcode and
# are recorded as failed builds downstream.
CPP_MARKERS = ('cmake', 'emake', 'meson', 'CFLAGS', 'CXXFLAGS')


def ebuild_is_cpp(ebuild_path):
  with open(ebuild_path, encoding='utf-8', errors='ignore') as ebuild:
    for line in ebuild:
      if 'inherit' in line and 'toolchain-funcs' in line:
        return True
      if 'toolchain' in line:
        return True
      if any(marker in line for marker in CPP_MARKERS):
        return True
  return False


def ebuild_amd64_keyword(ebuild_path):
  """Return (stable, testing) for the ebuild's amd64 KEYWORDS entry.

  Tokens are matched exactly so ``amd64`` (stable) and ``~amd64`` (testing) are
  distinguished from each other and from unrelated keywords such as
  ``amd64-linux`` or a hard-masked ``-amd64``.
  """
  stable = testing = False
  with open(ebuild_path, encoding='utf-8', errors='ignore') as ebuild:
    for line in ebuild:
      if 'KEYWORDS=' not in line:
        continue
      for token in line.replace('"', ' ').replace("'", ' ').split():
        if token == 'amd64':
          stable = True
        elif token == '~amd64':
          testing = True
  return stable, testing


def find_packages(repo, accept_testing):
  packages = []
  for category in sorted(os.listdir(repo)):
    category_path = os.path.join(repo, category)
    if category in NON_PACKAGE_DIRS or not os.path.isdir(category_path):
      continue
    for package in sorted(os.listdir(category_path)):
      package_path = os.path.join(category_path, package)
      if not os.path.isdir(package_path):
        continue
      for entry in os.listdir(package_path):
        if not entry.endswith('.ebuild'):
          continue
        ebuild_path = os.path.join(package_path, entry)
        if not ebuild_is_cpp(ebuild_path):
          continue
        stable, testing = ebuild_amd64_keyword(ebuild_path)
        if stable or (accept_testing and testing):
          packages.append(f'{category}/{package}')
          break
  return sorted(set(packages))


def main():
  parser = argparse.ArgumentParser(
      description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument(
      '--repo',
      default='/var/db/repos/gentoo',
      help='Path to the Portage ebuild repository.')
  parser.add_argument(
      '--output', required=True, help='Path to write the package list to.')
  parser.add_argument(
      '--keywords',
      choices=('stable', 'stable-testing'),
      default='stable-testing',
      help="'stable' keeps only amd64-stable packages; 'stable-testing' also "
      'includes ~amd64 (more coverage, less reliable builds).')
  args = parser.parse_args()

  packages = find_packages(args.repo, args.keywords == 'stable-testing')
  with open(args.output, 'w', encoding='utf-8') as output_file:
    output_file.write('\n'.join(packages) + '\n')
  print(f'Wrote {len(packages)} packages to {args.output}')


if __name__ == '__main__':
  main()
