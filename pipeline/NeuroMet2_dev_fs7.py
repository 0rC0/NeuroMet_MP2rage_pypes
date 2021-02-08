from nipype.pipeline.engine import Workflow, Node
from nipype import DataGrabber, DataSink, IdentityInterface
import nipype.interfaces.fsl as fsl
import \
    nipype.interfaces.freesurfer as fs
import nipype.interfaces.spm as spm
import nipype.interfaces.matlab as mlab
import os
from nipype.interfaces.utility import Function
from nipype.algorithms.misc import Gunzip
import shutil
import glob
from pipeline.nodes.fssegmentHA_T1 import SegmentHA_T1 # freesurfer 7 hippocampus segmentation
from pipeline.nodes.qdec import QDec
from pipeline.nodes.adj_vol import AdjustVolume
from pipeline.nodes.get_mask_value import GetMaskValue



__author__ = "Andrea Dell'Orco"
__version__ = "2.4.0"
__maintainer__ = "Andrea Dell'Orco"
__email__ = "andrea.dellorco@charite.de"
__status__ = "Development"


class NeuroMet():

    def __init__(self, sublist, temp_dir, w_dir, omp_nthreads, raw_data_dir):

        self.subject_list = self.mod_sublist(sublist)
        self.raw_data_dir = raw_data_dir
        self.temp_dir = temp_dir
        self.w_dir = w_dir
        self.omp_nthreads = omp_nthreads
        self.overwrite = overwrite
        self.spm_path = '/opt/spm12'
        self.matlab_command = "matlab -nodesktop -nosplash"
        self.fsl_file_format = 'NIFTI_GZ'

        self.subject_prefix = 'NeuroMET'
        self.mask_suffix = '.SPMbrain_bin.nii.gz'
        self.mask_file = '/media/drive_s/AG/AG-Floeel-Imaging/02-User/NEUROMET/Structural_analysis_fs7/List_UNI_DEN_Mask.xlsx' # Todo:

        mlab.MatlabCommand.set_default_matlab_cmd(self.matlab_command)
        mlab.MatlabCommand.set_default_paths(self.spm_path)
        fsl.FSLCommand.set_default_output_type(self.fsl_file_format)  # fsl output format

    @staticmethod
    def mod_sublist(l):
        "for semplicity the subjects are given as i.e. 2001T1, they have to be transformed in 2_001_T1"
        return ['{0}_{1}_T{2}'.format(i[0], i[1:-2], i[-1]) for i in l]

    def copy_from_raw_data(self):
        """
        copy niftis from scanner directory and rename them. It assumes a Siemens Scanner directory structure
        :return:
        """
        for sub in self.subject_list:
            sub = self.subject_prefix + sub
            print('Copying {0}'.format(sub))
            den = glob.glob(self.raw_data_dir + '/{subnum}/{sub}/*MDC*/*UNI_DEN*/*.nii.gz'.format(subnum=sub[:-3],sub=sub))[0]  # should be only 1 file
            uni = glob.glob(self.raw_data_dir + '/{subnum}/{sub}/*MDC*/*UNI_Images*/*.nii.gz'.format(subnum=sub[:-3],sub=sub))[0]  # should be only 1 file
            sub_dest_dir = os.path.join(self.w_dir, sub)
            if uni and den:
                os.makedirs(sub_dest_dir, exist_ok=True)
                uni_name = sub + '.UNI_mp2rage_orig.nii.gz' # ToDo: BIDS Name
                den_name = sub + '.DEN_mp2rage_orig.nii.gz' # ToDo: BIDS Name
                if not os.path.isfile(os.path.join(sub_dest_dir, uni_name)) or self.overwrite:
                    shutil.copyfile(uni, os.path.join(sub_dest_dir, uni_name))
                    print('{0} copyed to {1}'.format(uni, os.path.join(sub_dest_dir, uni_name)))
                else:
                    print('File exists, Skipping copy')
                if not os.path.isfile(os.path.join(sub_dest_dir, den_name)) or self.overwrite:
                    shutil.copyfile(den, os.path.join(sub_dest_dir, den_name))
                    print('{0} copyed to {1}'.format(den, os.path.join(sub_dest_dir, den_name)))
                else:
                    print('File exists, Skipping copy')
            else:
                raise FileNotFoundError


    # Ref: http://nipype.readthedocs.io/en/latest/users/function_interface.html
    def copy_mask(in_file, fs_dir):
        """
        Copy an user modified mask to freesurfer folder

        in_file has to be connected with out_file from mri_mask
        fs_dir has to be connected with subjects_dir from fs_recon2,

        return fs_dir for recon2
        """
        import os
        import shutil

        out_file = os.path.join(fs_dir, 'recon_all/mri/brainmask.mgz')
        bk_file = os.path.join(fs_dir, 'recon_all/mri/brainmask_false.mgz')
        shutil.copy(out_file, bk_file)
        shutil.copy(in_file, out_file)

        return fs_dir


    def copy_freesurfer_dir(in_dir, sub_id, out_dir):
        """
        Copy the recon_all folder to subject dir as Subject_id.freesurfer
        """
        import os
        import shutil
        # mkdir NeuroMet034.freesurfer &&
        # curdir=$PWD && cd /home/WorkFlowTemp/NeuroMet/Neuromet2/FreeSurfer/_subject_id_034/fs_recon1 &&
        # tar -hcf - ./recon_all | tar -xf - -C $curdir && cd $curdir && cp -R recon_all NeuroMet034.freesurfer
        shutil.copytree(os.path.join(in_dir, 'recon_all'),
                           os.path.join(out_dir, '{1}{0}/{1}{0}.freesurfer'.format(sub_id, '{pref}'.format(pref=self.subject_prefix))))
        return out_dir


    def sublist(in_list, start=0, end=3):
        """
        Return a sublist of a given list
        """
        return in_list[start:end]


    def spm_tissues(in_list):
        """
        from a SPM NewSegment Tissues list, return GM, WM and CSf
        """
        return in_list[0][0], in_list[1][0], in_list[2][0]


    def gzip_spm(in_list):
        """
        gzip SPM native_tissues list
        SPM returns a list of lists [[file1], [file2],.....]
        """
        from os import system
        from os.path import isfile
        out_list = []
        for l in in_list:
            in_file = l[0]
            if isfile(in_file):
                cmdline = 'gzip -9 {0}'.format(in_file)
                system(cmdline)
                out_file = in_file + '.gz'
                out_list.append(list([out_file]))
            elif isfile(in_file + '.gz'):
                out_file = in_file + '.gz'
                out_list.append(list([out_file]))
        return out_list



    def make_sink(self):
        sink = Node(interface=DataSink(),
                    name='sink')
        sink.inputs.base_directory = self.w_dir
        sink.inputs.substitutions = [('_subject_id_',self.subject_prefix),
                                     ('_uniden_UNI', ''),
                                     ('_uniden_DEN', ''),
                                     ('DEN_mp2rage_orig_reoriented_masked_maths', 'mUNIbrain_DENskull_SPMmasked'),
                                     ('_mp2rage_orig_reoriented_maths_maths_bin', '_brain_bin')]
        sink.inputs.regexp_substitutions = [(r'c1{prefix}(.*).UNI_brain_bin.nii.gz'.format(prefix=self.subject_prefix),
                                             r'{prefix}\1.UNI_brain_bin.nii.gz'.format(prefix=self.subject_prefix)),
                                            (r'c1{prefix}(.*).DEN_brain_bin.nii.gz'.format(prefix=self.subject_prefix),
                                             r'{prefix}\1.DEN_brain_bin.nii.gz'.format(prefix=self.subject_prefix))]
        return sink


    def make_segment(self):
        # Ref: http://nipype.readthedocs.io/en/0.12.1/interfaces/generated/nipype.interfaces.fsl.utils.html#reorient2std
        ro = Node(interface=fsl.Reorient2Std(), name='ro')

        # Ref: http://nipype.readthedocs.io/en/latest/interfaces/generated/interfaces.spm/preprocess.html#segment
        seg = Node(interface=spm.NewSegment(channel_info=(0.0001, 60, (True, True))),
                       name="seg")

        spm_tissues_split = Node(
            Function(['in_list'], ['gm', 'wm', 'csf'], self.spm_tissues),
            name='spm_tissues_split')

        gzip = Node(Function(['in_list'], ['out_list'], self.gzip_spm),
                        name='gzip')

        segment = Workflow(name='Segment', base_dir=self.temp_dir)

        gunzip = Node(interface=Gunzip(), name='gunzip')
        # for new segment
        segment.connect(ro, 'out_file', gunzip, 'in_file')
        segment.connect(gunzip, 'out_file', seg, 'channel_files')
        segment.connect(seg, 'native_class_images', spm_tissues_split, 'in_list')
        return segment


    def make_mask(self):
        # The c2 and c3 images from SPM Segment are added to c1 to generate a mask
        mask = Workflow(name='Mask_UNI', base_dir=self.temp_dir)
        sum_tissues1 = Node(interface=fsl.maths.MultiImageMaths(op_string=' -add %s'),
                                name='sum_tissues1')
        sum_tissues2 = Node(interface=fsl.maths.MultiImageMaths(op_string=' -add %s'),
                                name='sum_tissues2')
        gen_mask = Node(interface=fsl.maths.UnaryMaths(operation='bin'),
                            name='gen_mask')
        mask.connect(sum_tissues1, 'out_file', sum_tissues2, 'in_file')
        mask.connect(sum_tissues2, 'out_file', gen_mask, 'in_file')
        return mask



    def make_neuromet1_workflow(self):

        # Infosource: Iterate through subject names
        infosource = Node(interface=IdentityInterface(fields=['subject_id']), name="infosource")
        infosource.iterables = ('subject_id', self.subject_list)

        # unidensource, return for every subject uni and den
        unidensource = Node(interface=IdentityInterface(fields=['uniden']), name="unidensource")
        unidensource.iterables = ('uniden', ['UNI', 'DEN'])


        info = dict(
            t1=[['subject_id', 'subject_id', 'uniden']]
        )

        datasource = Node(
            interface=DataGrabber(
                infields=['subject_id', 'uniden'], outfields=['t1']),
            name='datasource')
        datasource.inputs.base_directory = self.w_dir
        datasource.inputs.template = 'sub-{prefix}%s/{prefix}%s.%s_mp2rage_orig.nii.gz'.format(prefix=self.subject_prefix)
        datasource.inputs.template_args = info
        datasource.inputs.sort_filelist = False

        sink = self.make_sink()

        segment = self.make_segment()


        mask = self.make_mask()


        neuromet = Workflow(name=self.subject_prefix, base_dir=self.temp_dir)
        neuromet.connect(infosource, 'subject_id', datasource, 'subject_id')
        neuromet.connect(unidensource, 'uniden', datasource, 'uniden')
        neuromet.connect(datasource, 't1', segment, 'ro.in_file')

        # neuromet.connect()
        neuromet.connect(segment, 'spm_tissues_split.gm', mask, 'sum_tissues1.in_file')
        neuromet.connect(segment, 'spm_tissues_split.wm', mask, 'sum_tissues1.operand_files')
        neuromet.connect(segment, 'spm_tissues_split.csf', mask, 'sum_tissues2.operand_files')
        neuromet.connect(segment, 'spm_tissues_split.gm', sink, '@gm')
        neuromet.connect(segment, 'spm_tissues_split.wm', sink, '@wm')
        neuromet.connect(segment, 'spm_tissues_split.csf', sink, '@csf')
        neuromet.connect(segment, 'seg.bias_corrected_images', sink, '@biascorr')


        # neuromet.connect(comb_imgs, 'uni_brain_den_surr_add.out_file', sink, '@img')
        neuromet.connect(mask, 'gen_mask.out_file', sink, '@mask')
        neuromet.connect(segment, 'ro.out_file', sink, '@ro')

        return neuromet



    def make_comb_imgs(self):
        #Ref: http://nipype.readthedocs.io/en/1.0.4/interfaces/generated/interfaces.fsl/maths.html
        mask_uni_bias = Node(interface=fsl.maths.ApplyMask(),
                             name = 'mask_uni_bias')
        uni_brain_den_surr_bin = Node(interface=fsl.maths.UnaryMaths(operation = 'binv'),
                                      name = 'uni_brain_den_surr_bin')
        uni_brain_den_surr_mas = Node(interface=fsl.maths.ApplyMask(),
                                      name = 'uni_brain_den_surr_mas')
        uni_brain_den_surr_add = Node(interface=fsl.maths.BinaryMaths(operation = 'add'),
                           name = 'uni_brain_den_surr_add')

        comb_imgs = Workflow(name='CombinedImages', base_dir=self.temp_dir)
        comb_imgs.connect(mask_uni_bias, 'out_file', uni_brain_den_surr_bin, 'in_file')
        comb_imgs.connect(uni_brain_den_surr_bin, 'out_file', uni_brain_den_surr_mas, 'mask_file')
        comb_imgs.connect(uni_brain_den_surr_mas, 'out_file', uni_brain_den_surr_add, 'in_file')
        comb_imgs.connect(mask_uni_bias, 'out_file', uni_brain_den_surr_add, 'operand_file')
        return comb_imgs

    def make_freesurfer(self):

        # Ref: http://nipype.readthedocs.io/en/1.0.4/interfaces/generated/interfaces.freesurfer/preprocess.html#reconall
        fs_recon1 = Node(interface=fs.ReconAll(directive='autorecon1',
                                               mris_inflate='-n 15',
                                               hires=True,
                                               mprage=True,
                                               openmp=self.omp_nthreads),
                         name='fs_recon1',
                         n_procs=self.omp_nthreads)
        fs_mriconv = Node(interface=fs.MRIConvert(out_type='mgz'),
                          name='fs_mriconv')
        fs_vol2vol = Node(interface=fs.ApplyVolTransform(mni_152_reg=True),
                          name='fs_vol2vol')
        fs_mrimask = Node(interface=fs.ApplyMask(), name='fs_mrimask')
        fs_recon2 = Node(interface=fs.ReconAll(directive='autorecon2',
                                               hires=True,
                                               mprage=True,
                                               hippocampal_subfields_T1=False,
                                               openmp=self.omp_nthreads),
                         name='fs_recon2',
                         n_procs=self.omp_nthreads)

        fs_recon3 = Node(interface=fs.ReconAll(directive='autorecon3',
                                               hires=True,
                                               mprage=True,
                                               hippocampal_subfields_T1=False,
                                               openmp=self.omp_nthreads),
                         name='fs_recon3',
                         n_procs=self.omp_nthreads)

        copy_brainmask = Node(
            Function(['in_file', 'fs_dir'], ['fs_dir'], self.copy_mask),
            name='copy_brainmask')
        segment_hp = Node(interface=SegmentHA_T1(), name='segment_hp')



        freesurfer = Workflow(name='freesurfer', base_dir=self.temp_dir)
        freesurfer.connect(fs_recon1, 'T1', fs_vol2vol, 'target_file')
        freesurfer.connect(fs_mriconv, 'out_file', fs_vol2vol, 'source_file')
        freesurfer.connect(fs_recon1, 'T1', fs_mrimask, 'in_file')
        freesurfer.connect(fs_vol2vol, 'transformed_file', fs_mrimask, 'mask_file')
        freesurfer.connect(fs_mrimask, 'out_file', copy_brainmask, 'in_file')
        freesurfer.connect(fs_recon1, 'subjects_dir', copy_brainmask, 'fs_dir')
        freesurfer.connect(copy_brainmask, 'fs_dir', fs_recon2, 'subjects_dir')
        freesurfer.connect(fs_recon2, 'subjects_dir', fs_recon3, 'subjects_dir')
        freesurfer.connect(fs_recon3, 'subjects_dir', segment_hp, 'subjects_dir')

        return freesurfer


    def make_neuromet_fs_workflow(self):

        # Infosource: Iterate through subject names
        infosource = Node(interface=IdentityInterface(fields=['subject_id']), name="infosource")
        infosource.iterables = ('subject_id', self.subject_list)

        mask_source = Node(interface=GetMaskValue(
            csv_file='/media/drive_s/AG/AG-Floeel-Imaging/02-User/NEUROMET2/Structural_Analysis_fs7/List_UNI_DEN_Mask.xlsx'
        ), name='get_mask')

        # Datasource: Build subjects' filenames from IDs
        info = dict(
            mask = [['subject_id', '', 'subject_id', 'mask', '_brain_bin.nii.gz']],
            uni_bias_corr = [['subject_id', 'm', 'subject_id', '', 'UNI_mp2rage_orig_reoriented.nii']],
            den_ro = [['subject_id', '', 'subject_id', '', 'DEN_mp2rage_orig_reoriented.nii.gz']])

        datasource = Node(
            interface=DataGrabber(
                infields=['subject_id', 'mask'], outfields=['mask', 'uni_bias_corr', 'den_ro']),
            name='datasource')
        datasource.inputs.base_directory = self.w_dir
        datasource.inputs.template = '{pref}%s/%s{pref}%s.%s%s'.format(pref=self.subject_prefix)
        datasource.inputs.template_args = info
        datasource.inputs.sort_filelist = False

        sink = self.make_sink()

        comb_imgs = self.make_comb_imgs()

        freesurfer = self.make_freesurfer()

        neuromet_fs = Workflow(name='{pref}_fs'.format(pref=self.subject_prefix), base_dir=self.temp_dir)
        neuromet_fs.connect(infosource, 'subject_id', datasource, 'subject_id')
        neuromet_fs.connect(infosource, 'subject_id', mask_source, 'subject_id')
        neuromet_fs.connect(mask_source, 'mask_value', datasource, 'mask')
        neuromet_fs.connect(datasource, 'uni_bias_corr', comb_imgs, 'mask_uni_bias.in_file')
        neuromet_fs.connect(datasource, 'mask', comb_imgs, 'mask_uni_bias.mask_file')
        neuromet_fs.connect(datasource, 'den_ro', comb_imgs, 'uni_brain_den_surr_mas.in_file')

        neuromet_fs.connect(comb_imgs, 'uni_brain_den_surr_add.out_file', freesurfer, 'fs_recon1.T1_files')
        neuromet_fs.connect(datasource, 'mask', freesurfer, 'fs_mriconv.in_file')

        out_dir_source = Node(interface=IdentityInterface(fields=['out_dir'], mandatory_inputs=True), name = 'out_dir_source')
        out_dir_source.inputs.out_dir = self.w_dir

        copy_freesurfer_dir = Node(
            Function(['in_dir', 'sub_id', 'out_dir'], ['out_dir'], self.copy_freesurfer_dir),
            name='copy_freesurfer_dir')

        qdec = Node(interface=QDec(basedir=self.w_dir), name='qdec')

        adj_vol = Node(interface=AdjustVolume(
            diag_csv='/media/drive_s/AG/AG-Floeel-Imaging/02-User/NEUROMET2/Structural_Analysis_fs7/Diagnosen.csv'
        ), name='adj_vol')

        neuromet_fs.connect(comb_imgs, 'uni_brain_den_surr_add.out_file', sink, '@img')
        #neuromet_fs.connect(infosource, 'subject_id', copy_freesurfer_dir, 'sub_id')
        #neuromet_fs.connect(freesurfer, 'segment_hp.subjects_dir', copy_freesurfer_dir, 'in_dir')
        neuromet_fs.connect(freesurfer, 'segment_hp.subjects_dir', sink, '@recon_all')
        #neuromet_fs.connect(out_dir_source, 'out_dir', copy_freesurfer_dir, 'out_dir')

        #ToDo:
        # 04.12.2020 QDec + Adjust volumes. It hang if qdec is in a workflow, works a single interface
        #neuromet_fs.connect(freesurfer, 'segment_hp.subject_id', qdec, 'devnull')
        #neuromet_fs.connect(datasource, 'base_directory', qdec, 'basedir')
        #neuromet_fs.connect(qdec, 'stats_directory', adj_vol, 'stats_directory')
        #neuromet_fs.connect(qdec, 'stats_directory', sink, '@stat_dir')
        #neuromet_fs.connect(adj_vol, 'adjusted_stats', sink, '@adj_stats')



        return neuromet_fs
