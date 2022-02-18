import os
import logging
import shutil
import hashlib
from dotenv import load_dotenv
from jianshou import JianshouClient

from src.editor import *
from src.encryption import *
from src.uploader import PcloudUploader

load_dotenv()
QINIU_ACCESS_KEY = os.environ.get('QINIU_ACCESS_KEY')
QINIU_SECRET_KEY = os.environ.get('QINIU_SECRET_KEY')
PCLOUD_EMAIL = os.environ.get('PCLOUD_EMAIL')
PCLOUD_PASSWD = os.environ.get('PCLOUD_PASSWD')

class PostAssetManager():
    def __init__(self, posts_dir):
        self.logger = logging.getLogger(__name__)
        self.posts_dir = posts_dir
        self.post_map = {}
        for root_dir, _, _ in os.walk(self.posts_dir):
            if self.is_asset_folder(root_dir):
                (_, foldername) = os.path.split(root_dir)
                self.post_map[foldername] = foldername

    def has_post(self, post_name):
        return post_name in self.post_map
    
    def posts(self):
        return list(self.post_map.keys())

    def traverse_asset_files(self, folderFilterFn, fileFilterFn, callbackFn):
        for root_dir, _, files in os.walk(self.posts_dir):
            # Exclude the root folder `posts_dir` and nested folders are included
            if folderFilterFn(root_dir):
                for file in files:
                    if fileFilterFn(file):
                        callbackFn(os.path.join(root_dir, file))

    def is_asset_folder(self, root_dir):
        # Not the `_posts` root folder or the subfolders in each post
        return root_dir != self.posts_dir and os.path.dirname(root_dir) == self.posts_dir

    def is_post_asset_subfolder_with_name(self, folder_path, subfolder_name):
        (_, foldername) = os.path.split(folder_path)
        post_folder_path = os.path.dirname(folder_path)
        # Ignore the nested subfolders with the name `encrypted`
        return folder_path != self.posts_dir and os.path.dirname(post_folder_path) == self.posts_dir and foldername == subfolder_name

    def remove_asset_file(self, filepath):
        # self.logger.info("File: %s is removed" % filepath)
        os.remove(filepath)
        return filepath

    def remove_assets(self):
        self.traverse_asset_files(
            self.is_asset_folder, 
            lambda file: True, 
            self.remove_asset_file
        )

    def remove_asset_subfolder(self, subfolder_name):
        for root_dir, _, _ in os.walk(self.posts_dir):
            (_, foldername) = os.path.split(root_dir)
            # It cannot be an asset folder or `_posts` folder but the subfolders in each post folder
            if not self.is_asset_folder(root_dir) and foldername == subfolder_name:
                shutil.rmtree(root_dir)


