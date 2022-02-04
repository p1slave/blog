import os
import gnupg
from pprint import pprint
from blind_watermark import WaterMark

from PIL import Image, ImageEnhance, ImageDraw, ImageFont

def convert2png(image_path, output_path):
    image = Image.open(image_path)
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    else:
        image = image.copy()

    image.save(output_path, "PNG")

# Convert to RGBA mode first to include the transparency and then invert 
# RGB channel but leave the transparency unchanged
def invert_transparent_img(image_path, output_path):
    img = Image.open(image_path)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    r, g, b, a = img.split()

    def invert(image):
        return image.point(lambda p: 255 - p)

    r, g, b = map(invert, (r, g, b))

    img2 = Image.merge(img.mode, (r, g, b, a))

    img2.save(output_path, "PNG")

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

def add_string_watermark(image, wm_str, opacity=0.8):
    assert opacity >= 0 and opacity <= 1
    if not image.mode is 'RGBA':
        image = image.convert('RGBA')

    # Set the font size based on the height of image 
    h = image.size[1]
    font_size = h // 15

    txt = Image.new('RGBA', image.size, (0,0,0,0))
    draw = ImageDraw.Draw(txt)
    font = ImageFont.truetype("party-confetti.ttf", font_size)
    draw.text((0, 0), wm_str, (255, 255, 255, 255), font=font)
    
    txt = reduce_opacity(txt, opacity)
    
    # add watermark
    # draw.text((0, 0), "puppy", 
    #         (255, 255, 255), font=font)
    # watermark_image = Image.alpha_composite(image, txt)
    watermark_image = Image.composite(txt, image, txt)
    return watermark_image

def add_watermark(image, mark, opacity=0.8):
    if opacity < 1:
        mark = reduce_opacity(mark, opacity)

    if not image.mode is 'RGBA':
        image = image.convert('RGBA')

    wm = mark.size[0]  
    hm = mark.size[1]

    w = image.size[0]
    h = image.size[1]

    # The watermark size is set to 1/3 of relatively shorter edge of original photo
    ratio = (w / wm if w / wm < h / hm else h / hm) / 3

    layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
    mark = mark.resize((int(wm*ratio), int(hm*ratio)))

    # Put the watermark at the bottom right corner by default
    layer.paste(mark, (w - int(wm*ratio), h - int(hm*ratio)))
    # layer.paste(mark, (0, 0))

    return Image.composite(layer, image, layer)

def add_double_watermarks(image, img_mark, str_mark, opacity=0.8):
    str_wm_image = add_string_watermark(image, str_mark, opacity)
    return add_watermark(str_wm_image, img_mark, opacity)

# Use the public key (keyid) of the recipient to encrypt the file
def gpg_encrypt_file(file_path, keyid, output_dir=None):
    gpg = gnupg.GPG()
    pprint(gpg.list_keys())
    stream = open(file_path, "rb")
    crypt = gpg.encrypt_file(stream, keyid)
    
    # Return the error code if the encryption fails
    if not crypt.ok:
        return crypt.status + ": " + keyid

    dirname, filename = os.path.split(file_path) 

    if output_dir is None:
        # Create a new folder to hold all encrypted files if output folder is not specified
        output_path = os.path.join(dirname, "encrypted", filename + ".asc")
        encrypted_dir = os.path.join(dirname, "encrypted")
        if not os.path.isdir(encrypted_dir):
            os.mkdir(encrypted_dir)
    else:
        # Create the output folder if it does not exist
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
        output_path = os.path.join(output_dir, filename + ".asc")

    if os.path.isfile(output_path):
        os.remove(output_path)

    f = open(output_path, "wb")
    f.write(crypt.data)
    f.close()

    return crypt.status

# The passphrase will be cached after the first successful decryption
def gpg_decrypt_file(encrypted_file_path, passphrase, output_dir=None):
    gpg = gnupg.GPG()
    stream = open(encrypted_file_path, "rb")
    crypt = gpg.decrypt_file(stream, passphrase=passphrase)

    if not crypt.ok:
        return crypt.status

    dirname, filename = os.path.split(encrypted_file_path) 
    ending = filename.split(".")[-1]

    # Only continue the decryption with .asc or .gpg file 
    if not ending == "asc" and not ending == "gpg":
        return "wrong file format"

    # Remove suffix .asc or .gpg to get the original file name
    original_filename = ".".join(filename.split(".")[:-1])

    if output_dir is None:
        # Create a separate folder to hold decrypted files
        output_dir = os.path.join(dirname, "decrypted")

    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    output_path = os.path.join(output_dir, original_filename)

    if os.path.isfile(output_path):
        os.remove(output_path)

    f = open(output_path, "wb")
    f.write(crypt.data)
    f.close()

    return crypt.status


current_dir = os.getcwd()
repo_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir, os.pardir))
print(repo_dir)

logo_file = os.path.join(repo_dir, "source/images/p1slave-logo.png")
wechat_file = os.path.join(repo_dir, "source/images/wechat.jpg")
nowechat_file = os.path.join(repo_dir, "source/images/nowechat.jpg")


# Change the grayscale photo to binary mode photo to minimize the size
# Image.open(blind_wm_grayscale_file).convert('1').save(blind_wm_bin_file, "PNG")

print(gpg_encrypt_file("hello.txt", "p1slave"))
print(gpg_decrypt_file("encrypted/hello.txt.asc", "", output_dir="decrypted"))

image = Image.open(nowechat_file)
mark = Image.open(logo_file)
# add_string_watermark(image, "p1slave.com", opacity=0.5).save("watermarked.png", "PNG")
# wm_image = add_string_watermark(image, "p1slave.com", opacity=0.5)
add_double_watermarks(image, mark, "p1slave.com", opacity=0.8).save("watermarked.png", "PNG")
