import cv2
import numpy as np
from keras.models import load_model
def tests(model, images, ksize=128, mean_and_std=None):
    '''
    ksize: int, model input shape is (None, ksize, ksize, 1)
    mean_and_std: tuple as (mean, std)
    '''
    if isinstance(model, str):
        model = load_model(filepath=model)

    res = []
    for img in images:
        if isinstance(img, str):
            img = cv2.imread(img, 0)

        h, w = img.shape
        new_h = (h + ksize - 1) // ksize * ksize
        new_w = (w + ksize - 1) // ksize * ksize

        new_img = np.zeros((new_h, new_w, 1))
        new_img[:h, :w, 0] = img

        if new_img.ndim == 2:
            new_img = np.expand_dims(new_img, -1)

        if mean_and_std is not None:
            new_img -= mean_and_std[0]
            new_img /= mean_and_std[1]

        out_img = np.zeros(new_img.shape)
        for i in range(0, new_img.shape[0], ksize):
            for j in range(0, new_img.shape[1], ksize):
                x = new_img[i:i+ksize, j:j+ksize, :]
                y = model.predict(np.asarray([x]))[0]
                out_img[i:i+ksize, j:j+ksize, :] = y

        res.append((img, out_img[:h, :w, 0]))

    return res


import numpy as np
from skimage import morphology
def remove_small_regions(x, im_shape, rate=0.02):
    '''Morphologically removes small (less than size) connected regions of 0s or 1s
    x: ndarray, int or bool type
    im_shape: (width, height)
    '''
    x = x.copy()
    size = int(rate * np.prod(im_shape))
    morphology.remove_small_objects(x, min_size=size, in_place=True)
    morphology.remove_small_holes(x, min_size=size, in_place=True)
    return x


import numpy as np
from skimage import morphology, color
def image_mask(img, pred, mask=None, alpha=1):
    '''
    img: ndarray, opencv imread grayscale
    pred: ndarray, int or bool type
    Returns image with:
        predicted lung field filled with blue
        GT lung field outlined with red
    '''
    img_color = np.dstack((img, img, img))
    out_color = np.zeros(img.shape + (3,))
    boundary = morphology.dilation(pred, morphology.disk(3)) - pred
    out_color[boundary == 1] = [1, 0, 0]

    img_hsv = color.rgb2hsv(img_color)
    out_hsv = color.rgb2hsv(out_color)

    img_hsv[..., 0] = out_hsv[..., 0]
    img_hsv[..., 1] = out_hsv[..., 1] * alpha

    return color.hsv2rgb(img_hsv)


def IoU(y_true, y_pred):
    '''
    Returns Intersection over Union score for ground truth and predicted masks
    '''
    assert y_true.dtype == bool and y_pred.dtype == bool
    y_true_f = y_true.flatten()
    y_pred_f = y_pred.flatten()
    intersection = np.logical_and(y_true_f, y_pred_f).sum()
    union = np.logical_or(y_true_f, y_pred_f).sum()
    return (intersection + 1.) / (union + 1.)


def Dice(y_true, y_pred):
    '''
    Returns Dice Similarity Coefficient for ground truth and predicted masks
    '''
    assert y_true.dtype == bool and y_pred.dtype == bool
    y_true_f = y_true.flatten()
    y_pred_f = y_pred.flatten()
    intersection = np.logical_and(y_true_f, y_pred_f).sum()
    return (2. * intersection + 1.) / (y_true.sum() + y_pred.sum() + 1.)