class AutomatedBlogAssetManager(PostAssetManager):
    def __init__(self, posts_dir, keyid="p1slave"):
        PostAssetManager.__init__(self, posts_dir)
        self.keyid = keyid
        self.overwrite_all = False
        self.uploader = PcloudUploader(PCLOUD_EMAIL, PCLOUD_PASSWD)

    def is_encryption_folder(self, folder_path):
        return self.is_post_asset_subfolder_with_name(folder_path, "encrypted")

    def is_decryption_folder(self, folder_path):
        return self.is_post_asset_subfolder_with_name(folder_path, "decrypted")

    def is_preview_folder(self, folder_path):
        return self.is_post_asset_subfolder_with_name(folder_path, "preview")

    def is_jianshou_folder(self, folder_path):
        return self.is_post_asset_subfolder_with_name(folder_path, "jianshou")

    def remove_encryption_folders(self):
        self.remove_asset_subfolder("encrypted")

    def remove_decryption_folders(self):
        self.remove_asset_subfolder("decrypted")

    def remove_preview_folders(self):
        self.remove_asset_subfolder("preview")

    def remove_watermarked_assets(self):
        self.remove_assets()

    def process_newfile(self, post_name, file_path):
        if not self.has_post(post_name):
            self.logger.error("The name of the post %s does not exist." % post_name)
            return

        if not os.path.isfile(file_path):
            self.logger.error("File does not exist: " + file_path)
            return

        _, filename = os.path.split(file_path) 
        selected_post_dir = os.path.join(self.posts_dir, post_name)

        encryption_dir = os.path.join(selected_post_dir, "encrypted")
        encrypted_file = os.path.join(encryption_dir, filename + ".asc")

        decryption_dir = os.path.join(selected_post_dir, "decrypted")
        decrypted_file = os.path.join(decryption_dir, filename)

        # Copy the new file to the `decrypted` folder if agree to overwrite or does not exist yet.
        if os.path.isfile(decrypted_file):
            overwritten = input("Decrypted file %s already exists. Overwrite? (y/n)" % decrypted_file)
            if not overwritten.startswith("y"):
                self.logger.info("Abort the process because the decrypted file %s already exists." % decrypted_file)
                return

        shutil.copyfile(file_path, decrypted_file)
        self.logger.info("File %s is copied to %s" % (file_path, decrypted_file))

        # Encrypt the file and add it to the `encrypted` folder if agree to overwrite or does not exist yet.
        if os.path.isfile(encrypted_file): 
            overwritten = input("Encrypted file %s already exists. Overwrite? (y/n)" % encrypted_file)
            if not overwritten.startswith("y"):
                self.logger.info("Abort the process because the encrypted file %s already exists." % encrypted_file)
                return

        status = gpg_encrypt_file(file_path, self.keyid, output_dir=encryption_dir)
        self.logger.info("File encrypted as %s with status: %s" % (encrypted_file, status))
 
    def encrypt_post_assets(self, overwrite=False):
        def encrypt_file(original_file_path):
            # The existing encrypted file will be overwritten
            (decrypted_dir, filename) = os.path.split(original_file_path)
            encryption_dir = os.path.abspath(os.path.join(decrypted_dir, os.pardir, "encrypted"))
            encrypted_file = os.path.join(encryption_dir, filename + ".asc")

            if not self.overwrite_all and not overwrite and os.path.isfile(encrypted_file): 
                check = input("Encrypted file %s already exists. Overwrite? (y/n/all)" % encrypted_file)
                if check.startswith("n"):
                    self.logger.info("Abort the process because the encrypted file %s already exists." % encrypted_file)
                    return
                if check.startswith("all"): 
                    self.logger.info("Overwrite all existing encrypted files")
                    self.overwrite_all = True

            self.logger.debug("Encrypting %s" % original_file_path)
            # Set `overwrite` to True because no need to double check.
            status = gpg_encrypt_file(original_file_path, self.keyid, output_dir=encryption_dir, overwrite=True)
            self.logger.info("The status of encryption: %s" % status)

        self.logger.debug("hello world")
        self.traverse_asset_files(
            self.is_decryption_folder,
            lambda file: True,
            encrypt_file
        )

    def decrypt_post_assets(self, overwrite=False):
        passphrase = input("Enter passphrase for GPG private key: ")

        def decrypt_file(encrypted_file_path):
            (encrypted_dir, encrypted_filename) = os.path.split(encrypted_file_path)
            decryption_dir = os.path.abspath(os.path.join(encrypted_dir, os.pardir, "decrypted"))
            # Remove the .asc extension from the encrypted file name
            decrypted_file = os.path.join(decryption_dir, encrypted_filename[:-4])

            if not self.overwrite_all and not overwrite and os.path.isfile(decrypted_file): 
                check = input("Decrypted file %s already exists. Overwrite? (y/n/all)" % decrypted_file)
                if check.startswith("n"):
                    self.logger.info("Abort the process because the encrypted file %s already exists." % decrypted_file)
                    return
                if check.startswith("all"): 
                    self.logger.info("Overwrite all existing encrypted files")
                    self.overwrite_all = True

            # The existing decrypted file will be overwritten
            print("Decrypting %s" % encrypted_file_path)
            # Set `overwrite` to True because no need to double check.
            status = gpg_decrypt_file(encrypted_file_path, passphrase, output_dir=decryption_dir, overwrite=True)
            print("The status of decryption: %s" % status)

        self.traverse_asset_files(
            self.is_encryption_folder,
            lambda file: True,
            decrypt_file
        )

    # If the file is selected for preview then don't watermark it but copy the preview file to asset folder
    def watermark_post_assets(self, logo_file, signature, opacity=0.6, preview_selected={}, overwrite=False):
        if not os.path.isfile(logo_file):
            print("Provide a valid logo file")
            return

        def gen_watermark_image(original_file_path):
            (decrypted_dir, filename) = os.path.split(original_file_path)
            pre, _ = os.path.splitext(filename)
            asset_dir = os.path.dirname(decrypted_dir)
            _, asset_folder_name = os.path.split(asset_dir)

            # Create a separate `jianshou` folder for the watermarked images to be uploaded to jianshou.online
            jianshou_asset_dir = os.path.join(asset_dir, "jianshou")
            if not os.path.isdir(jianshou_asset_dir):
                os.mkdir(jianshou_asset_dir)

            watermarked_png_image = add_double_watermarks(
                Image.open(original_file_path), 
                # Image.open(self.logo_file), 
                make_grayish_img(logo_file),
                signature, 
                opacity
            )

            # Put the watermarked image files in either asset folder or jianshou folder if the photo is selected for preview 
            if asset_folder_name in preview_selected and filename in preview_selected[asset_folder_name]:
                jianshou_asset_file_path = os.path.join(jianshou_asset_dir, pre + ".jpg")
                watermarked_png_image.convert("RGB").save(jianshou_asset_file_path)
            else:
                # The suffix has to be change to .jpg after conversion
                asset_jpg_file_path = os.path.join(asset_dir, pre + ".jpg")
                watermarked_png_image.convert("RGB").save(asset_jpg_file_path)

        self.traverse_asset_files(
            self.is_decryption_folder,
            lambda file: file.endswith(".jpg") or file.endswith(".png"),
            gen_watermark_image
        )

    def create_preview_images(self, paywall_img_path, preview_selected={}, radius=22):
        if not os.path.isfile(paywall_img_path):
            self.logger.error("Paywall image does not exist: " + paywall_img_path)
            return

        # The original file must be in the `decrypted` folder
        def gen_preview_image(original_file_path):
            decrypted_dir, filename = os.path.split(original_file_path) 
            asset_folder_path = os.path.dirname(decrypted_dir)
            _, post_folder_name = os.path.split(asset_folder_path)

            if post_folder_name in preview_selected and filename in preview_selected[post_folder_name]:
                pre, _ = os.path.splitext(filename)
                # preview_dir = os.path.abspath(os.path.join(decrypted_dir, os.pardir, "preview"))
                # Just put in the same asset folder under each post
                preview_dir = os.path.abspath(os.path.join(decrypted_dir, os.pardir))
                if not os.path.isdir(preview_dir):
                    os.mkdir(preview_dir)
                # The preview image will be converted into a JPG file at the end.
                preview_photo_path = os.path.join(preview_dir, pre + "-preview.jpg")

                image = Image.open(original_file_path) 
                blurred_img = image.filter(ImageFilter.GaussianBlur(radius))
                paywall_img = Image.open(paywall_img_path)
                final_image = add_watermark(blurred_img, paywall_img, position="CENTER")
                final_image.convert("RGB").save(preview_photo_path)

                self.logger.info("Preview image %s is generated" % preview_photo_path)

        # Blur the images and add pay-to-view watermarks 
        self.traverse_asset_files(
            self.is_decryption_folder,
            lambda file: file.endswith(".jpg") or file.endswith(".png"),
            gen_preview_image
        )
    
    def upload_pcloud(self, site_path="/", overwrite=True):
        _, public_root_folder_name = self.uploader.find_public_folder()
        sitepath_folderid = self.uploader.create_path(site_path)

        def upload_assets(original_file_path):
            asset_folder_path, filename = os.path.split(original_file_path) 

            # Create the post folder under the site path
            post_asset_foldername = os.path.split(asset_folder_path)[-1]
            res = self.uploader.pcloud.createfolderifnotexists(folderid=sitepath_folderid, name=post_asset_foldername)

            # TODO: The pcloud Python APIs still use the deprecated `path` instead of using `folderid`
            post_folderid = res['metadata']['folderid']
            pcloud_upload_folder_abspath = os.path.join(public_root_folder_name, site_path, post_asset_foldername)

            # Do not have to check the files in the asset folder if we are going to upload and overwrite them.
            if not overwrite:
                post_asset_folder_info = self.uploader.pcloud.listfolder(folderid=post_folderid)
                info_dict = {info['name']: info for info in post_asset_folder_info['metadata']['contents']}

                with open(original_file_path, "rb") as f:
                    bytes = f.read() # read entire file as bytes
                    localfile_md5 = hashlib.md5(bytes).hexdigest()
                    if filename in info_dict:
                        fileid = info_dict[filename]['fileid']
                        pcloud_md5 = self.uploader.pcloud.checksumfile(fileid=fileid)['md5']
                        # Do nothing if the file is already uploaded and the md5 is the same
                        if localfile_md5 == pcloud_md5:
                            self.logger.info("MD5 of %s is the same as the one on pcloud, skip uploading" % filename)
                            return
                        else:
                            self.logger.info("The MD5 of %s is different from the one on pcloud" % filename)

            res = self.uploader.pcloud.uploadfile(files=[original_file_path], path=pcloud_upload_folder_abspath)
            self.logger.info(res)

        self.traverse_asset_files(
            self.is_asset_folder,
            lambda file: file.endswith(".jpg") or file.endswith(".png"),
            upload_assets
        )