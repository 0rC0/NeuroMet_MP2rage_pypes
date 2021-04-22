from nipype.pipeline.engine import Workflow, Node
from nipype import DataGrabber, DataSink, IdentityInterface
import nipype.interfaces.fsl as fsl
import nipype.interfaces.freesurfer as fs
import nipype.interfaces.spm as spm
import nipype.interfaces.matlab as mlab
import os
from nipype.interfaces.utility import Function
from nipype.algorithms.misc import Gunzip
from .nodes.fssegmentHA_T1 import SegmentHA_T1 # freesurfer 7 hippocampus segmentation
from .nodes.qdec import QDec
from .nodes.adj_vol import AdjustVolume
from .nodes.get_mask_value import GetMaskValue
from .nodes.parse_scanner_dir import ParseScannerDir
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
        #imgsrc = Node(interface=IdentityInterface(fields=['img']), name="imgsrc")
        #imgsrc.iterables = ('img', ['uni'])

        parse_scanner_dir = Node(interface=ParseScannerDir(raw_data_dir=self.raw_data_dir),
                                 name='parse_scanner_dir')

        ro = Node(interface=fsl.Reorient2Std(), name='ro')

        mv_uni = Node(interface=Rename(format_string='uni_'), name='mv_uni')
        mv_uniden = Node(interface=Rename(format_string='uniden'), name='mv_uniden')
        mv_flair = Node(interface=Rename(format_string='flair'), name='mv_flair')
        mv_bold = Node(interface=Rename(format_string='bold_'), name='mv_bold')
        mv_boldmag1 = Node(interface=Rename(format_string='boldmag1'), name='mv_boldmag1')
        mv_boldmag2 = Node(interface=Rename(format_string='boldmag2'), name='mv_boldmag2')
        mv_phasediff = Node(interface=Rename(format_string='boldphdiff'), name='mv_phasediff')
        sink = Node(interface=DataSink(),
                    name='sink')
        sink.inputs.base_directory = self.bids_root
        #sink.inputs.substitutions = [('mp2rage075iso', '{}'.format(str(sink.inputs._outputs.keys()))),
        #                              ('uni', 'uni.nii.gz')]#,
        #                              ('_uniden_DEN', ''),
        #                              ('DEN_mp2rage_orig_reoriented_masked_maths', 'mUNIbrain_DENskull_SPMmasked'),
        #                              ('_mp2rage_orig_reoriented_maths_maths_bin', '_brain_bin')]
        sink.inputs.regexp_substitutions = [(r'_subject_str_2(?P<subid>[0-9][0-9][0-9])T(?P<sesid>[0-9])/uni_',
                                               r'sub-NeuroMET\g<subid>/ses-0\g<sesid>/anat/sub-NeuroMET\g<subid>_ses-0\g<sesid>_UNI-T1w.nii.gz'),
                                            (r'_subject_str_2(?P<subid>[0-9][0-9][0-9])T(?P<sesid>[0-9])/uniden',
                                             r'sub-NeuroMET\g<subid>/ses-0\g<sesid>/anat/sub-NeuroMET\g<subid>_ses-0\g<sesid>_desc-UNI-T1-DEN.nii.gz'),
                                            (r'_subject_str_2(?P<subid>[0-9][0-9][0-9])T(?P<sesid>[0-9])/flair',
                                             r'sub-NeuroMET\g<subid>/ses-0\g<sesid>/anat/sub-NeuroMET\g<subid>_ses-0\g<sesid>_FLAIR.nii.gz'),
                                            (r'_subject_str_2(?P<subid>[0-9][0-9][0-9])T(?P<sesid>[0-9])/bold_',
                                             r'sub-NeuroMET\g<subid>/ses-0\g<sesid>/func/sub-NeuroMET\g<subid>_ses-0\g<sesid>_task-rest_bold.nii.gz'),
                                            (r'_subject_str_2(?P<subid>[0-9][0-9][0-9])T(?P<sesid>[0-9])/boldmag1',
                                             r'sub-NeuroMET\g<subid>/ses-0\g<sesid>/fmap/sub-NeuroMET\g<subid>_ses-0\g<sesid>_magnitude1.nii.gz'),
                                            (r'_subject_str_2(?P<subid>[0-9][0-9][0-9])T(?P<sesid>[0-9])/boldmag2',
                                             r'sub-NeuroMET\g<subid>/ses-0\g<sesid>/fmap/sub-NeuroMET\g<subid>_ses-0\g<sesid>_magnitude2.nii.gz'),
                                            (r'_subject_str_2(?P<subid>[0-9][0-9][0-9])T(?P<sesid>[0-9])/boldphdiff',
                                             r'sub-NeuroMET\g<subid>/ses-0\g<sesid>/fmap/sub-NeuroMET\g<subid>_ses-0\g<sesid>_phasediff.nii.gz')]
        #    (r'c1{prefix}(.*).UNI_brain_bin.nii.gz'.format(prefix=self.project_prefix),
        #                                      r'{prefix}\1.UNI_brain_bin.nii.gz'.format(prefix=self.project_prefix)),
        #                                     (r'c1{prefix}(.*).DEN_brain_bin.nii.gz'.format(prefix=self.project_prefix),
        #                                      r'{prefix}\1.DEN_brain_bin.nii.gz'.format(prefix=self.project_prefix))]

        scanner_to_bids = Workflow(name='scanner_to_bids', base_dir=self.temp_dir)
        #scanner_to_bids.connect(imgsrc, 'img', mv, 'format_string')
        scanner_to_bids.connect(infosource, 'subject_str', parse_scanner_dir, 'subject_id')
        scanner_to_bids.connect(parse_scanner_dir, 'uni',  mv_uni, 'in_file')
        scanner_to_bids.connect(parse_scanner_dir, 'uniden', mv_uniden, 'in_file')
        scanner_to_bids.connect(parse_scanner_dir, 'flair', mv_flair, 'in_file')
        scanner_to_bids.connect(parse_scanner_dir, 'bold', mv_bold, 'in_file')
        scanner_to_bids.connect(parse_scanner_dir, 'boldmag1', mv_boldmag1, 'in_file')
        scanner_to_bids.connect(parse_scanner_dir, 'boldmag2', mv_boldmag2, 'in_file')
        scanner_to_bids.connect(parse_scanner_dir, 'boldphdiff', mv_phasediff, 'in_file')
        scanner_to_bids.connect(mv_uni, 'out_file', sink, '@uni')
        scanner_to_bids.connect(mv_uniden, 'out_file', sink, '@uniden')
        scanner_to_bids.connect(mv_flair, 'out_file', sink, '@flair')
        scanner_to_bids.connect(mv_bold, 'out_file', sink, '@bold')
        scanner_to_bids.connect(mv_boldmag1, 'out_file', sink, '@boldmag1')
        scanner_to_bids.connect(mv_boldmag2, 'out_file', sink, '@boldmag2')
        scanner_to_bids.connect(mv_phasediff, 'out_file', sink, '@phasediff')

        return scanner_to_bids
