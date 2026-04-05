"""
Evaluation metrics for NLOS reconstruction.
Compute PSNR, MAE, SSIM, runtime, and memory usage.
"""

import numpy as np
from scipy.signal import convolve2d


def compute_metrics(albedo_recon, depth_recon, albedo_gt, depth_gt, eps=1e-10):
    """
    Compute reconstruction quality metrics.

    Parameters:
      albedo_recon: reconstructed albedo (N, N)
      depth_recon: reconstructed depth (N, N)
      albedo_gt: ground truth albedo (N, N)
      depth_gt: ground truth depth (N, N)
      eps: small constant for numerical stability

    Returns:
      dict of metrics
    """
    # Normalize albedo to [0, 1]
    a_norm = albedo_recon / (albedo_recon.max() + eps)
    a_gt_norm = albedo_gt / (albedo_gt.max() + eps)

    # PSNR for albedo
    mse = np.mean((a_norm - a_gt_norm) ** 2)
    if mse < eps:
        psnr = 100.0
    else:
        psnr = 20 * np.log10(1.0 / np.sqrt(mse))

    # MAE for albedo
    albedo_mae = np.mean(np.abs(a_norm - a_gt_norm))

    # MAE for depth
    depth_mae = np.mean(np.abs(depth_recon - depth_gt))

    # SSIM for albedo (simplified)
    ssim = compute_ssim(a_norm, a_gt_norm)

    return {
        'psnr': psnr,
        'albedo_mae': albedo_mae,
        'depth_mae': depth_mae,
        'ssim': ssim,
    }


def compute_ssim(img1, img2, window_size=8, C1=0.01**2, C2=0.03**2):
    """
    Simplified SSIM computation.
    """
    mu1 = img1.mean()
    mu2 = img2.mean()
    sigma1_sq = img1.var()
    sigma2_sq = img2.var()
    sigma12 = ((img1 - mu1) * (img2 - mu2)).mean()

    numerator = (2 * mu1 * mu2 + C1) * (2 * sigma12 + C2)
    denominator = (mu1**2 + mu2**2 + C1) * (sigma1_sq + sigma2_sq + C2)

    if denominator < C2:
        return 1.0
    return numerator / denominator


def compute_runtime_stats(runtimes):
    """
    Compute statistics over multiple runtime measurements.
    """
    return {
        'mean': np.mean(runtimes),
        'std': np.std(runtimes),
        'min': np.min(runtimes),
        'max': np.max(runtimes),
        'median': np.median(runtimes),
    }
