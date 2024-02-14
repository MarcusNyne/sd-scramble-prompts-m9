# Stable Diffusion: Scramble Prompts [m9]

A custom extension for [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui).

This extension scrambles a positive prompt to create variations of the prompt.  The intended purpose is to help create random variations to find a better version of an existing prompt.

## Overview

Modifications to the prompt may include:
   * Changing the order of tokens in a prompt
   * Removing prompt tokens
   * Changing the weight of prompt tokens

A 'token' is a phrase between commas, but not inside of parenthesis.  If you have parenthesis between commas, it is considered a single token.  For example:
- token one, token two
- token (one), token two
- (token, one), token two

The entire count/batch will be generated for each variation.  For example, if batch count is 2, batch size is 3, and variations are 10, then 60 images will be generated.

Recommended to only generate enough images per variation to determine if that variation is worth exploring. The above example would produce 6 images per variation, which is more than enough to know if the variation is good.

The same seed values will be used for each variation, regardless if it is random (-1) or fixed.

## Detailed settings

### Prompt Order

  * **Order Tokens**: The number of tokens to reorder.
    * A single "reorder" is a swap of two random tokens
    * When 0, all tokens will be randomly ordered
  * **Order Variance**: Randomly modify the count of tokens to reorder.
    * By plus/minus the specified amount
    * Ignored when Order Tokens is 0

### Prompt Reduction

   * **Reduce Tokens**: The number of tokens to remove.
     * Tokens are removed from the prompt entirely
     * Does not include Loras
   * **Reduce Variance**: Randomly modify the count of tokens to remove.
   * **Keep Tokens**: A list of keywords for tokens to keep.
     * As long as a token includes the specified keyword, it will not be reduced
     * Comma delimited

### Prompt Weight

   * **Weight Range**: The maximum amount to modify the weight in either direction.
     * If a change would take the weight below zero, the weight will be left as is
   * **Max Weight**: Maximum final weight.
     * When a change will take the weight over the max, the change is not made
     * For example, if the weight is 1, the max is 1.2, and the change is +0.3, the weight will be left at 1
   * **Weight Count**: The number of tokens that will have the weight changed.
   * **Weight Variance**: Randomly modify the count of tokens for a weight change.
   * **Lora Weight Range**: The maximum amount to modify a Lora weight.
     * When 0, no Loras are modified, otherwise all Loras will be modified

### Variant Generation

   * **Variations (count)**: The number of variations to produce
     * Each variation will generate (count * batch) images
   * **Create variation folders**: Create a new folder per variation
     * All images for a variation will be placed in the folder
     * Folders will be named YYMMDD-HHMM-NN, where NN is the variation number
