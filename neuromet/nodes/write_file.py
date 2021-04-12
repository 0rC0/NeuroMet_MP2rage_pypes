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

class WriteFileInputSpec(BaseInterfaceInputSpec):

    #data_str = traits.Str(argstr="%s", desc="subject id of surface file", mandatory=True)
    csv_in = File(desc="Input CSV file", mandatory=True, exists=True)
    csv_file = File(desc="Output CSV file", mandatory=True)


class WriteFileOutputSpec(TraitedSpec):

    csv_file = File(exists=True, desc="Output CSV file")


class WriteFile(BaseInterface):
    """
    ToDo: Example Usage:

    """

    input_spec =WriteFileInputSpec
    output_spec = WriteFileOutputSpec



    def _run_interface(self, runtime, correct_return_codes=(0,)):

        # if the csv file doesn't exists create one an write the title line:
        df_in = pd.read_csv(self.inputs.csv_in).reset_index()

        csv_file = self.inputs.csv_file
        if not os.path.isfile(csv_file):
            df_in.transpose().to_csv(csv_file, index_label=False)
        else:
            df = pd.read_csv(csv_file).transpose().reset_index()
            lastcol = len(df.columns) + 1
            df[str(lastcol)] = df_in['1']
            df.transpose().drop('index').to_csv(csv_file, index_label=False)
        #print(self.inputs.data_str)
        return runtime

    def _list_outputs(self):

        outputs = self._outputs().get()
        outputs["csv_file"] = self.inputs.csv_file
        return outputs
