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

class ReconAllStatsInputSpec(BaseInterfaceInputSpec):

    subject_id = traits.Str("recon_all", argstr="%s", desc="subject id of surface file", usedefault=True
    )
    subjects_dir = traits.String(
        mandatory=True, argstr="%s", desc="subject dir of surface file"
    )


class ReconAllStatsOutputSpec(TraitedSpec):

    subjects_dir = Directory(exists=True, desc="Freesurfer subjects directory.")
    subject_id = traits.Str(desc="Subject name")
    #stats_data = traits.Str(desc="Str a CSV line with the aseg.stat data")
    stats_csv = File(desc='path of the CSV containing the data')


class ReconAllStats(BaseInterface):
    """
    Example Usage:
    > from pipeline.nodes import recon_all_stats
    > aseg = recon_all_stats.ReconAllStats()
    > aseg.inputs.subjects_dir = '/media/drive_s/AG/AG-Floeel-Imaging/02-User/NEUROMET2/Structural_Analysis_fs7/Structural_analysis_quant'
    > aseg.inputs.subject_id = 'test_stats'
    > aseg.run().outputs.stats_data
    > aseg.run().outputs.stats_csv
    """

    input_spec = ReconAllStatsInputSpec
    output_spec = ReconAllStatsOutputSpec

    @staticmethod
    def _gen_subjects_dir():
        return os.getcwd()


    def _parse_aseg_stats(self, aseg):
        """
        Parse Freesurfer aseg.stats
        :param aseg: aseg.stats file
        :return: pd.Series with aseg.stats values
        """

        with open(aseg, 'r') as fs:
            ff = fs.read().split('\n')
        ff_meas = [i for i in ff if i.startswith('# Measure')]
        end = pd.DataFrame([i.split(',') for i in ff_meas])[[2, 3]]
        end.columns = ['0', '1']
        end = end.astype({'1': float})
        begin = pd.read_csv(aseg, comment='#', delim_whitespace=True, header=None, engine='python')[[4, 3]]
        begin.columns = ['0', '1']
        df = begin.append(end, ignore_index=True, sort=True)
        df_title = pd.DataFrame(['Measure:volume', self.inputs.subject_id]).transpose()
        df_title.columns = ['0', '1']
        df = df_title.append(df)
        #df.transpose().to_csv(csv_name)
        #return ', '.join(list(df['1'].apply(lambda x: str(x)))), csv_name
        #print(df)
        return df


    def _parse_aparc(self, aparc_file):
        begin = pd.read_csv(aparc_file, comment='#', delim_whitespace=True, header=None, engine='python')
        with open(aparc_file, 'r') as f:
            titles = [i for i in f.read().split('\n') if i.startswith('#')][-1].split(' ')[2:]
        begin.columns = titles
        begin = begin[['StructName', 'GrayVol']]
        begin.columns = ['0', '1']
        #print(begin)
        return begin
        

    def _run_interface(self, runtime, correct_return_codes=(0,)):

        aseg_file = os.path.join(self.inputs.subjects_dir, 'recon_all', 'stats', 'aseg.stats')
        out_df = self._parse_aseg_stats(aseg_file)
        for i in ['lh.aparc.stats', 'rh.aparc.stats', 'lh.aparc.a2009s.stats', 'rh.aparc.a2009s.stats']:
            aparc_file = os.path.join(self.inputs.subjects_dir, 'recon_all', 'stats', i)
            df = self._parse_aparc(aparc_file)
            out_df = pd.concat([out_df, df], axis=0)
            #print(out_df)
        #out = ','.join(list(out_df.apply(lambda x: str(x)).transpose()))
        #print(out)
        out_path = os.path.join(os.getcwd(), 'stats.csv')
        out_df.to_csv(out_path, index_label=False)
        setattr(self, '_out_path', out_path)  # Save result
        return runtime


    def _list_outputs(self):

        outputs = self._outputs().get()

        if isdefined(self.inputs.subjects_dir):
            outputs["subjects_dir"] = self.inputs.subjects_dir
        else:
            outputs["subjects_dir"] = self._gen_subjects_dir()

        outputs["subject_id"] = self.inputs.subject_id
        #outputs["stats_data"] = getattr(self, '_out')
        outputs["stats_csv"] = getattr(self, '_out_path')
        return outputs
