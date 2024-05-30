import cv2

def create_thumbnail(image):
    """
    This function creates a thumbnail from given image

    Parameters
    ----------
    :param image: opencv image

    Returns
    -------
    :return a resized image
    """

    thumbnail_px = 150
    (height, width) = image.shape[:2]
    print(height, width)

    # If height is greater than width, resize image
    # proportionally by height, else by width
    if height >= width:
        ratio = thumbnail_px / float(height)
        image_dimensions = (int(width * ratio), thumbnail_px)
    else:
        ratio = thumbnail_px / float(width)
        image_dimensions = (thumbnail_px, int(height * ratio))

    # Resize the image
    resized_image = cv2.resize(image, image_dimensions, interpolation = cv2.INTER_AREA)

    return resized_image

# Code to be removed later
file = "../../images/000000523969.jpg"
image = cv2.imread(file)
rimage = create_thumbnail(image)
cv2.imwrite("thumbnail/image-1.jpg", rimage, [cv2.IMWRITE_JPEG_QUALITY, 90])