# Stable Diffusion: Scramble Prompts [m9]

A custom extension for [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui).

This extension scrambles a positive prompt to create variations of the prompt.  The intended purpose is to help create random variations to find a better version of an existing prompt.

*Not intended to be used while Tweak Weights [m9] is in use*

## Overview

Modifications to the prompt may include:
   * Changing the order of prompts
   * Removing prompts
   * Changing the weight of prompts

A 'prompt' is a phrase between commas, but not inside of parenthesis.  If you have parenthesis between commas, it is considered a single prompt.  For example:
- prompt one, prompt two
- prompt (one), prompt two
- (prompt, one), prompt two

The entire count/batch will be generated for each variation.  For example, if batch count is 2, batch size is 3, and variations are 10, then 60 images will be generated.

Recommended to only generate enough images per variation to determine if that variation is worth exploring. The above example would produce 6 images per variation, which is more than enough to know if the variation is good.

The same seed values will be used for each variation, regardless if it is random (-1) or fixed.

## Detailed settings

### Prompt Order

  * **Order Prompts**: The percent of prompts to reorder.

### Prompt Reduction

   * **Remove Prompts**: The number of prompts to remove.
     * prompts are removed entirely
     * Does not include Loras
   * **Keep Prompts**: A list of keywords for prompts to keep.
     * As long as a prompt includes the specified keyword, it will not be removed
     * Comma delimited

### Prompt Weight

   * **Modify Weights**: The percent of prompts that will have the weight changed.
   * **Weight Range**: The maximum amount to modify the weight in either direction.
     * If a change would take the weight below zero, the weight will be left as is
   * **Max Weight**: Maximum final weight.
     * When a change will take the weight over the max, the change is not made
     * For example, if the weight is 1, the max is 1.2, and the change is +0.3, the weight will be left at 1
   * **Lora Weight Range**: The maximum amount to modify a Lora weight.
     * When 0, no Loras are modified, otherwise all Loras will be modified

### Variant Generation

   * **Variations (count)**: The number of variations to produce
     * Each variation will generate (count * batch) images
   * **Create variation folders**: Create a new folder per variation
     * All images for a variation will be placed in the folder
     * Folders will be named YYMMDD-HHMM-NN, where NN is the variation number
   * **Create info text file**: Create an info file per variation
     * Contains the final prompt
     * Contains a log of changes to the prompt, so you can see what changed

## Help and Feedback

   * **Discord Server**
     * https://discord.gg/trMfHcTcsG

## m9 Prompts Catalog

   * **Scramble Prompts for Stable Diffusion**
     * Works with Automatic1111
     * Reorder, remove, modify weights of prompts
     * https://github.com/MarcusNyne/sd-scramble-prompts-m9

   * **Tweak Weights for Stable Diffusion**
     * Works with Automatic1111
     * Modify prompt weights using keywords
     * https://github.com/MarcusNyne/sd-tweak-weights-m9

   * **m9 Prompts for ComfyUI**
     * Works with ComfyUI
     * Includes nodes for Scramble Prompts and Tweak Weights
     * https://github.com/MarcusNyne/m9-prompts-comfyui
