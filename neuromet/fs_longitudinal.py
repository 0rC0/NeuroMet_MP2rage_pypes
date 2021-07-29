from nipype.pipeline.engine import Workflow, Node
from nipype import DataGrabber, DataSink, IdentityInterface
import nipype.interfaces.fsl as fsl
import nipype.interfaces.freesurfer as fs
import nipype.interfaces.spm as spm
import nipype.interfaces.matlab as mlab
import os
import json
from nipype.interfaces.utility import Function, Merge
from nipype.algorithms.misc import Gunzip
from .nodes.fssegmentHA_T1 import SegmentHA_T1
from .nodes.qdec import QDec
from .nodes.adj_vol import AdjustVolume
from .nodes.utils import GetMaskValue, SumStrings, OsPathJoin
from .nodes.parse_scanner_dir import ParseScannerDir

# Nipype Workflow for the Freesurfer Longitudinal Pipeline

def get_freesurfer_longitudinal_workflow():
    
