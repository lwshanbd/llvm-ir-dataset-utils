"""Utilities related to portage."""

import subprocess
import shutil
import os


def get_portage_compiler_config(filename):
  if 'ruby' in os.uname().nodename:
    content = (
        'USE="unicode nls"\n'
        'CONFIG_SHELL="/p/lustre3/shan4/gentoo/bin/bash"\n'
        'DISTDIR="/p/lustre3/shan4/gentoo/var/cache/distfiles"\n'
        'ACCEPT_KEYWORDS="${ARCH} -~${ARCH}"\n'
        'COMMON_FLAGS="-O2 -pipe -Xclang -fembed-bitcode=all"\n'
        '\n'
        'CC="/p/lustre3/shan4/ir-llvm/utils/compiler_wrapper"\n'
        'CXX="/p/lustre3/shan4/ir-llvm/utils/compiler_wrapper++"\n'
        'CFLAGS="${COMMON_FLAGS}"\n'
        'CXXFLAGS="${COMMON_FLAGS}"\n'
        'FCFLAGS="${COMMON_FLAGS}"\n'
        'FFLAGS="${COMMON_FLAGS}"\n'
        '\n'
        'FEATURES="noclean"\n'
        '\n'
        'LC_MESSAGES=C.utf8'
    )
  else:
    content = (
        'COMMON_FLAGS="-O2 -pipe -Xclang -fembed-bitcode=all"\n'
        '\n'
        'CC="/data/ir-llvm/utils/compiler_wrapper"\n'
        'CXX="/data/ir-llvm/utils/compiler_wrapper++"\n'
        'CFLAGS="${COMMON_FLAGS}"\n'
        'CXXFLAGS="${COMMON_FLAGS}"\n'
        'FCFLAGS="${COMMON_FLAGS}"\n'
        'FFLAGS="${COMMON_FLAGS}"\n'
        '\n'
        'LC_MESSAGES=C.utf8\n'
        'FEATURES="noclean -ipc-sandbox -xattr -network-sandbox -pid-sandbox -sandbox -usersandbox -usersync -userfetch -userpriv"'
    )
  with open(filename, 'w') as file:
    file.write(content)


def portage_setup_compiler(build_dir):
  # Same as spack, path is variable depending upon the system.
  # Path to the Portage make.conf file within the build directory
  
  if 'ruby' in os.uname().nodename:
    source_config_folder = '/p/lustre3/shan4/gentoo/etc/portage/'
  else:
    source_config_folder = '/etc/portage/'
  config_path = os.path.join(build_dir, "etc/portage")
  make_conf_path = os.path.join(config_path, "make.conf")
  make_profile_path = os.path.join(config_path, "make.profile")
  # if os.path.exists(config_path):
  #   shutil.rmtree(config_path)
  shutil.copytree(source_config_folder, config_path)

  # Delete make.profile and make a new soft link to the default profile
  shutil.rmtree(make_profile_path)
  #shutil.rmtree(make_conf_path)
  if 'ruby' in os.uname().nodename:
    os.symlink('/p/lustre3/shan4/gentoo/etc/portage/make.profile', make_profile_path)
  else:
    os.symlink('/etc/portage/make.profile', make_profile_path)
  get_portage_compiler_config(make_conf_path)


def clean_binpkg(package_spec):
  pkgpath = ''
  if 'ruby' in os.uname().nodename:
    pkgpath = '/p/lustre3/shan4/gentoo/var/cache/binpkgs/' + package_spec
  else:
    pkgpath = '/var/cache/binpkgs/' + package_spec
  if os.path.exists(pkgpath):
    command_vector = ['rm', '-rf', pkgpath]
    subprocess.run(command_vector)
    sync_command = ['emaint', '--fix', 'binhost']
    subprocess.run(sync_command)
