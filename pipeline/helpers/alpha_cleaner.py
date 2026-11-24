#!/usr/bin/env python3
import os
import sys
import numpy as np
from PIL import Image

def remove_white_bg(img_path, out_path, threshold=242):
    img = Image.open(img_path).convert("RGBA")
    arr = np.array(img, dtype=np.uint8)
    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
    
    # Fully transparent for pure/near white
    is_pure_white = (r >= threshold) & (g >= threshold) & (b >= threshold)
    arr[is_pure_white, 3] = 0
    
    # Soft edge feathering between threshold - 20 and threshold
    low_thresh = threshold - 20
    is_near_white = (r >= low_thresh) & (g >= low_thresh) & (b >= low_thresh) & (~is_pure_white)
    
    # Calculate alpha linearly
    min_rgb = np.minimum(np.minimum(r, g), b).astype(float)
    alpha_factor = 1.0 - (min_rgb - low_thresh) / 20.0
    alpha_factor = np.clip(alpha_factor, 0.0, 1.0)
    arr[is_near_white, 3] = (arr[is_near_white, 3].astype(float) * alpha_factor[is_near_white]).astype(np.uint8)
    
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    Image.fromarray(arr).save(out_path, "PNG")
    print(f"Saved transparent PNG to {out_path}")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        remove_white_bg(sys.argv[1], sys.argv[2])
