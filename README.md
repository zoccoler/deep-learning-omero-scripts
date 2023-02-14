# Deep-learning OMERO scripts

## Description

This repository hosts OMERO scripts for running some deep-learning pre-trained models for images in an OMERO server with a GPU.

Currently the following scripts are available:
  - [Stardist2D]()
  
## Usage

### Configuring the environment

The scripts expect certain python packages to be installed, like tensorflow and stardist for example. Thus, you (or your IT department) should install the packages described in the [environment.yaml file]() (work in progess...) into the OMERO server. These packages expect that the server has a NVIDIA graphics card with updated drivers where CUDA can be installed.

### Loading scripts to server

Follow the official instructions to add scripts to an OMERO server: https://docs.openmicroscopy.org/omero/5.4.5/developers/scripts/index.html#downloading-and-installing-scripts

### Running scripts

Check [this blog post](https://biapol.github.io/blog/marcelo_zoccoler/omero_scripts/readme.html) to learn how to run the scripts.
