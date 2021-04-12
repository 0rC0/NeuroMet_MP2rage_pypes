# -*- coding: utf-8 -*-


"""

"""
import os
import pandas as pd
import re
import shutil

from nipype import logging
from nipype.utils.filemanip import fname_presuffix, split_filename

from nipype import logging, LooseVersion
from nipype.utils.filemanip import fname_presuffix, check_depends
from nipype.interfaces.io import FreeSurferSource

from nipype.interfaces.base import (
    TraitedSpec,
    File,
    traits,
    Directory,
    InputMultiPath,
    OutputMultiPath,
    CommandLine,
    CommandLineInputSpec,
    isdefined,
    BaseInterfaceInputSpec,
    BaseInterface
)

from nipype.interfaces.freesurfer.base import FSCommand, FSTraitedSpec, FSTraitedSpecOpenMP, FSCommandOpenMP, Info
from nipype.interfaces.freesurfer.utils import copy2subjdir

__docformat__ = "restructuredtext"
iflogger = logging.getLogger("nipype.interface")

# Keeping this to avoid breaking external programs that depend on it, but
# this should not be used internally
FSVersion = Info.looseversion().vstring

class GetMaskValueInputSpec(BaseInterfaceInputSpec):


    subject_id = traits.Str(argstr="%s", desc="subject id", mandatory=True)
    csv_file = File(desc="Excel .XLSX file with list of mask", mandatory=True)


class GetMaskValueOutputSpec(TraitedSpec):

    mask_value = traits.Str(desc="String, UNI od DEN")


class GetMaskValue(BaseInterface):
    """
    ToDo: Example Usage:

    """

    input_spec = GetMaskValueInputSpec
    output_spec = GetMaskValueOutputSpec

    def get_mask_name(self):
        import pandas as pd
        mask_file = self.inputs.csv_file
        print(mask_file)
        df = pd.read_excel(mask_file, header=None, names=['ids', 'masks', 'note'])
        print(df)
        d = dict(zip(df.ids.values, df.masks.values))
        return d['NeuroMET' + self.inputs.subject_id]

    def _run_interface(self, runtime, correct_return_codes=(0,)):
        mask = self.get_mask_name()
        setattr(self, '_mask', mask)
        return runtime

    def _list_outputs(self):

        outputs = self._outputs().get()
        outputs["mask_value"] = getattr(self, '_mask')
        return outputs
