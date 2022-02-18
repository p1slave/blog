import os
from pprint import pprint
from blind_watermark import WaterMark
from PIL import Image, ImageEnhance, ImageDraw, ImageFont, ImageFilter

def convert2png(image_path, output_path):
    image = Image.open(image_path)
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    else:
        image = image.copy()

    image.save(output_path, "PNG")

# Convert to RGBA mode first to include the transparency and then invert 
# RGB channel but leave the transparency unchanged
def invert_transparent_img(image_path):
    img = Image.open(image_path)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    r, g, b, a = img.split()

    def invert(image):
        return image.point(lambda p: 255 - p)

    r, g, b = map(invert, (r, g, b))

    img2 = Image.merge(img.mode, (r, g, b, a))
    return img2

def make_grayish_img(image_path):
    # Less than (125, 125, 125) to (25, 25, 25)
    # Greater than (125, 125, 125) to (225, 225, 225)
    img = Image.open(image_path)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    r, g, b, a = img.split()

    def invert(image):
        return image.point(lambda p: 25 if p < 125 else 225)

    r, g, b = map(invert, (r, g, b))

    img2 = Image.merge(img.mode, (r, g, b, a))
    return img2

# The blind watermark is not working well on screenshots and may need more tuning on params
def add_blind_watermark(original_file, watermark_file, output_file):
    bwm1 = WaterMark(password_wm=1, password_img=1)
    bwm1.read_img(original_file)
    bwm1.read_wm(watermark_file)
    bwm1.embed(output_file)
    return output_file

def extract_blind_watermark(watermarked_file, extracted_wm_file, wm_shape=(64, 64)):
    bwm1 = WaterMark(password_wm=1, password_img=1)
    # notice that wm_shape is necessary
    bwm1.extract(watermarked_file, wm_shape=wm_shape, out_wm_name=extracted_wm_file)
    return extracted_wm_file

def add_blind_str_watermark(initial_file, password, output_file, times=1):
    original_file = initial_file
    for i in range(0, times):
        # print("Round: %s" % i)
        bwm1 = WaterMark(password_wm=1, password_img=1)
        bwm1.read_img(original_file)
        bwm1.read_wm(password, mode='str')
        bwm1.embed(output_file)

    # len_wm = len(bwm1.wm_bit)
    # print(len_wm)

    return output_file

def extract_blind_str_watermark(watermarked_file, len_wm):
    bwm1 = WaterMark(password_wm=1, password_img=1)
    # notice that wm_shape is necessary
    password_extracted = bwm1.extract(watermarked_file, wm_shape=len_wm, mode='str')
    print("Extract the password: %s" % password_extracted)
    return password_extracted

def reduce_opacity(image, opacity):
    assert opacity >= 0 and opacity <= 1

    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    else:
        image = image.copy()

    alpha = image.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    image.putalpha(alpha)

    return image

def add_string_watermark(image, wm_str, position=(0, 0), opacity=0.5):
    assert opacity >= 0 and opacity <= 1
    # Set the opacity lower than 0.5 ideally to avoid covering the original photo
    if image.mode != 'RGBA':
        image = image.convert('RGBA')

    # Set the font size based on the height of image 
    h = image.size[1]
    font_size = h // 15

    txt = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt)
    font = ImageFont.truetype("party-confetti.ttf", font_size)
    # Do not use white text (255, 255, 255) because it won't be visible on white background
    draw.text(position, wm_str, (225, 225, 225, 255), font=font)
    
    txt = reduce_opacity(txt, opacity)
    
    # add watermark
    # draw.text((0, 0), "puppy", 
    #         (255, 255, 255), font=font)
    # watermark_image = Image.alpha_composite(image, txt)
    watermark_image = Image.composite(txt, image, txt)
    return watermark_image

def add_watermark(image, mark, opacity=0.5, position="CORNER"):
    if opacity < 1:
        mark = reduce_opacity(mark, opacity)

    if image.mode != 'RGBA':
        image = image.convert('RGBA')

    wm = mark.size[0]  
    hm = mark.size[1]

    w = image.size[0]
    h = image.size[1]

    if position == "CORNER":
        ratio_constant = 3
    else:
        ratio_constant = 1.5

    # The watermark size is set to 1/3 of relatively shorter edge of original photo
    ratio = (w / wm if w / wm < h / hm else h / hm) / ratio_constant

    layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
    mark = mark.resize((int(wm*ratio), int(hm*ratio)))

    if position == "CORNER":
        # Put the watermark at the bottom right corner by default
        layer.paste(mark, (w - int(wm*ratio), h - int(hm*ratio)))
        # layer.paste(mark, (0, 0))
    else:
        layer.paste(mark, (int((w - wm*ratio)/2), int((h - hm*ratio)/2)))

    return Image.composite(layer, image, layer)

def add_double_watermarks(image, img_mark, str_mark, opacity=0.8):
    str_wm_image = add_string_watermark(image, str_mark, opacity=opacity)
    return add_watermark(str_wm_image, img_mark, opacity)