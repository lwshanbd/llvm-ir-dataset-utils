#!/bin/bash
# Build the Gentoo corpus image on a compute node and save it to shared storage
# so collection jobs can `podman load` it (podman storage is node-local, so the
# image must be shipped via a tarball on a shared filesystem).
#
# Run inside a flux allocation, e.g.:
#   flux run -q pdebug -N1 --exclusive -t 90m bash .packaging/gentoo/build_and_save.sh
#
# Env (with defaults):
#   REPO       repo checkout             (/p/lustre2/shan4/llvm-ir-dataset-utils)
#   IMAGE_TAG  image tag                 (llvm-ir-dataset-utils-gentoo:latest)
#   IMAGE_TAR  output tarball on Lustre  (/p/lustre2/shan4/gentoo-image.tar)
set -euo pipefail

REPO=${REPO:-/p/lustre2/shan4/llvm-ir-dataset-utils}
IMAGE_TAG=${IMAGE_TAG:-llvm-ir-dataset-utils-gentoo:latest}
IMAGE_TAR=${IMAGE_TAR:-/p/lustre2/shan4/gentoo-image.tar}

echo "build node=$(hostname) nproc=$(nproc) start=$(date -u)"
cd "$REPO"
podman build -t "$IMAGE_TAG" -f ./.packaging/Dockerfile.gentoo .
echo "saving image -> $IMAGE_TAR"
podman save "$IMAGE_TAG" -o "$IMAGE_TAR"
ls -lh "$IMAGE_TAR"
echo "done $(date -u)"
