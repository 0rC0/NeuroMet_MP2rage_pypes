# -*- coding: utf-8 -*-


"""
#The following formula is used
#Adjusted Volume = Raw Volume - Regression Slope * (TIV - Cohort Mean TIV)
#Reference Literature: Voevodskaya et al, 2014: The effects of intracranial volume adjustment approaches on multiple regional MRI volumes in healthy aging and Alzheimer's disease
"""
import os
import pandas as pd
import re
import shutil
import glob
import numpy as np
from sklearn.linear_model import LinearRegression
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


class AdjustVolumeInputSpec(BaseInterfaceInputSpec):

    stats_directory = Directory(desc="stat_tables directory", mandatory=True, exists=True)
    diag_csv = File(desc='CSV with diagnosis', exists=True, mandatory=True)


class AdjustVolumeOutputSpec(TraitedSpec):

    adjusted_stats = File(desc="a list of files with adjusted volumes")


class AdjustVolume(BaseInterface):
    """
    ToDo: Example Usage:

    """

    input_spec = AdjustVolumeInputSpec
    output_spec = AdjustVolumeOutputSpec

    def __get_sub_nr(self, sub):
        """
        given a subject IDs like PROJECT_000_T1 return the number i.e. 000
        it matches the first group of three numers
        :param sub: subject ID
        :return: subject number
        """
        p = re.compile(r'\d{3}')
        m = p.search(sub)
        return m.group(0)

    def get_vol_files(self):
        """
        :return: a list with all the .dat files in the stat directory
        """
        return glob.glob(self.inputs.stats_directory + '/*volume*.dat') + glob.glob(self.inputs.stats_directory + '/*quantification*.dat')

    def get_merged_df(self):
        """
        create a Pandas Dataframe with the values from all stats CSVs from QDec
        :return:
        """
        df_list = [ i for i in self.get_vol_files() if not i.endswith('aseg.volume.stats.dat')]
        aseg = [ i for i in self.get_vol_files() if i.endswith('aseg.volume.stats.dat')][0]

        df = pd.read_csv(aseg, sep='\t|;', header=0)
        df.columns = [i.lstrip().rstrip() for i in df.columns]
        for f in df_list:
            tmp_df = pd.read_csv(f, sep='\t', header=0)
            tmp_df.columns = [i.lstrip().rstrip() for i in tmp_df.columns]
            fst_col = tmp_df.columns[0]  # The subjects' columns can have different names
            #print(df.columns)
            df = df.join(tmp_df.set_index(fst_col), on='Measure:volume', rsuffix=f.split('/')[-1])
        # Diagnosis
        df['nums'] = df['Measure:volume'].apply(lambda x: self.__get_sub_nr(x))

        diag_df = pd.read_csv(self.inputs.diag_csv, sep=',', header=0)
        #print(diag_df)
        diag_df['nums'] = diag_df.Pseudonym.apply(lambda x: self.__get_sub_nr(x))
        df = df.join(diag_df.set_index('nums'), on='nums')

        return df

    def __get_slope_list(self, df):
        """
        linear regression
        :param df:
        :return: a list of slopes
        """
        l = list()
        etiv = df.EstimatedTotalIntraCranialVol.values
        rois = [ i for i in df.columns if not ('IntraCranial' in i or 'Diagnosen' in i or 'eTIV' in i or 'Measure' in i or 'num' in i or 'Pseudonym' in i)]
        for i in rois:
            lm = LinearRegression()
            X= etiv.reshape(-1, 1)
            lm.fit(X,df[i].values)
            l.append((i,lm.coef_[0]))
            #print((i,lm.coef_[0]))
        return l

    def __get_hem_means(self, df):
        """
        calculate average volume for the same roi in l and r hemisphear
        """
        lh_rois = [i for i in df.columns if i.startswith('lh')]
        for lh_roi in lh_rois:
            rh_roi = 'rh' + lh_roi[2:]
            mean_roi = 'mean' + lh_roi[2:]
            df[mean_roi] = (df[lh_roi].values + df[rh_roi].values)/2
        return df

    def __rename_hp_amyg_columns(self, df):
        """
        columns in Hp and Amygdala quantification begin with right_ or left_ instead of lh_ or rh_
        This function rename those fields
        """
        for i in df.columns:
            if i.startswith('left_'):
                df.rename(columns={i: 'lh_' + i[5:]})
            if i.startswith('right_'):
                df.rename(columns={i: 'rh_' + i[5:]})
        return df

    def __correct_volumes(self):

        df = self.get_merged_df()
        etiv = df.EstimatedTotalIntraCranialVol.values
        mean_etiv = etiv.mean() # average estimated total intracranial volume
        df_hc = df[(df.DiagnoseSCD_BL) == 0]
        slope_list = self.__get_slope_list(df_hc)
        #print(slope_list)
        adj_df = df[['Measure:volume', 'EstimatedTotalIntraCranialVol']]
        for i in slope_list:
            #print('{0}, slope: {1}, mean_etiv: {2}'.format(i[0], i[1], mean_etiv))
            adj_df[i[0]] = df[i[0]].values - i[1]*(df.EstimatedTotalIntraCranialVol.values - mean_etiv)
        adj_df = self.__rename_hp_amyg_columns(adj_df)
        adj_df = self.__get_hem_means(adj_df)
        return adj_df

    def _run_interface(self, runtime, correct_return_codes=(0,)):
        adj_vol_file = 'adjusted_volumes.csv'
        adj_df = self.__correct_volumes()
        adj_df.to_csv(adj_vol_file)
        setattr(self, '_adj_vol_file', adj_vol_file)
        return runtime

    def _list_outputs(self):

        outputs = self._outputs().get()
        outputs["adjusted_stats"] = getattr(self, '_adj_vol_file')
        return outputs
