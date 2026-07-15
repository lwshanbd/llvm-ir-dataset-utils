# Gentoo corpus collection on an HPC cluster (flux + podman)

Scale-out harness for building the Portage C/C++ package list
(`corpus_descriptions_test/portage_pkg.list`) into per-package bitcode corpora
across many compute nodes. Uses rootless `podman` inside `flux` jobs.

Do **not** build or collect on a login node — it saturates shared resources.
Everything below runs inside `flux` allocations on compute nodes.

## Why an image tarball

`podman` storage is node-local (the compute node's `/tmp`/`/var/tmp`), so an
image built on one node is not visible on another. The image is therefore built
once and saved to a shared-filesystem tarball; each collection job `podman
load`s it on whatever node it lands on.

## 1. Build the image once and save it to Lustre

```bash
flux run -q pdebug -N1 --exclusive -t 90m bash .packaging/gentoo/build_and_save.sh
# -> writes $IMAGE_TAR (default /p/lustre2/shan4/gentoo-image.tar)
```

## 2. Fan the list out across nodes

```bash
.packaging/gentoo/submit_collection.sh 24     # 24 disjoint slices -> 24 flux jobs
flux jobs                                       # watch
tail -f /p/lustre2/shan4/collect-logs/slice_*.log
```

Each job loads the image, sets `ACCEPT_KEYWORDS="~amd64"` (so the testing
packages in the list emerge), and runs `portage_list_build.py` on its slice,
writing corpora to `$CORPUS_DIR` (default `/p/lustre2/shan4/corpus`).

## Resumable

A slice skips any package whose corpus directory already exists. Re-run
`submit_collection.sh` to continue after a time limit, a node failure, or to
pick up newly added packages. Failed builds leave a directory too (with just the
log), so they are not retried automatically — delete a corpus dir to force a
rebuild.

## Configuration (env vars)

| Var | Default | Meaning |
|-----|---------|---------|
| `IMAGE_TAR` | `/p/lustre2/shan4/gentoo-image.tar` | saved image tarball |
| `CORPUS_DIR` | `/p/lustre2/shan4/corpus` | corpus output (shared) |
| `LIST` | `corpus_descriptions_test/portage_pkg.list` | list path in the image |
| `QUEUE` | `pdebug` | flux queue |
| `TIME` | `12h` | per-job time limit |

## Scale note

`pdebug` caps jobs at 12h and ~24 nodes. Large packages (LLVM, qtwebengine,
chromium-derived, boost) can approach or exceed 12h alone, and the full ~6400
list is far more than 24×12h. For a full harvest use a longer queue (e.g.
`pall`) and/or several waves — the resume behavior makes waves safe. Start with
a small `submit_collection.sh` slice count to gauge throughput first.
