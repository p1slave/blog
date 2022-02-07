import os
import shutil
import gnupg
from pprint import pprint
from blind_watermark import WaterMark
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
from qiniu import Auth, put_file, etag
from dotenv import load_dotenv
from pcloud import PyCloud

load_dotenv()
QINIU_ACCESS_KEY = os.environ.get('QINIU_ACCESS_KEY')
QINIU_SECRET_KEY = os.environ.get('QINIU_SECRET_KEY')
PCLOUD_EMAIL = os.environ.get('PCLOUD_EMAIL')
PCLOUD_PASSWD = os.environ.get('PCLOUD_PASSWD')


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

def add_string_watermark(image, wm_str, opacity=0.5):
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
    draw.text((0, 0), wm_str, (225, 225, 225, 255), font=font)
    
    txt = reduce_opacity(txt, opacity)
    
    # add watermark
    # draw.text((0, 0), "puppy", 
    #         (255, 255, 255), font=font)
    # watermark_image = Image.alpha_composite(image, txt)
    watermark_image = Image.composite(txt, image, txt)
    return watermark_image

def add_watermark(image, mark, opacity=0.5):
    if opacity < 1:
        mark = reduce_opacity(mark, opacity)

    if image.mode != 'RGBA':
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
    # pprint(gpg.list_keys())
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


# print(gpg_encrypt_file("hello.txt", "p1slave"))
# print(gpg_decrypt_file("encrypted/hello.txt.asc", "", output_dir="decrypted"))

# add_string_watermark(image, "p1slave.com", opacity=0.5).save("watermarked.png", "PNG")
# wm_image = add_string_watermark(image, "p1slave.com", opacity=0.5)
# add_double_watermarks(image, mark, "p1slave.com", opacity=0.8).save("watermarked.png", "PNG")


