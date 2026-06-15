from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Launch Diffusers LoRA training for CineHuman AI Studio.")
    parser.add_argument("--dataset-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--model", default="stabilityai/stable-diffusion-xl-base-1.0")
    parser.add_argument("--resolution", type=int, default=1024)
    parser.add_argument("--rank", type=int, default=16)
    parser.add_argument("--steps", type=int, default=1000)
    args = parser.parse_args()

    dataset = Path(args.dataset_dir)
    if not dataset.exists():
        raise FileNotFoundError(dataset)
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        "-m",
        "accelerate.commands.launch",
        "train_text_to_image_lora_sdxl.py",
        "--pretrained_model_name_or_path",
        args.model,
        "--train_data_dir",
        str(dataset),
        "--resolution",
        str(args.resolution),
        "--rank",
        str(args.rank),
        "--max_train_steps",
        str(args.steps),
        "--output_dir",
        args.output_dir,
        "--mixed_precision",
        "fp16",
    ]
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())
