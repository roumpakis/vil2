import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import imageio.v3 as iio
import os

def extract_patches(image, patch_size, stride=None):
    if stride is None:
        stride = patch_size

    h, w = image.shape[:2]
    ph, pw = patch_size
    sh, sw = stride

    pad_h = (ph - (h % ph)) % ph
    pad_w = (pw - (w % pw)) % pw

    padded_image = np.pad(image, ((0, pad_h), (0, pad_w), (0, 0)), mode='constant', constant_values=0)
    padded_h, padded_w = padded_image.shape[:2]

    mask = np.ones((h, w), dtype=np.uint8)
    padded_mask = np.pad(mask, ((0, pad_h), (0, pad_w)), mode='constant', constant_values=0)

    patches, masks = [], []
    for i in range(0, padded_h - ph + 1, sh):
        for j in range(0, padded_w - pw + 1, sw):
            patches.append(padded_image[i:i+ph, j:j+pw])
            masks.append(padded_mask[i:i+ph, j:j+pw])
    
    return patches, masks

def plot_patches_with_masks(patches, masks, cols=5):
    rows = int(np.ceil(len(patches) / cols))
    fig, axes = plt.subplots(rows, cols * 2, figsize=(cols * 4, rows * 4))
    axes = axes.flatten()
    
    for idx, (patch, mask) in enumerate(zip(patches, masks)):
        axes[idx * 2].imshow(patch)
        axes[idx * 2].axis("off")
        axes[idx * 2].set_title(f"Patch {idx+1}")

        axes[idx * 2 + 1].imshow(mask, cmap="gray")
        axes[idx * 2 + 1].axis("off")
        axes[idx * 2 + 1].set_title(f"Mask {idx+1}")
    
    plt.tight_layout()
    plt.show()

def process_image(image_path, patch_size, stride=None):
    image = iio.imread(image_path)
    
    if image.ndim == 2:
        image = np.stack([image] * 3, axis=-1)
    
    patches, masks = extract_patches(image, patch_size, stride)
    plot_patches_with_masks(patches, masks)
    
    return patches, masks

def save_patches_with_masks(patches, masks, base_id, save_mask=True, output_dir="patches_output"):
    os.makedirs(output_dir, exist_ok=True)
    
    for idx, (patch, mask) in enumerate(zip(patches, masks)):
        patch_filename = os.path.join(output_dir, f"{base_id}_patch_{idx+1}.png")
        patch = (patch * 255).astype(np.uint8) if patch.max() <= 1 else patch.astype(np.uint8)
        Image.fromarray(patch).save(patch_filename)
        
        if save_mask:
            mask_filename = os.path.join(output_dir, f"{base_id}_mask_{idx+1}.png")
            Image.fromarray((mask * 255).astype(np.uint8)).save(mask_filename)

patches, masks = process_image(r"C:\Users\csdro\Downloads\app_12_2\autoeinai\to_new\EMSR795_results\S2\AFTER\AOI02_sentinel2.png", (256, 256))
patches_before, masks_before = process_image(r"C:\Users\csdro\Downloads\app_12_2\autoeinai\to_new\EMSR795_results\S2\BEFORE\AOI02_before_sentinel2.png", (256, 256))
patches_mask, masks_mask = process_image(r"C:\Users\csdro\Downloads\app_12_2\autoeinai\to_new\EMSR795_results\S2\MASK\\02_DEL_PRODUCT_2_1.png", (256, 256))

save_patches_with_masks(patches, masks, "EMSR795_AOI06_after", True, "patches_after")
save_patches_with_masks(patches_before, masks_before, "EMSR795_AOI06_before", False, "patches_before")
save_patches_with_masks(patches_mask, masks_mask, "EMSR795_AOI06_mask", False, "patches_mask")
