"""

From: https://nipype.readthedocs.io/en/latest/devel/cmd_interface_devel.html
"""

from nipype.interfaces.base import (
    TraitedSpec,
    CommandLineInputSpec,
    CommandLine,
    File
)
import os

class GZipInputSpec(CommandLineInputSpec):
    input_file = File(desc="File", exists=True, mandatory=True, argstr="%s")

class GZipOutputSpec(TraitedSpec):
    output_file = File(desc="Zip file", exists = True)

class GZipTask(CommandLine):
    input_spec = GZipInputSpec
    output_spec = GZipOutputSpec
    _cmd = 'gzip -k'

    def _list_outputs(self):
            outputs = self.output_spec().get()
            outputs['output_file'] = os.path.abspath(self.inputs.input_file + ".gz")
            return outputs
