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
        df = pd.read_csv(mask_file, header=0, sep='\t')
        print(df)
        sid = self.inputs.subject_id
        d = dict(zip(df.participant.values, df['mask_(UNI_or_DEN)'].values))
        out = d['NeuroMET' + sid]
        return 'UNI' if out == 'UNI' else 'UNIDEN' if out == 'DEN' else ''

    def _run_interface(self, runtime, correct_return_codes=(0,)):
        mask = self.get_mask_name()
        setattr(self, '_mask', mask)
        return runtime

    def _list_outputs(self):

        outputs = self._outputs().get()
        outputs["mask_value"] = getattr(self, '_mask')
        return outputs

class SumStringsInputSpec(BaseInterfaceInputSpec):


    str1 = traits.Str(argstr="%s", desc="string1", mandatory=True)
    str2 = traits.Str(argstr="%s", desc="string2", mandatory=True)


class SumStringsOutputSpec(TraitedSpec):

    out_str = traits.Str(desc="Output string, sum of the twos as input")


class SumStrings(BaseInterface):
    """
    ToDo: Simple interface to sum two strings. i.e. Freesurfer subjects_dir and subject_id for the sink
    """

    input_spec = SumStringsInputSpec
    output_spec = SumStringsOutputSpec


    def _run_interface(self, runtime, correct_return_codes=(0,)):
        out_str = self.inputs.str1 + self.inputs.str2
        setattr(self, '_out_str', out_str)
        return runtime

    def _list_outputs(self):

        outputs = self._outputs().get()
        outputs["out_str"] = getattr(self, '_out_str')
        return outputs

class OsPathJoinInputSpec(BaseInterfaceInputSpec):


    str_list = traits.List(
        traits.Str(desc="strings to join as path", mandatory=True))



class OsPathJoinOutputSpec(TraitedSpec):

    out_path = traits.Str(desc="Output path as string")


class OsPathJoin(BaseInterface):
    """
    ToDo: Simple interface to sum two strings. i.e. Freesurfer subjects_dir and subject_id for the sink
    """

    input_spec = OsPathJoinInputSpec
    output_spec = OsPathJoinOutputSpec

    def __ospathjoin_recursive(self, l):
        if len(l) > 1:
            return (os.path.join(l[0], self.__ospathjoin_recursive(l[1:])))
        else:
            return l[0]

    def _run_interface(self, runtime, correct_return_codes=(0,)):
        out_path = self.__ospathjoin_recursive(self.inputs.str_list)
        setattr(self, '_out_path', out_path)
        return runtime

    def _list_outputs(self):

        outputs = self._outputs().get()
        outputs["out_path"] = getattr(self, '_out_path')
        return outputs