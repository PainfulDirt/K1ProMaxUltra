#!/usr/bin/env python3
"""Keep the repo results small: PNGs only for the informative cases, palette-quantized.
Every case keeps its results.json. Full fields stay in the work dir."""
import sys
from pathlib import Path

from PIL import Image

RES = Path(__file__).resolve().parents[1] / "results"
KEEP_CASES = {"STOCK_part_proxy_L2", "S1_part_proxy_L2", "S2_part_proxy_L2", "S7_part_proxy_L2",
              "S7_lidar_estimated_L2", "STOCK_lidar_estimated_L2", "REF_part_proxy_L2", "S7_part_proxy_L3",
              # review round (cfd-report s17)
              "S8_part_proxy_L2", "STOCK_part_proxy_r8_L2", "S8_lidar_estimated_L2", "S8_plate_proxy_L2",
              "S8_probe_proxy_L2"}
KEEP_IN_OTHERS = set()


def main():
    removed, saved = 0, 0
    for d in RES.iterdir():
        if not d.is_dir() or d.name.startswith("val_") or d.name == "figures":
            continue
        for png in d.glob("*.png"):
            if d.name not in KEEP_CASES and png.name not in KEEP_IN_OTHERS:
                removed += png.stat().st_size
                png.unlink()
                continue
            before = png.stat().st_size
            im = Image.open(png)
            if im.mode == "P":               # already quantized: leave the file (and git) untouched
                continue
            im = im.convert("RGB")
            im.quantize(colors=96, method=Image.Quantize.MEDIANCUT).save(png, optimize=True)
            saved += before - png.stat().st_size
    print(f"removed {removed / 1e6:.1f} MB of PNGs, quantization saved {saved / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
