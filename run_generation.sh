#!/usr/bin/env bash
cd /home/jack/Desktop/Media_Studio || exit 1

VENV_PYTHON="/home/jack/Desktop/Media_Studio/venv/bin/python"

$VENV_PYTHON -u ONE_model_cfg.py \
  -p "A close up of a beautiful alien cyborg (face direct  camera:1,6), the cyborg has a steampunk  robotic body, human face long wild wild hair, sitting on a rock near a waterfall, it is wearing battle armor, and (staring at camera:1.7)" \
  -s 3360 \
  -n 200 \
  --cfg-start 1.5 \
  --cfg-step 0.01 \
  --steps 5 \
  -m comiccraftLCM_beta4.safetensors \
  --lora models/loras/more_details.safetensors \
  --lora-scale 0.25 \
  --vae models/vae/vae-ft-mse-840000-ema-pruned.safetensors \
  > generation.log 2>&1
