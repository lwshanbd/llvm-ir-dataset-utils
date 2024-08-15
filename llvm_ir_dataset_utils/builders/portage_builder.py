"""Module for building and extracting bitcode from applications using Portage"""

import subprocess
import os
import glob
import tempfile
import logging
import pathlib
import shutil
import re
import getpass
import ray

from mlgo.corpus import extract_ir_lib

from llvm_ir_dataset_utils.util import file
from llvm_ir_dataset_utils.util import portage as portage_utils
from llvm_ir_dataset_utils.util import extract_source_lib

BUILD_LOG_NAME = './portage_build.log'


def get_spec_command_vector_section(spec):
  return spec.split(' ')


def generate_emerge_command(package_to_build, threads, build_dir):
  command_vector = [
      'emerge',  # Portage package management command
      '--jobs={}'.format(
          64),  # Set the number of jobs for parallel building
      '-v',  # Enable verbose output
      '--load-average={}'.format(
          threads),  # Set the maximum load average for parallel builds
      '--config-root={}'.format(
          build_dir),  # Set the configuration root directory
      '--buildpkg',  # Build binary packages, similar to Spack's build cache
      '--usepkg',  # Use binary packages if available
      '--binpkg-respect-use=y',  # Ensure that binary package installations respect USE flag settings
      '--autounmask-write=y',  # Automatically write unmasking changes to the configuration
      package_to_build  # The package to install
  ]
  print(command_vector)
  return command_vector

def perform_build_again(package_name, assembled_build_command, corpus_dir, build_dir):
  logging.info(f"Portage building package {package_name}")
  environment = os.environ.copy()
  build_log_path = os.path.join(corpus_dir, BUILD_LOG_NAME)
  try:
    with open(build_log_path, 'w') as build_log_file:
      print(assembled_build_command)
      #print('uttst')
      subprocess.run(
          assembled_build_command,
          stdout=build_log_file,
          stderr=build_log_file,
          check=True,
          env=environment)
  except subprocess.SubprocessError:
    logging.warn(f"Failed AGAIN to build portage package {package_name}")
    #cleanup(corpus_dir)
    return False
  logging.info(f"Finished build portage package {package_name}")
  return True


def perform_build(package_name, assembled_build_command, corpus_dir, build_dir):
  logging.info(f"Portage building package {package_name}")
  environment = os.environ.copy()
  # Set DISTDIR and PORTAGE_TMPDIR to set the build directory for Portage
  environment['DISTDIR'] = build_dir
  environment['PORTAGE_TMPDIR'] = build_dir
  environment['ALLOW_BUILD_AS_ROOT'] = "1"
  # environment['PYTHON_TARGETS'] = "python3_10"
  print(build_dir)
  build_log_path = os.path.join(corpus_dir, BUILD_LOG_NAME)
  try:
    with open(build_log_path, 'w') as build_log_file:
      #print('uttst')
      subprocess.run(
          assembled_build_command,
          stdout=build_log_file,
          stderr=build_log_file,
          check=True,
          env=environment)
  except subprocess.CalledProcessError as e:
    print(f"Error running emerge: {e.stderr}")
    logging.warn(f"Failed to build portage package {package_name}")
    update_command = ['etc-update', '--automode', '-5']
    subprocess.run(update_command)
    print(f"Error running emerge: {e.stderr}; Let's try again!")
    return False
    return perform_build_again(package_name, assembled_build_command, corpus_dir, build_dir)
  logging.info(f"Finished build portage package {package_name}")
  return True


def extract_ir(package_spec, corpus_dir, build_dir, threads):
  # Not using the tmp directory
  build_directory = build_dir + "/portage/"
  if os.path.exists(build_directory):
    objects = extract_ir_lib.load_from_directory(build_directory, corpus_dir)
    relative_output_paths = extract_ir_lib.run_extraction(
        objects, threads, "llvm-objcopy", None, None, ".llvmcmd", ".llvmbc")
    extract_ir_lib.write_corpus_manifest(None, relative_output_paths,
                                         corpus_dir)
    extract_source_lib.copy_source(build_directory, corpus_dir)
    return
  
  # Using the tmp directory
  build_directory = "/var/tmp/portage/"
  package_spec = package_spec + "*"
  match = glob.glob(os.path.join(build_directory, package_spec))
  build_directory = match[0] + "/work"
  if build_directory is not None:
    objects = extract_ir_lib.load_from_directory(build_directory, corpus_dir)
    relative_output_paths = extract_ir_lib.run_extraction(
        objects, threads, "llvm-objcopy", None, None, ".llvmcmd", ".llvmbc")
    extract_ir_lib.write_corpus_manifest(None, relative_output_paths,
                                         corpus_dir)
    extract_source_lib.copy_source(build_directory, corpus_dir)
    shutil.rmtree(build_directory)


def cleanup(build_dir):
  shutil.rmtree(build_dir)
  return


def construct_build_log(build_success, package_name):
  return {
      'targets': [{
          'name': package_name,
          'build_log': BUILD_LOG_NAME,
          'success': build_success
      }]
  }


def build_package(dependency_futures,
                  package_name,
                  package_spec,
                  corpus_dir,
                  threads,
                  buildcache_dir,
                  build_dir,
                  cleanup_build=False):
  dependency_futures = ray.get(dependency_futures)
  #build_backup = build_dir.copy()
  for dependency_future in dependency_futures:
    if not dependency_future['targets'][0]['success']:
      logging.warning(
          f"Dependency {dependency_future['targets'][0]['name']} failed to build "
          f"for package {package_name}, not building.")
      #if cleanup_build:
      #  cleanup(package_name, package_spec, corpus_dir, uninstall=False)
      return construct_build_log(False, package_name, None)
  portage_utils.portage_setup_compiler(build_dir)
  portage_utils.clean_binpkg(package_spec)
  build_command = generate_emerge_command(package_spec, threads, build_dir)
  build_result = perform_build(package_name, build_command, corpus_dir,
                               build_dir)
  if build_result:
    extract_ir(package_spec, corpus_dir, build_dir, threads)
    logging.warning(f'Finished building {package_name}')
    
  try:
    cleanup(build_dir)
  except Exception as e:
    pass


  return construct_build_log(build_result, package_name)
