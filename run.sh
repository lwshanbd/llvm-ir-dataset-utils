#!/bin/bash


TOTAL_TASKS=150
TASKS_PER_JOB=150
JOB_COUNT=$((TOTAL_TASKS / TASKS_PER_JOB))

for ((i=0; i<JOB_COUNT; i++)); do
    START=$((i * TASKS_PER_JOB))
    EEND=$((START + TASKS_PER_JOB - 1))

    JOB_NAME="job_$i"

    SBATCH_FILE="job_$i.sbatch"
    cp template.sbatch res-slurm/$SBATCH_FILE

    sed -i "s/topXXX/$JOB_NAME/" res-slurm/$SBATCH_FILE
    sed -i "s/START/$START/" res-slurm/$SBATCH_FILE
    sed -i "s/EEND/$EEND/" res-slurm/$SBATCH_FILE

    sbatch res-slurm/$SBATCH_FILE
done
