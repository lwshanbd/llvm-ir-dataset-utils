"""Tool for deleting a lot of inodes in parallel."""

import os
import shutil

import ray

from absl import app
from absl import flags
from absl import logging

FLAGS = flags.FLAGS

flags.DEFINE_string('folder', None,
                    'The folder to delete all files/folders in.')

flags.mark_flag_as_required('folder')


@ray.remote
def delete_folder(folder_path):
  shutil.rmtree(folder_path)
  logging.warning(f'Deleted {folder_path}')
  return True


def main(_):
  subfolders = os.listdir(FLAGS.folder)
  subfolder_futures = []
  for subfolder in subfolders:
    subfolder_futures.append(
        delete_folder.remote(os.path.join(FLAGS.folder, subfolder)))
  ray.get(subfolder_futures)


if __name__ == '__main__':
  app.run(main)
