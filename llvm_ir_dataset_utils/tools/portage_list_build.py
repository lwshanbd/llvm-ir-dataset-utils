"""Batch-build a slice of the Portage package list into per-package corpora.

Reads a package list (``category/package`` per line, as produced by
``portage_extract_packages.py``), takes a ``[--start, --end)`` slice, and builds
each package's bitcode corpus by invoking ``corpus_from_description.py``.

Packages whose corpus directory already exists are skipped, so runs are
resumable and disjoint slices can run in parallel (one process/host per slice).
Build scratch is kept on a fast local directory (``--scratch-dir``, e.g. tmpfs)
while the finished corpus is written to ``--corpus-dir`` (e.g. shared storage).

Run inside the Gentoo corpus image. Testing (``~amd64``) packages only build if
the container accepts them, e.g. ``ACCEPT_KEYWORDS="~amd64"`` in
``/etc/portage/make.conf`` (the collection harness sets this).
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile

CORPUS_TOOL = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'corpus_from_description.py')


def read_slice(list_path, start, end):
  with open(list_path, encoding='utf-8') as list_file:
    atoms = [line.strip() for line in list_file if line.strip()]
  return atoms[start:end], len(atoms)


def folder_name(atom):
  # Filesystem-safe name; also how corpus_from_description lays out the corpus.
  return atom.replace('/', '_')


def already_attempted(corpus_dir, atom):
  return os.path.isdir(os.path.join(corpus_dir, folder_name(atom)))


def build_one(atom, corpus_dir, scratch_dir, threads):
  category, name = atom.split('/', 1)
  description = {
      'sources': [],
      'folder_name': folder_name(atom),
      'build_system': 'portage',
      'package_name': name,
      'package_spec': atom,
  }
  source_dir = os.path.join(scratch_dir, 'source')
  build_dir = os.path.join(scratch_dir, 'build', folder_name(atom))
  for directory in (source_dir, build_dir, corpus_dir):
    os.makedirs(directory, exist_ok=True)

  description_handle, description_path = tempfile.mkstemp(suffix='.json')
  with os.fdopen(description_handle, 'w') as description_file:
    json.dump(description, description_file)

  command = [
      sys.executable, CORPUS_TOOL,
      f'--source_dir={source_dir}',
      f'--corpus_dir={corpus_dir}',
      f'--build_dir={build_dir}',
      f'--corpus_description={description_path}',
      f'--thread_count={threads}',
      '--cleanup',
  ]
  try:
    subprocess.run(command, check=True)
    return True
  except subprocess.CalledProcessError:
    return False
  finally:
    os.unlink(description_path)


def main():
  parser = argparse.ArgumentParser(
      description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument(
      '--list',
      default='corpus_descriptions_test/portage_pkg.list',
      help='Package list file (category/package per line).')
  parser.add_argument(
      '--start', type=int, default=0, help='First list index (inclusive).')
  parser.add_argument(
      '--end',
      type=int,
      default=None,
      help='Last list index (exclusive); default is end of list.')
  parser.add_argument(
      '--corpus-dir', required=True, help='Where finished corpora are written.')
  parser.add_argument(
      '--scratch-dir',
      default='/tmp/corpus-scratch',
      help='Fast local directory for build/source scratch.')
  parser.add_argument(
      '--threads', type=int, default=os.cpu_count(), help='Threads per build.')
  args = parser.parse_args()

  atoms, total = read_slice(args.list, args.start, args.end)
  built = skipped = failed = 0
  for offset, atom in enumerate(atoms):
    index = args.start + offset
    if already_attempted(args.corpus_dir, atom):
      skipped += 1
      continue
    print(f'[{index}/{total}] building {atom}', flush=True)
    if build_one(atom, args.corpus_dir, args.scratch_dir, args.threads):
      built += 1
    else:
      failed += 1
      print(f'[{index}/{total}] FAILED {atom}', flush=True)
  print(f'slice [{args.start},{args.end}) done: '
        f'built={built} skipped={skipped} failed={failed}')


if __name__ == '__main__':
  main()
