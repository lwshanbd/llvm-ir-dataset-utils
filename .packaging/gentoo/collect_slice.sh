#!/bin/bash
# Load the saved image and build one [START, END) slice of the package list into
# per-package corpora on shared storage. Meant to run as a flux job (one slice
# per job); usually launched by submit_collection.sh, but can be run directly:
#   flux run -q pdebug -N1 --exclusive -t 12h bash collect_slice.sh 0 200
#
# Env (with defaults):
#   IMAGE_TAG   image tag              (llvm-ir-dataset-utils-gentoo:latest)
#   IMAGE_TAR   image tarball          (/p/lustre2/shan4/gentoo-image.tar)
#   CORPUS_DIR  corpus output (shared) (/p/lustre2/shan4/corpus)
#   LIST        list path in container (corpus_descriptions_test/portage_pkg.list)
#   LOGDIR      per-slice logs         (/p/lustre2/shan4/collect-logs)
START=${1:?usage: collect_slice.sh START END}
END=${2:?usage: collect_slice.sh START END}
IMAGE_TAG=${IMAGE_TAG:-llvm-ir-dataset-utils-gentoo:latest}
IMAGE_TAR=${IMAGE_TAR:-/p/lustre2/shan4/gentoo-image.tar}
CORPUS_DIR=${CORPUS_DIR:-/p/lustre2/shan4/corpus}
LIST=${LIST:-corpus_descriptions_test/portage_pkg.list}
LOGDIR=${LOGDIR:-/p/lustre2/shan4/collect-logs}

mkdir -p "$CORPUS_DIR" "$LOGDIR"
exec > "$LOGDIR/slice_${START}_${END}.log" 2>&1
echo "node=$(hostname) slice=[$START,$END) start=$(date -u)"

# podman storage is node-local; load the image once per node.
podman image exists "$IMAGE_TAG" || podman load -i "$IMAGE_TAR"

# ACCEPT_KEYWORDS="~amd64" lets the testing packages in the list emerge without
# per-package unmasking. Failed builds are recorded and skipped, not fatal.
podman run --rm --shm-size=10g -v "$CORPUS_DIR":/corpus "$IMAGE_TAG" bash -c "
  source /opt/venv/bin/activate
  export PATH=\$PATH:/usr/lib/llvm/22/bin
  echo 'ACCEPT_KEYWORDS=\"~amd64\"' >> /etc/portage/make.conf
  cd /workspace/llvm-ir-dataset-utils
  python3 llvm_ir_dataset_utils/tools/portage_list_build.py \
    --list='$LIST' --start=$START --end=$END \
    --corpus-dir=/corpus --scratch-dir=/tmp/corpus-scratch --threads=\$(nproc)
"
echo "slice done $(date -u)"
