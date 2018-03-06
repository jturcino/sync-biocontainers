# sync-biocontainers

A Docker container for submitting Biocontainers docker-to-singularity sync jobs. When submitting a job, can pass an alternate actor id (`d2s_actor`), list of containers (`make_containers`), or a boolean flag to list the containers that need to be synced (`get_containers`). If no conditions are submitted, the actor generates a list of images to be generated and submits these as jobs to the `d2s-generic-jturcino` abaco actor (Docker container [here](https://hub.docker.com/r/jturcino/abaco-d2s-generic/)).

This readme will be filled out in more detail at a later date.
