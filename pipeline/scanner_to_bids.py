from nipype.pipeline.engine import Workflow, Node
from nipype import DataGrabber, DataSink, IdentityInterface
import nipype.interfaces.fsl as fsl
import nipype.interfaces.freesurfer as fs
import nipype.interfaces.spm as spm
import nipype.interfaces.matlab as mlab
import os
from nipype.interfaces.utility import Function
from nipype.algorithms.misc import Gunzip
from pipeline.nodes.fssegmentHA_T1 import SegmentHA_T1 # freesurfer 7 hippocampus segmentation
from pipeline.nodes.qdec import QDec
from pipeline.nodes.adj_vol import AdjustVolume
from pipeline.nodes.get_mask_value import GetMaskValue
from pipeline.nodes.parse_scanner_dir import ParseScannerDir
from nipype.interfaces.utility import Rename

class ScannerToBIDS:

    def __init__(self, sublist, raw_data_dir, bids_root, temp_dir):
        self.subject_list = sublist  # self.mod_sublist(sublist)
        self.raw_data_dir = raw_data_dir
        self.bids_root = bids_root
        self.temp_dir = temp_dir

    def split_subject_ses(subject_str):
        # Split the input $subjectT$session in subject and session
        sub_str=str(subject_str)
        return subject_str.split('T')[0], subject_str.split('T')[1]

    def make_workflow(self):
        # Infosource: Iterate through subject names
        infosource = Node(interface=IdentityInterface(fields=['subject_str']), name="infosource")
        infosource.iterables = ('subject_str', self.subject_list)

        # Infosource: Iterate through subject names
        imgsrc = Node(interface=IdentityInterface(fields=['img']), name="imgsrc")
        imgsrc.iterables = ('img', ['uni'])

        parse_scanner_dir = Node(interface=ParseScannerDir(raw_data_dir=self.raw_data_dir),
                                 name='parse_scanner_dir')

        ro = Node(interface=fsl.Reorient2Std(), name='ro')

        mv = Node(interface=Rename(), name='mv')
        sink = Node(interface=DataSink(),
                    name='sink')
        sink.inputs.base_directory = self.bids_root
        sink.inputs.substitutions = [('mp2rage075iso', '{}'.format(str(sink.inputs._outputs.keys())))]
        #                              ('_uniden_UNI', ''),
        #                              ('_uniden_DEN', ''),
        #                              ('DEN_mp2rage_orig_reoriented_masked_maths', 'mUNIbrain_DENskull_SPMmasked'),
        #                              ('_mp2rage_orig_reoriented_maths_maths_bin', '_brain_bin')]
        sink.inputs.regexp_substitutions = [(r'_subject_str_2(?P<subid>[0-9][0-9][0-9])T(?P<sesid>[0-9])',
                                               r'sub-NeuroMET\g<subid>/ses-0\g<sesid>')]
        #    (r'c1{prefix}(.*).UNI_brain_bin.nii.gz'.format(prefix=self.project_prefix),
        #                                      r'{prefix}\1.UNI_brain_bin.nii.gz'.format(prefix=self.project_prefix)),
        #                                     (r'c1{prefix}(.*).DEN_brain_bin.nii.gz'.format(prefix=self.project_prefix),
        #                                      r'{prefix}\1.DEN_brain_bin.nii.gz'.format(prefix=self.project_prefix))]

        scanner_to_bids = Workflow(name='scanner_to_bids', base_dir=self.temp_dir)
        scanner_to_bids.connect(imgsrc, 'img', mv, 'format_string')
        scanner_to_bids.connect(infosource, 'subject_str', parse_scanner_dir, 'subject_id')
        scanner_to_bids.connect(parse_scanner_dir, 'uniden',  mv, 'in_file')
        scanner_to_bids.connect(mv, 'out_file', sink, '@uniden')

        return scanner_to_bids