class BlogAssetManager():
    def __init__(self, posts_dir, keyid="p1slave"):
        self.posts_dir = posts_dir
        self.keyid = keyid

    def add_file(self, post_name, file_path):
        if not os.path.isfile(file_path):
            print("File does not exist: " + file_path)
            return

        _, filename = os.path.split(file_path) 
        selected_post_dir = os.path.join(self.posts_dir, post_name)

        encryption_dir = os.path.join(selected_post_dir, "encrypted")
        encrypted_file = os.path.join(encryption_dir, filename + ".asc")

        decryption_dir = os.path.join(selected_post_dir, "decrypted")
        decrypted_file = os.path.join(decryption_dir, filename)

        if os.path.isfile(decrypted_file):
            overwritten = input("Decrypted file %s already exists. Overwrite? (y/n)" % decrypted_file)
            if not overwritten.startswith("y"):
                print("Abort")
                return

        # Copy the new file to the decryption folder
        shutil.copyfile(file_path, decrypted_file)
        print("Copied %s to %s" % (file_path, decrypted_file))

        if os.path.isfile(encrypted_file): 
            overwritten = input("Encrypted file %s already exists. Overwrite? (y/n)" % encrypted_file)
            if not overwritten.startswith("y"):
                print("Abort")
                return

        # Encrypt the file and add it to the encryption folder
        status = gpg_encrypt_file(file_path, keyid, output_dir=encryption_dir)
        print("Encrypting file as %s: %s" % (encrypted_file, status))

    def remove_encryption_folders(self):
        for root_dir, _, _ in os.walk(self.posts_dir):
            # Remove all folders containing encrypted files
            if root_dir.endswith("encrypted"):
                shutil.rmtree(root_dir)

    def remove_decryption_folders(self):
        for root_dir, _, _ in os.walk(self.posts_dir):
            # Remove all folders containing decrypted files
            if root_dir.endswith("decrypted"):
                shutil.rmtree(root_dir)

    def remove_watermarked_assets(self):
        for root_dir, dirs, files in os.walk(self.posts_dir):
            # Find the asset folder for each post
            if root_dir != self.posts_dir and os.path.dirname(root_dir) == self.posts_dir:
                for file in files:
                    os.remove(os.path.join(root_dir, file))

    def encrypt_post_assets(self):
        for root_dir, dirs, files in os.walk(self.posts_dir):
            # Only encrypt files in the the decrypted folder and add new files to this folder
            if root_dir != self.posts_dir and root_dir.endswith("decrypted"):
                print("The direcotry %s has folders: %s and files: %s" % (root_dir, dirs, files))
                encryption_dir = os.path.abspath(os.path.join(root_dir, os.pardir, "encrypted"))
                for file in files:
                    file_path = os.path.join(root_dir, file)
                    # The existing encrypted file will be overwritten
                    status = gpg_encrypt_file(file_path, keyid, output_dir=encryption_dir)
                    print("Encrypting %s: %s" % (file_path, status))

    def decrypt_post_assets(self):
        passphrase = input("Enter passphrase for GPG private key: ")
        for root_dir, _, files in os.walk(self.posts_dir):
            if root_dir.endswith("encrypted"):
                print("Found encryption folder: %s" % root_dir)
                # Create a decryption folder in the parent directory of encryption folder
                decryption_dir = os.path.abspath(os.path.join(root_dir, os.pardir, "decrypted"))
                for encrypted_file in files:
                    encrypted_file_path = os.path.join(root_dir, encrypted_file)
                    # The existing decrypted file will be overwritten
                    status = gpg_decrypt_file(encrypted_file_path, passphrase, output_dir=decryption_dir)
                    print("Decrypting %s: %s" % (encrypted_file_path, status))
                
    def watermark_post_assets(self, logo_file, signature, opacity=0.6):
        if not os.path.isfile(logo_file):
            print("Provide a valid logo file")
            return

        for root_dir, dirs, files in os.walk(self.posts_dir):
            # Only encrypt files in the the decrypted folder and add new files to this folder
            if root_dir != self.posts_dir and root_dir.endswith("decrypted"):
                print("The direcotry %s has folders: %s and files: %s" % (root_dir, dirs, files))
                # Asset folder is the parent directory of decrypted folder to hold watermarked files
                asset_dir = os.path.abspath(os.path.join(root_dir, os.pardir))
                for file in files:
                    decrypted_file_path = os.path.join(root_dir, file)
                    pre, _ = os.path.splitext(file)
                    # Convert to JPEG format to reduce the size
                    asset_file_path = os.path.join(asset_dir, pre + ".jpg")
                    if file.split('.')[-1] in ["jpg", "jpeg", "png"]:
                        png_image = add_double_watermarks(
                            Image.open(decrypted_file_path), 
                            # Image.open(self.logo_file), 
                            make_grayish_img(logo_file),
                            signature, 
                            opacity
                        )
                        png_image.convert("RGB").save(asset_file_path)

    def upload_qiniu(self, qiniu_auth, bucket_name):
        for root_dir, dirs, files in os.walk(self.posts_dir):
            # Only choose the asset folder under `_posts` folder and ignore the nested folders
            if root_dir != self.posts_dir and os.path.dirname(root_dir) == self.posts_dir:
                print("The direcotry %s has folders: %s and files: %s" % (root_dir, dirs, files))
                for file in files:
                    upload_file_path = os.path.join(root_dir, file)
                    key = os.path.basename(root_dir) + "/" + file
                    token = qiniu_auth.upload_token(bucket_name, key, 3600)
                    ret, info = put_file(token, key, upload_file_path, version='v2') 
                    print(info)
                    assert ret['key'] == key
                    assert ret['hash'] == etag(upload_file_path)

    def upload_pcloud(self, site_path="/"):
        pcloud = PyCloud(PCLOUD_EMAIL, PCLOUD_PASSWD, endpoint="nearest")
        root_info = pcloud.listfolder(folderid=0)
        public_folder_info = list(filter(lambda x: 'ispublic' in x, root_info['metadata']['contents']))[0]
        public_folderid = public_folder_info['folderid']
        public_root_folder_name = public_folder_info['path'] # e.g. "/public"
        
        # e.g. "/mysites/p1slave/blog" without the root folder name
        subfolders = site_path.split('/')         
        folderid = public_folderid
        # Create the subfolders under pcloud public folder
        for subfolder_name in subfolders:
            res = pcloud.createfolderifnotexists(folderid=folderid, name=subfolder_name)
            folderid = res['metadata']['folderid']

        for root_dir, dirs, files in os.walk(self.posts_dir):
            # Only choose the asset folder under `_posts` folder and ignore the nested folders
            if root_dir != self.posts_dir and os.path.dirname(root_dir) == self.posts_dir:
                # Create post folder under site path if it does not exists
                post_asset_foldername = os.path.split(root_dir)[-1]
                res = pcloud.createfolderifnotexists(folderid=folderid, name=post_asset_foldername)

                # TODO: The pcloud Python APIs still use the deprecated `path` instead of using `folderid`
                # post_folderid = res['metadata']['folderid']
                post_folder_abspath = os.path.join(public_root_folder_name, site_path, post_asset_foldername)

                print("The direcotry %s has folders: %s and files: %s" % (root_dir, dirs, files))
                for file in files:
                    upload_file_path = os.path.join(root_dir, file)
                    res = pcloud.uploadfile(files=[upload_file_path], path=post_folder_abspath)
                    print(res)


current_dir = os.getcwd()
repo_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir, os.pardir))
posts_dir = os.path.join(repo_dir, "source/_posts")

keyid = "p1slave"
manager = BlogAssetManager(posts_dir, keyid=keyid)
manager.upload_pcloud(site_path="websites/p1slave")


