# NeuroMET MP2RAGE pipeline

Structural MRI preprocessing pipeline for MP2RAGE images.
Uses the T1w UNI and its denoised reconstruction (O’Brien et al., 2014) to achieve a T1w derivatives optimized for further processing with `fmriprep` and `freesurfer`

## About 

The T1w<sub>UNI</sub> image from the MP2Rage sequence has an optimal contrast for the brain, but its high background noise, caused by the high (7 T) magnetic field, makes it difficult to use this image as-is with various software packages.  On the other hand, the T1w denoised (T1w<sub>DEN</sub>) image loses contrast with the denoising process.
This pipeline processes the T1w images to achieve an image with the brain from the UNI image and the background from DEN image and thus an optimal contrast.

## Installation

*ToDo*

## Directory Structure
```
BIDS_ROOT
└── sub-sub001
    └── ses-03
        ├── anat
        │   ├── sub-sub001_ses-03_desc-UNIDEN_MP2RAGE.nii.gz
        │   ├── sub-sub001_ses-03_desc-UNI_MP2RAGE.nii.gz
        │   └── sub-sub001_ses-03_FLAIR.nii.gz
```
Note: there is a BIDS extension proposal for MP2Rage dataset. This directory structure is not actually a valid BIDS dataset.

## Usage

 See [JupyterNorebook](notebooks/NeuroMET.ipynb).
 
## Outputs

*ToDo*
