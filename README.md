
# NeuroMET MP2RAGE pipeline
Structural MRI preprocessing pipeline to produce a T1w image optimized for further processing with `fmriprep` and `freesurfer`

## About 

The T1w<sub>UNI</sub> image from the MP2Rage sequence has an optimal contrast for the brain, but its high background noise, caused by the high (7 T) magnetic field, makes it difficult to use this image as-is with various software packages.  On the other hand, the T1w denoised (T1w<sub>DEN</sub>) image loses contrast with the denoising process.
This pipeline processes the T1w images to achieve an image with the brain from the UNI image and the background from DEN image and thus an optimal contrast.

## Usage

*ToDo*
