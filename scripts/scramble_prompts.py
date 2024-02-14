import os
import copy
from datetime import datetime

import modules.scripts as scripts
import gradio as gr

from modules import images
from modules.processing import Processed, process_images
from modules.shared import state

from code.m_prompt import *

class Script(scripts.Script):
    def __init__(self):
        pass

    def title(self):
        return "Scramble Prompts [M9]"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        with gr.Group(elem_id="m9-scramble-prompts"):
            with gr.Accordion("Scramble Prompts [M9]", open=False):
                is_enabled = gr.Checkbox(
                    label="Scramble Prompts enabled",
                    value=True,
                    interactive=True,
                    elem_id="m9-dynamic-prompts-enabled",
                )

                with gr.Group(visible=True):
                    with gr.Row():
                        with gr.Column(scale=19):
                            with gr.Row():
                                markdown = gr.Markdown("Scrambles a prompt by changing token order, removing tokens, and changing token weights.  The entire count/batch will be run against a prompt variation before running the next one.")
                            with gr.Row():
                                order_limit = gr.Number(label="Order Tokens (0=all)", infox="Causes tokens to be reordered", value=0, minimum=0, elem_id=self.elem_id("order_limit"))
                                order_variance = gr.Number(label="Order Variance (+/-)", infox="Modify count, when order tokens is not 0", value=None, minimum=0, elem_id=self.elem_id("order_variance"))
                            with gr.Row():
                                reduction_limit = gr.Number(label="Reduce Tokens (0=none)", infox="Causes tokens to be eliminated", value=0, minimum=0, elem_id=self.elem_id("reduction_limit"))
                                reduction_variance = gr.Number(label="Reduce Variance (+/-)", infox="Modify count in the range -N to +N", value=None, minimum=0, elem_id=self.elem_id("reduction_variance"))
                            with gr.Row():
                                keep_tokens = gr.Textbox(label="Keep Tokens (,)", infox="Tokens with these keywords in them will not be reduced", lines=1, elem_id=self.elem_id("keep_tokens"))
                            with gr.Row():
                                weight_range = gr.Number(label="Weight Range (+/-)", value=0.5, step=0.1, minimum=0, elem_id=self.elem_id("weight_range"))
                                weight_max = gr.Number(label="Max Weight", value=1.9, step=0.1, minimum=0, elem_id=self.elem_id("weight_max"))
                            with gr.Row():
                                weight_limit = gr.Number(label="Weight Count", value=20, step=1, minimum=0, elem_id=self.elem_id("weight_limit"))
                                weight_variance = gr.Number(label="Weight Variance (+/-)", infox="Modify count, when weight token count", value=None, minimum=0, elem_id=self.elem_id("weight_variance"))
                                lora_weight_range = gr.Number(label="Lora Weight Range (+/-)", value=0.2, minimum=0, step=0.1, elem_id=self.elem_id("lora_weight_range"))
                            with gr.Row():
                                cnt_variations = gr.Slider(label="Variations (count)", info="Number of variations to produce.  (count*batch) images are produced for each variation.", minimum=1, maximum=100, value=1, step=1, elem_id=self.elem_id("cnt_variations"))
                            with gr.Row():
                                chk_variation_folders = gr.Checkbox(label="Create variation folders", infox="Causes an image subfolder to be created for a variation", value=False, elem_id=self.elem_id("chk_variation_folders"))

        return [is_enabled, order_limit, order_variance, reduction_limit, reduction_variance, chk_variation_folders, cnt_variations, keep_tokens, \
                    weight_range, weight_max, weight_limit, weight_variance, lora_weight_range, markdown]

    def run(self, p, is_enabled, order_limit, order_variance, reduction_limit, reduction_variance, chk_variation_folders, cnt_variations, keep_tokens, \
                    weight_range, weight_max, weight_limit, weight_variance, lora_weight_range, markdown):

        if is_enabled is False:
            return process_images(p)

        p.do_not_save_grid = True
        state.job_count = cnt_variations

        images = []
        all_prompts = []
        infotexts = []

        original_seed = p.seed
        original_prompt = p.prompt
        original_outpath = p.outpath_samples
        outpath_root = datetime.now().strftime("%y%m%d-%H%M")
        cnt_variations = int(cnt_variations)
        for var_ix in range (cnt_variations):
            print(f"Variation {var_ix+1} of {cnt_variations}.\n")

            p.seed = original_seed
            test_prompt = mPrompt(inSeed=None, inPrompt=original_prompt)
            test_prompt.ScrambleOrder(inLimit=self.__if_zint(order_limit), inVariance=self.__if_zint(order_variance))
            weight_range=self.__if_zero(weight_range)
            if weight_range is not None:
                test_prompt.ScrambleWeights(weight_range, inIsLora=False, inLimit=self.__if_zint(weight_limit), inVariance=self.__if_zint(weight_variance), inMinOutput=0, inMaxOutput=self.__if_zero(weight_max))
            lora_weight_range=self.__if_zero(lora_weight_range)
            if lora_weight_range is not None:
                test_prompt.ScrambleWeights(lora_weight_range, inIsLora=True)
            reduction_limit = self.__if_zint(reduction_limit) 
            if reduction_limit is not None:
                test_prompt.ScrambleReduction(inTarget=self.__if_zint(reduction_limit), inRange=self.__if_zint(reduction_variance), inKeepTokens=keep_tokens)
            new_prompt = test_prompt.Generate()

            copy_p = copy.copy(p)
            copy_p.prompt = new_prompt
            if chk_variation_folders is True:
                copy_p.outpath_samples = os.path.join (original_outpath, f"{outpath_root}-{var_ix+1:02d}")   
            proc = process_images(copy_p)

            if original_seed==-1 and len(proc.all_seeds)>0:
                original_seed = proc.all_seeds[0]

            images += proc.images
            all_prompts += proc.all_prompts
            infotexts += proc.infotexts

        return Processed(p, images, p.seed, "", all_prompts=all_prompts, infotexts=infotexts)

    def __if_zero(self, inValue):
        return None if (inValue is None or inValue==0.0) else inValue
    def __if_zint(self, inValue):
        return None if (inValue is None or inValue==0.0) else int(inValue)
