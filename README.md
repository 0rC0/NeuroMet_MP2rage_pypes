

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7181045.svg)](https://doi.org/10.5281/zenodo.7181045)


# NeuroMET MP2RAGE pipeline

Structural preprocesing pipeline for MP2Rage

## The pipeline 

The T1w<sub>UNI</sub> image from the MP2Rage sequence has an optimal contrast for the brain, but its high background noise, caused by the high (7 T) magnetic field, makes it difficult to use this image as-is with various software packages.  On the other hand, the T1w denoised (T1w<sub>DEN</sub>) image loses contrast with the denoising process.
This pipeline processes the T1w images to achieve an image with the brain from the UNI image and the background from DEN image and thus an optimal contrast.

## Usage

See Example Notebook. Only the variables in Settings section should be modified.

