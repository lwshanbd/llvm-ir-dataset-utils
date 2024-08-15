#!/bin/bash
#SBATCH --job-name=list
#SBATCH --output=result.%j.out
#SBATCH --error=result.%j.err
#SBATCH --time=10:00:00
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=baodi.shan@stonybrook.edu


podman load -i $VAST/docker/portage.tar


podman run --privileged --security-opt=seccomp=/collab/usr/gapps/lcweg/containers/profiles/chown.json --shm-size=148gb -e PKGDIR=/data/packages  -v /p/lustre3/shan4:/data:Z  localhost/portage:latest /bin/bash -c "export PKGDIR=/data/packages && cd /data/ir-llvm/ && pip install . --break-system-packages && pip install mlgo-utils --break-system-packages && python /data/ir-llvm/list.py 10 150 && exit"