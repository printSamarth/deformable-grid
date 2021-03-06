import torch
import torch.nn.functional as F
import numpy as np
from Utils import utils
from skimage.morphology import binary_dilation, disk
import math

def accuracy(poly, mask, pred_polys, grid_size):
    """
    Computes prediction accuracy

    poly: [batch_size, time_steps]
    pred_polys: [batch_size, time_steps,]
    Each element stores y*grid_size + x, or grid_size**2 for EOS

    mask: [batch_size, time_steps,]
    The mask of valid time steps in the GT poly. It is manipulated
    inside this function!

    grid_size: size of the grid in which the polygons are in    
    """
    idxs = np.argmax(pred_polys, axis=-1)
    for i,idx in enumerate(idxs):
        if pred_polys[i,idx] == grid_size**2:
            # If EOS
            if idx > np.sum(mask[i,:]):
                # If there are more predictions than
                # ground truth points, then extend mask
                mask[i, :idx] = 1.

        else:
            # If no EOS was predicted
            mask[i, :] = 1.
    
    corrects = pred_polys == poly

    corrects = corrects * mask
    percentage = np.sum(corrects, axis=-1)*1.0/np.sum(mask, axis=-1)

    return np.mean(percentage)

def train_accuracy(poly, mask, pred_polys, grid_size):
    """
    Computes prediction accuracy with GT masks

    poly: [batch_size, time_steps]
    pred_polys: [batch_size, time_steps,]
    Each element stores y*grid_size + x, or grid_size**2 for EOS

    mask: [batch_size, time_steps,]

    grid_size: size of the grid in which the polygons are in    
    accepts grid_size to be compatible with accuracy()
    """
    corrects = (pred_polys == poly).astype(np.float32)

    corrects = corrects * mask

    percentage = np.sum(corrects, axis=-1)*1.0/np.sum(mask, axis=-1)

    return np.mean(percentage)

def iou_from_mask(pred, gt):
    """
    Compute intersection over the union.
    Args:
        pred: Predicted mask
        gt: Ground truth mask
    """
    pred = pred.astype(np.bool)
    gt = gt.astype(np.bool)

    # true_negatives = np.count_nonzero(np.logical_and(np.logical_not(gt), np.logical_not(pred)))
    false_negatives = np.count_nonzero(np.logical_and(gt, np.logical_not(pred)))
    false_positives = np.count_nonzero(np.logical_and(np.logical_not(gt), pred))
    true_positives = np.count_nonzero(np.logical_and(gt, pred))

    union = float(true_positives + false_positives + false_negatives)
    intersection = float(true_positives)

    iou = intersection / union if union > 0. else 0.

    return iou

def iou_from_poly(pred, gt, width, height):
    """
    Compute IoU from poly. The polygons should
    already be in the final output size

    pred: list of np arrays of predicted polygons
    gt: list of np arrays of gt polygons
    grid_size: grid_size that the polygons are in

    """
    masks = np.zeros((2, height, width), dtype=np.uint8)

    if not isinstance(pred, list):
        pred = [pred]
    if not isinstance(gt, list):
        gt = [gt]

    for p in pred: 
        masks[0] = utils.draw_poly(masks[0], p)

    for g in gt:
        masks[1] = utils.draw_poly(masks[1], g)

    return iou_from_mask(masks[0], masks[1]), masks

def db_eval_boundary(foreground_mask, gt_mask, bound_th=2):
    """
    Compute mean,recall and decay from per-frame evaluation.
    Calculates precision/recall for boundaries between foreground_mask and
    gt_mask using morphological operators to speed it up.
    Arguments:
        foreground_mask (ndarray): binary segmentation image.
        gt_mask         (ndarray): binary annotated image.
    Returns:
        F (float): boundaries F-measure
        P (float): boundaries precision
        R (float): boundaries recall
    """
    assert np.atleast_3d(foreground_mask).shape[2] == 1
    bound_pix = bound_th if bound_th >= 1 else \
        np.ceil(bound_th * np.linalg.norm(foreground_mask.shape))
    # Get the pixel boundaries of both masks
    fg_boundary = seg2bmap(foreground_mask)
    gt_boundary = seg2bmap(gt_mask)
    fg_dil = binary_dilation(fg_boundary, disk(bound_pix))
    gt_dil = binary_dilation(gt_boundary, disk(bound_pix))
    # Get the intersection
    gt_match = gt_boundary * fg_dil
    fg_match = fg_boundary * gt_dil

    # Area of the intersection
    n_fg = np.sum(fg_boundary)
    n_gt = np.sum(gt_boundary)

    # % Compute precision and recall
    if n_fg == 0 and n_gt > 0:
        precision = 1
        recall = 0
    elif n_fg > 0 and n_gt == 0:
        precision = 0
        recall = 1
    elif n_fg == 0 and n_gt == 0:
        precision = 1
        recall = 1
    else:
        precision = np.sum(fg_match) / float(n_fg)
        recall = np.sum(gt_match) / float(n_gt)

    # Compute F measure
    if precision + recall == 0:
        F = 0
    else:
        F = 2 * precision * recall / (precision + recall);

    return F


def seg2bmap(seg, width=None, height=None):
    """
    From a segmentation, compute a binary boundary map with 1 pixel wide
    boundaries.  The boundary pixels are offset by 1/2 pixel towards the
    origin from the actual segment boundary.
    Arguments:
        seg     : Segments labeled from 1..k.
        width	  :	Width of desired bmap  <= seg.shape[1]
        height  :	Height of desired bmap <= seg.shape[0]
    Returns:
        bmap (ndarray):	Binary boundary map.
     David Martin <dmartin@eecs.berkeley.edu>
     January 2003
 """

    seg = seg.astype(np.bool)
    seg[seg > 0] = 1

    assert np.atleast_3d(seg).shape[2] == 1

    width = seg.shape[1] if width is None else width
    height = seg.shape[0] if height is None else height

    h, w = seg.shape[:2]

    ar1 = float(width) / float(height)
    ar2 = float(w) / float(h)

    assert not (width > w | height > h | abs(ar1 - ar2) > 0.01), \
        'Can''t convert %dx%d seg to %dx%d bmap.' % (w, h, width, height)

    e = np.zeros_like(seg)
    s = np.zeros_like(seg)
    se = np.zeros_like(seg)

    e[:, :-1] = seg[:, 1:]
    s[:-1, :] = seg[1:, :]
    se[:-1, :-1] = seg[1:, 1:]

    b = seg ^ e | seg ^ s | seg ^ se
    b[-1, :] = seg[-1, :] ^ e[-1, :]
    b[:, -1] = seg[:, -1] ^ s[:, -1]
    b[-1, -1] = 0

    if w == width and h == height:
        bmap = b
    else:
        bmap = np.zeros((height, width))
        for x in range(w):
            for y in range(h):
                if b[y, x]:
                    j = 1 + math.floor((y - 1) + height / h)
                    i = 1 + math.floor((x - 1) + width / h)
                    bmap[j, i] = 1;

    return bmap

