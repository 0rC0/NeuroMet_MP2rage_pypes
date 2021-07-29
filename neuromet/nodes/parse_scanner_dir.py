# -*- coding: utf-8 -*-


"""

"""
import os

from nipype import logging

from nipype.interfaces.base import (
    TraitedSpec,
    File,
    traits,
    Directory,
    BaseInterfaceInputSpec,
    BaseInterface
)

__docformat__ = "restructuredtext"
iflogger = logging.getLogger("nipype.interface")


class ParseScannerDirInputSpec(BaseInterfaceInputSpec):

    subject_id = traits.Str(argstr="%s", desc="subject id", mandatory=True)
    raw_data_dir = Directory(desc="Raw data directory", mandatory=True)


class ParseScannerDirOutputSpec(TraitedSpec):
    # ToDo: add JSON, every object should be a list
    # Ref: https://nipype.readthedocs.io/en/latest/api/generated/nipype.interfaces.base.traits_extension.html
    uni = File(desc='MP2Rage UNI File')
    uniden = File(desc='MP2Rage denoised UNI File')
    flair = File(desc='FLAIR')
    bold = File(desc='BOLD file')
    boldmag1 = File(desc='Field Map for BOLD, magnitude 1')
    boldmag2 = File(desc='Field Map for BOLD, magnitude 2')
    boldphdiff = File(desc='Field Map for BOLD, phasediff')


class ParseScannerDir(BaseInterface):
    """
    ToDo: Example Usage:

    """

    input_spec = ParseScannerDirInputSpec
    output_spec = ParseScannerDirOutputSpec

    def _split_sub_id_str(self):
        # Here is aspected an input like '2004T1', '2_004_T1' should be returned
        return '{0}_{1}_{2}'.format(self.inputs.subject_id[0], self.inputs.subject_id[1:4], self.inputs.subject_id[-2:])

    def _parse_field_maps(self, fm):
        # fm: list of fieldmaps containig folders, they should be 2
        # return: dict with filenames {'mangitude1': 'filepath'}
        #try:
        d = {'magnitude1': '', 'magnitude2': '', 'phasediff': ''}
        assert len(fm) == 2
        for i in fm:
            i = os.path.join(self.scanner_dir, i)
            #print(i)
            if len(os.listdir(i)) == 1:
                d['phasediff'] = os.path.join(i, os.listdir(i)[0])
            if len(os.listdir(i)) == 2:
                #print(os.listdir(i))
                d['magnitude1'] = os.path.join(i, [i for i in os.listdir(i) if '0001g' in i][0])
                d['magnitude2'] = os.path.join(i, [i for i in os.listdir(i) if '0001-e2' in i or '0001-2'][0])
        #print(d)
        return d
        #except:
        #    return None

    def _parse_scanner_dir(self):
        # Make scanner dir complete path
        raw_data_dir = self.inputs.raw_data_dir
        sub_str = self._split_sub_id_str()
        sub_raw_data_dir = os.path.join(raw_data_dir, 'NeuroMET'+sub_str[:-3], 'NeuroMET'+sub_str)
        scanner_dir = [i for i in os.listdir(sub_raw_data_dir) if i.startswith('MDC') and
                       os.path.isdir(os.path.join(sub_raw_data_dir, i))][0]
        scanner_dir = os.path.join(sub_raw_data_dir, scanner_dir)
        setattr(self, 'scanner_dir', scanner_dir)
        strs = ['UNI_Image', 'UNI_DEN', 'FLAIR', 'bold', 'gre_field_mapping_0']
        d = dict()
        # find corresponding dirs and grab the nifti if they are length 1
        for s in strs:
            try:
                d[s] = [i for i in os.listdir(scanner_dir) if s in i]
                if len(d[s]) == 0:
                    d[s] = ''
                elif len(d[s]) == 1:
                    d[s] = d[s][0]
                    src_dir = os.path.join(scanner_dir, d[s])
                    #print(s)
                    #print([i for i in os.listdir(src_dir) if i.endswith('.nii.gz')])
                    d[s] = os.path.join(src_dir, [i for i in os.listdir(src_dir) if i.endswith('.nii.gz') or i.endswith('.nii')][0])  # take the nifti
                elif len(d[s]) > 1 and 'field_map' in s:
                    #print(s)
                    d[s] = self._parse_field_maps(d[s])
            except:
                print('error with {}'.format(s))
        return d

    def _run_interface(self, runtime, correct_return_codes=(0,)):

        d = self._parse_scanner_dir()
        #print(d)
        try:
            setattr(self, '_uni', d['UNI_Image'])
            setattr(self, '_uni_den', d['UNI_DEN'])
        except:
            pass
        try:
            setattr(self, '_flair', d['FLAIR'])
            setattr(self, '_bold', d['bold'])
            setattr(self, '_boldmag1', d['gre_field_mapping_0']['magnitude1'])
            setattr(self, '_boldmag2', d['gre_field_mapping_0']['magnitude2'])
            setattr(self, '_boldphdiff', d['gre_field_mapping_0']['phasediff'])
        except:
            pass

        return runtime

    def _list_outputs(self):

        outputs = self._outputs().get()
        try:
            outputs["uni"] = getattr(self, '_uni')
            outputs["uniden"] = getattr(self, '_uni_den')
        except:
            pass
        try:
            outputs["bold"] = getattr(self, '_bold')
            outputs["flair"] = getattr(self, '_flair')
            outputs["boldmag1"] = getattr(self, '_boldmag1')
            outputs["boldmag2"] = getattr(self, '_boldmag2')
            outputs["boldphdiff"] = getattr(self, '_boldphdiff')
        except:
            pass
        return outputs
