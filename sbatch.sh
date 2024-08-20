#!/bin/bash
#SBATCH --job-name=list-600
#SBATCH --output=result.%j.out
#SBATCH --error=result.%j.err
#SBATCH --time=22:00:00
#SBATCH --mail-type=END
#SBATCH --mail-user=baodi.shan@stonybrook.edu


podman load -i $VAST/docker/portage.tar

# podman run --privileged --security-opt=seccomp=/collab/usr/gapps/lcweg/containers/profiles/chown.json --shm-size=148gb -e PKGDIR=/data/packages  -v /usr/workspace/shan4:/data:Z  localhost/portage:latest /bin/bash -c "sh /data/podman_env.sh && source ~/.bashrc && which llvm-objcopy && /data/ir-llvm/utils/compiler_wrapper --version"

podman run --privileged --security-opt=seccomp=/collab/usr/gapps/lcweg/containers/profiles/chown.json --shm-size=148gb -e PKGDIR=/data/packages  -v /usr/workspace/shan4:/data:Z  localhost/portage:latest /bin/bash -c "sh /data/podman_env.sh && source ~/.bashrc && export PKGDIR=/data/packages && cd /data/ir-llvm/ && pip install . --break-system-packages && pip install mlgo-utils --break-system-packages && python /data/ir-llvm/list.py  300 600 && exit"