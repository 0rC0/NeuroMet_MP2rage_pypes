# -*- coding: utf-8 -*-


"""
Emulate Freesurfer QDec wrapping *stats2table commands
"""
import os
import glob
import subprocess
from nipype import logging
from nipype.interfaces.base import (
    traits,
    TraitedSpec,
    Directory,
    BaseInterfaceInputSpec,
    BaseInterface
)
from traits.trait_types import Str

__docformat__ = "restructuredtext"
iflogger = logging.getLogger("nipype.interface")


class QDecInputSpec(BaseInterfaceInputSpec):

    basedir = traits.Str(desc="Base directory", argstr="%s", mandatory=True)
    fs_dir_template = traits.Str("*/*.freesurfer", argstr="%s", desc="Freesurfer directory template, default sub*/*.freesurfer", usedefault = True)
    devnull = traits.Str(desc="just a not-used input to put the node after another node")

class QDecOutputSpec(TraitedSpec):

    stats_directory = Directory(desc="stat_tables directory", mandatory=True)
    stdout = traits.List(traits.Str(), desc="stdout messages")
    stderr = traits.List(traits.Str(), desc="stderr messages")


class QDec(BaseInterface):
    """
    from pipeline.nodes import qdec
    q = qdec.QDec()
    q.inputs.basedir = '' # accepts path like /dir for structure like /dir/sub-001/sub-001.freesurfer
    q.run().outputs.stats_directory # return /dir/stat_tables
    """

    input_spec = QDecInputSpec
    output_spec = QDecOutputSpec

    def __make_sublist(self):
        sublist = glob.glob(self.inputs.basedir + '/*/*.freesurfer')
        return sublist

    def _run_interface(self, runtime, correct_return_codes=(0,)):

        os.environ["SUBJECTS_DIR"] = str(self.inputs.basedir)
        std_outputs_list = list()
        std_errors_list = list()
        commands =["asegstats2table --common-segs --meas volume --tablefile {d}/aseg.volume.stats.dat --statsfile=aseg.stats --subjects {s}",
                   "asegstats2table --common-segs --meas volume --tablefile {d}/wmparc.volume.stats.dat --statsfile=wmparc.stats --subjects {s}",
                   "aparcstats2table --hemi lh --parc aparc --meas area --tablefile {d}/lh.aparc.area.stats.dat --subjects {s}",
                   "aparcstats2table --hemi lh --parc aparc --meas volume --tablefile {d}/lh.aparc.volume.stats.dat --subjects {s}",
                   "aparcstats2table --hemi lh --parc aparc --meas thickness --tablefile {d}/lh.aparc.thickness.stats.dat --subjects {s}",
                   "aparcstats2table --hemi lh --parc aparc --meas meancurv --tablefile {d}/lh.aparc.meancurv.stats.dat --subjects {s}",
                   "aparcstats2table --hemi lh --parc aparc.a2009s --meas area --tablefile {d}/lh.aparc.a2009s.area.stats.dat --subjects {s}",
                   "aparcstats2table --hemi lh --parc aparc.a2009s --meas volume --tablefile {d}/lh.aparc.a2009s.volume.stats.dat --subjects {s}",
                   "aparcstats2table --hemi lh --parc aparc.a2009s --meas thickness --tablefile {d}/lh.aparc.a2009s.thickness.stats.dat --subjects {s}",
                   "aparcstats2table --hemi lh --parc aparc.a2009s --meas meancurv --tablefile {d}/lh.aparc.a2009s.meancurv.stats.dat --subjects {s}",
                   "aparcstats2table --hemi rh --parc aparc --meas area --tablefile {d}/rh.aparc.area.stats.dat --subjects {s}",
                   "aparcstats2table --hemi rh --parc aparc --meas volume --tablefile {d}/rh.aparc.volume.stats.dat --subjects {s}",
                   "aparcstats2table --hemi rh --parc aparc --meas thickness --tablefile {d}/rh.aparc.thickness.stats.dat --subjects {s}",
                   "aparcstats2table --hemi rh --parc aparc --meas meancurv --tablefile {d}/rh.aparc.meancurv.stats.dat --subjects {s}",
                   "aparcstats2table --hemi rh --parc aparc.a2009s --meas area --tablefile {d}/rh.aparc.a2009s.area.stats.dat --subjects {s}",
                   "aparcstats2table --hemi rh --parc aparc.a2009s --meas volume --tablefile {d}/rh.aparc.a2009s.volume.stats.dat --subjects {s}",
                   "aparcstats2table --hemi rh --parc aparc.a2009s --meas thickness --tablefile {d}/rh.aparc.a2009s.thickness.stats.dat --subjects {s}",
                   "aparcstats2table --hemi rh --parc aparc.a2009s --meas meancurv --tablefile {d}/rh.aparc.a2009s.meancurv.stats.dat --subjects {s}",
                   "asegstats2table --statsfile=hipposubfields.lh.T1.v21.stats --tablefile={d}/hipposubfields.lh.T1.v21.dat --subjects {s}",
                   "asegstats2table --statsfile=hipposubfields.rh.T1.v21.stats --tablefile={d}/hipposubfields.rh.T1.v21.dat --subjects {s}",
                   "asegstats2table --statsfile=amygdalar-nuclei.lh.T1.v21.stats --tablefile={d}/amygdalar-nuclei.lh.T1.v21.dat --subjects {s}",
                   "asegstats2table --statsfile=amygdalar-nuclei.rh.T1.v21.stats --tablefile={d}/amygdalar-nuclei.rh.T1.v21.dat --subjects {s}"
                   ]
        if not os.path.isdir(os.path.join(str(self.inputs.basedir), 'stats_tables')):
            os.mkdir(os.path.join(str(self.inputs.basedir), 'stats_tables'))
        for command in commands:
            #print(command.format(d=os.path.join(str(self.inputs.basedir), 'stats_tables'),
            #                                          s=' '.join(self.__make_sublist()).split()))
            process = subprocess.Popen(command.format(d=os.path.join(str(self.inputs.basedir), 'stats_tables'),
                                                      s=' '.join(self.__make_sublist())).split(),
                                        stdout=subprocess.PIPE)
            std_output, std_error = process.communicate()
            std_outputs_list.append(str(std_output))
            std_errors_list.append(str(std_error))
        setattr(self, '_std_outputs', std_outputs_list)  # Save result
        setattr(self, '_std_errors', std_errors_list)  # Save result
        return runtime

    def _list_outputs(self):

        outputs = self._outputs().get()
        outputs["stats_directory"] = os.path.join(str(self.inputs.basedir), 'stats_tables')
        outputs["stdout"] = getattr(self, '_std_outputs')
        outputs["stderr"] = getattr(self, '_std_errors')
        return outputs
