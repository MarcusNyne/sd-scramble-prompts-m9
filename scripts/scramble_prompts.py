import os
import copy
from datetime import datetime

from modules.processing import fix_seed
import modules.scripts as scripts
import gradio as gr
from modules.shared import opts
if hasattr(opts, 'hypertile_enable_unet'):  # webui >= 1.7
    from modules.ui_components import InputAccordion
else:
    InputAccordion = None

from modules import images
from modules.processing import Processed, process_images
from modules.shared import state

from m9_sd_libs.m_prompt import *

class Script(scripts.Script):
    def __init__(self):
        self.__inside = False
        self._prompt = None
        self._lastprompt = None

    def title(self):
        return "Scramble Prompts [M9]"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        tab = 't2i'  if not is_img2img else 'i2i'
        m9_label = 'Scramble Prompts [M9]'
        m9_accordian = "m9-scramble-prompts-accordion"
        m9_enabled = "m9-scramble-prompts-enabled"
        with (
            InputAccordion(False, label=m9_label, elem_id=f'{m9_accordian}-{tab}') if InputAccordion
            else gr.Accordion(m9_label, open=False, elem_id=f'{m9_accordian}-{tab}')
            as is_enabled
        ):
            if not InputAccordion:
                with gr.Row(variant='compact'):
                    is_enabled = gr.Checkbox(label='Enable Scramble Prompts', value=False, interactive=True, elem_id=f'{m9_enabled}-{tab}')

            with gr.Group(visible=True):
                with gr.Row():
                    with gr.Column(scale=19):
                        with gr.Row():
                            markdown = gr.Markdown("Scrambles a prompt by changing prompt order, removing prompts, and changing prompt weights.  The entire (count*batch) will be run against a prompt variation before running the next one.")
                        with gr.Row():
                            order_limit = gr.Slider(label="Order Prompts", info="Percent of prompts to reorder", minimum=0, maximum=100, value=20, step=5, elem_id=self.elem_id("order_limit"))
                        with gr.Row():
                            reduction_limit = gr.Slider(label="Remove Prompts", info="Percent of prompts to remove", minimum=0, maximum=30, value=0, step=5, elem_id=self.elem_id("reduction_limit"))
                        with gr.Row():
                            keep_tokens = gr.Textbox(label="Keep Prompts (,)", info="Prompts with these keywords will not be removed", lines=1, elem_id=self.elem_id("keep_tokens"))
                        with gr.Row():
                            weight_limit = gr.Slider(label="Modify Weights", info="Percent of prompts to modify weights", minimum=0, maximum=100, value=20, step=5, elem_id=self.elem_id("weight_limit"))
                        with gr.Row():
                            weight_range = gr.Number(label="Weight Range (+/-)", value=0.5, step=0.1, minimum=0, elem_id=self.elem_id("weight_range"))
                            weight_max = gr.Number(label="Max Weight", value=1.9, step=0.1, minimum=0, elem_id=self.elem_id("weight_max"))
                            lora_weight_range = gr.Number(label="Lora Weight Range (+/-)", value=0.2, minimum=0, step=0.1, elem_id=self.elem_id("lora_weight_range"))
                        with gr.Row():
                            cnt_variations = gr.Slider(label="Variations (count)", info="Number of prompt variations to produce", minimum=1, maximum=100, value=1, step=1, elem_id=self.elem_id("cnt_variations"))
                        with gr.Row():
                            chk_variation_folders = gr.Checkbox(label="Create variation folders", value=False, elem_id=self.elem_id("chk_variation_folders"))
                            chk_info_textfile = gr.Checkbox(label="Create info text file", value=False, elem_id=self.elem_id("chk_info_textfile"))                                

        return [is_enabled, order_limit, reduction_limit, chk_variation_folders, cnt_variations, keep_tokens, \
                    weight_range, weight_max, weight_limit, lora_weight_range, chk_info_textfile, markdown]

    def process(self, p, is_enabled, order_limit, reduction_limit, chk_variation_folders, cnt_variations, keep_tokens, \
                    weight_range, weight_max, weight_limit, lora_weight_range, chk_info_textfile, markdown):

        if not self.__inside and is_enabled:

            if self._cnt_variations>1:

                self.__inside = True

                try:
                    for var_ix in range (self._cnt_variations-1):
                        self.__print_variation_header(var_ix)

                        p.seed = self._original_seed

                        new_prompt = self.__generate_prompt(order_limit, reduction_limit, keep_tokens, \
                            weight_range, weight_max, weight_limit, lora_weight_range)

                        copy_p = copy.copy(p)
                        copy_p.prompt = new_prompt
                        if p.prompt==p.hr_prompt:
                            copy_p.hr_prompt = ''
                        if chk_variation_folders is True:
                            opts.data['directories_filename_pattern'] = self.__calc_dirpattern(chk_variation_folders, var_ix)

                        processed = process_images(copy_p)

                        self._processed_images += processed.images
                        self._processed_all_prompts += processed.all_prompts
                        self._processed_infotexts += processed.infotexts

                        if chk_info_textfile is True:
                            self.__write_info_file(var_ix, chk_variation_folders, processed.images[0].already_saved_as if len(processed.images)>0 else None)                        

                except:
                    print("Scramble Prompts [M9]: Exception during processing")

            self.__inside = False
            self.__print_variation_header(self._cnt_variations-1)
            if chk_variation_folders is True:
                opts.data['directories_filename_pattern'] = self.__calc_dirpattern(chk_variation_folders, self._cnt_variations-1)

    def __if_zint(self, inValue):
        return None if (inValue is None or inValue==0.0) else int(inValue)
    def __if_zfloat(self, inValue):
        return None if (inValue is None or inValue==0.0) else float(inValue)

    def __print_variation_header(self, in_iteration):
        print(f"Variation {in_iteration+1} of {self._cnt_variations} [{self._outpath_root}].\n")

    def __iter_folder(self, in_iteration):
        return f"{self._outpath_root}-{in_iteration+1:02d}"

    def __is_none(self, in_pattern):
        if type(in_pattern) is not str:
            return True
        in_pattern = in_pattern.lstrip().rstrip('\\ /').lower()
        return in_pattern == '' or in_pattern == '[none]'

    def __calc_dirpattern(self, chk_variation_folders, in_iteration):
        if chk_variation_folders is False:
            return self._original_dirpattern
        elif self.__is_none(self._original_dirpattern):
            return self.__iter_folder(in_iteration)
        return os.path.join(self._original_dirpattern, self.__iter_folder(in_iteration))

    def __write_info_file(self, in_iteration, chk_variation_folders, in_image_file):
        filepath = None
        try:
            if self._prompt and in_image_file:
                if chk_variation_folders is True:
                    filename = self.__iter_folder(in_iteration)+"-info.txt"
                else:
                    filename = os.path.basename(in_image_file)+"-info.txt"

                filepath = os.path.join(os.path.dirname(in_image_file), filename)
                self._prompt.SavePrompt(filepath, inLog=True)
        except:
            print(f"Failed to write info text file: {filepath}")

    def __generate_prompt(self, order_limit, reduction_limit, keep_tokens, \
                    weight_range, weight_max, weight_limit, lora_weight_range):
        self._prompt = mPrompt(inSeed=None, inPrompt=self._original_prompt)
        cnt_prompts = self._prompt.CountTokens('prompt')
        if cnt_prompts>0:
            if order_limit>0:
                self._prompt.ScrambleOrder(inLimit=int((self.__if_zint(order_limit)*cnt_prompts)/100) if order_limit<100 else None)
            weight_range=self.__if_zfloat(weight_range)
            if weight_limit is not None and weight_limit>0 and weight_range is not None and weight_range>0:
                self._prompt.ScrambleWeights(weight_range, inIsLora=False, inLimit=int((self.__if_zint(weight_limit)*cnt_prompts)/100), inMinOutput=0, inMaxOutput=self.__if_zfloat(weight_max))
            lora_weight_range=self.__if_zfloat(lora_weight_range)
            if lora_weight_range is not None and lora_weight_range>0:
                self._prompt.ScrambleWeights(lora_weight_range, inIsLora=True)
            reduction_limit = self.__if_zint(reduction_limit) 
            if reduction_limit is not None and reduction_limit>0:
                self._prompt.ScrambleReduction(inTarget=int((self.__if_zint(reduction_limit)*cnt_prompts)/100), inKeepTokens=keep_tokens)
        new_prompt = self._prompt.Generate()
        return new_prompt

    def before_process(self, p, is_enabled, order_limit, reduction_limit, chk_variation_folders, cnt_variations, keep_tokens, \
                    weight_range, weight_max, weight_limit, lora_weight_range, chk_info_textfile, markdown):

        if self.__inside or not is_enabled:
            return

        fix_seed(p)
        p.do_not_save_grid = True
        self._cnt_variations = int(cnt_variations)
        self._outpath_root = datetime.now().strftime("%y%m%d-%H%M")
        self._original_seed = p.seed
        self._original_prompt = p.prompt
        self._original_outpath = p.outpath_samples
        self._original_dirpattern = opts.data['directories_filename_pattern']
        self._processed_images = []
        self._processed_all_prompts = []
        self._processed_infotexts = []
        state.job_count = self._cnt_variations * p.n_iter

        if chk_variation_folders is True:
            opts.data['directories_filename_pattern'] = self.__calc_dirpattern(chk_variation_folders, self._cnt_variations-1)
        p.prompt = self.__generate_prompt(order_limit, reduction_limit, keep_tokens, \
            weight_range, weight_max, weight_limit, lora_weight_range)
        self._lastprompt = self._prompt

    def postprocess(self, p, processed, is_enabled, order_limit, reduction_limit, chk_variation_folders, cnt_variations, keep_tokens, \
                    weight_range, weight_max, weight_limit, lora_weight_range, chk_info_textfile, markdown):

        if self.__inside or not is_enabled:
            return

        self._processed_images += processed.images
        self._processed_all_prompts += processed.all_prompts
        self._processed_infotexts += processed.infotexts

        if chk_info_textfile is True:
            self._prompt = self._lastprompt
            self.__write_info_file(self._cnt_variations-1, chk_variation_folders, processed.images[0].already_saved_as if len(processed.images)>0 else None)
            
        processed.images = self._processed_images
        processed.all_prompts = self._processed_all_prompts
        processed.infotexts = self._processed_infotexts

        if chk_variation_folders is True:
            opts.data['directories_filename_pattern'] = self._original_dirpattern
