import os
import logging
import shutil
from dotenv import load_dotenv
from jianshou import JianshouClient

from src.editor import *
from src.encryption import *

load_dotenv()
QINIU_ACCESS_KEY = os.environ.get('QINIU_ACCESS_KEY')
QINIU_SECRET_KEY = os.environ.get('QINIU_SECRET_KEY')
PCLOUD_EMAIL = os.environ.get('PCLOUD_EMAIL')
PCLOUD_PASSWD = os.environ.get('PCLOUD_PASSWD')

class PostAssetManager():
    def __init__(self, posts_dir):
        self.posts_dir = posts_dir
        self.post_map = {}
        for root_dir, _, _ in os.walk(self.posts_dir):
            if self.is_asset_folder(root_dir):
                (_, foldername) = os.path.split(root_dir)
                self.post_map[foldername] = foldername

    def has_post(self, post_name):
        return post_name in self.post_map

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
        # logging.info("File: %s is removed" % filepath)
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
            logging.error("The name of the post %s does not exist." % post_name)
            return

        if not os.path.isfile(file_path):
            logging.error("File does not exist: " + file_path)
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
                logging.info("Abort the process because the decrypted file %s already exists." % decrypted_file)
                return

        shutil.copyfile(file_path, decrypted_file)
        logging.info("File %s is copied to %s" % (file_path, decrypted_file))

        # Encrypt the file and add it to the `encrypted` folder if agree to overwrite or does not exist yet.
        if os.path.isfile(encrypted_file): 
            overwritten = input("Encrypted file %s already exists. Overwrite? (y/n)" % encrypted_file)
            if not overwritten.startswith("y"):
                logging.info("Abort the process because the encrypted file %s already exists." % encrypted_file)
                return

        status = gpg_encrypt_file(file_path, keyid, output_dir=encryption_dir)
        logging.info("File encrypted as %s with status: %s" % (encrypted_file, status))
 
    def create_preview_images(self, paywall_img_path, radius=22):
        if not os.path.isfile(paywall_img_path):
            print("Paywall image does not exist: " + paywall_img_path)
            return

        # `original_file_path` must be a file in the `decrypted` folder
        def gen_preview_image(original_file_path):
            (decrypted_dir, _) = os.path.split(original_file_path)
            preview_dir = os.path.abspath(os.path.join(decrypted_dir, os.pardir, "preview"))
            blurred_image_path = gen_preview_image(original_file_path, paywall_img_path, preview_dir, radius)
            logging.info("Preview image %s is generated" % blurred_image_path)

        # Blur the images and add pay-to-view watermarks 
        self.traverse_asset_files(
            self.is_decryption_folder,
            lambda file: file.endswith(".jpg") or file.endswith(".png"),
            gen_preview_image
        )

    def encrypt_post_assets(self, overwrite=False):
        def encrypt_file(original_file_path):
            # The existing encrypted file will be overwritten
            (decrypted_dir, filename) = os.path.split(original_file_path)
            encryption_dir = os.path.abspath(os.path.join(decrypted_dir, os.pardir, "encrypted"))
            encrypted_file = os.path.join(encryption_dir, filename + ".asc")

            if os.path.isfile(encrypted_file): 
                overwritten = input("Encrypted file %s already exists. Overwrite? (y/n)" % encrypted_file)
                if not overwritten.startswith("y"):
                    logging.info("Abort the process because the encrypted file %s already exists." % encrypted_file)
                    return

            logging.info("Encrypting %s" % original_file_path)
            status = gpg_encrypt_file(original_file_path, keyid, output_dir=encryption_dir, overwrite=overwrite)
            logging.info("The status of encryption: %s" % status)

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

            if os.path.isfile(decrypted_file): 
                overwritten = input("Decrypted file %s already exists. Overwrite? (y/n)" % decrypted_file)
                if not overwritten.startswith("y"):
                    logging.info("Abort the process because the decrypted file %s already exists." % decrypted_file)
                    return

            # The existing decrypted file will be overwritten
            print("Decrypting %s" % encrypted_file_path)
            status = gpg_decrypt_file(encrypted_file_path, passphrase, output_dir=decryption_dir, overwrite=overwrite)
            print("The status of decryption: %s" % status)

        self.traverse_asset_files(
            self.is_encryption_folder,
            lambda file: True,
            decrypt_file
        )

    # If the file is selected for preview then don't watermark it but copy the preview file to asset folder
    def watermark_post_assets(self, logo_file, signature, opacity=0.6, preview_selected={}, radius=22, overwrite=False):
        if not os.path.isfile(logo_file):
            print("Provide a valid logo file")
            return

        for root_dir, dirs, files in os.walk(self.posts_dir):
            # Only encrypt files in the the decrypted folder and add new files to this folder
            if root_dir != self.posts_dir and root_dir.endswith("decrypted"):
                print("The direcotry %s has folders: %s and files: %s" % (root_dir, dirs, files))
                # Asset folder is the parent directory of decrypted folder to hold watermarked files
                asset_dir = os.path.dirname(root_dir)
                _, asset_folder_name = os.path.split(asset_dir)

                preview_files = []
                if asset_folder_name in preview_selected:
                    preview_files = preview_selected[asset_folder_name]

                for file in files:
                    if file.split('.')[-1] in ["jpg", "jpeg", "png"]:
                        decrypted_file_path = os.path.join(root_dir, file)
                        watermarked_png_image = add_double_watermarks(
                            Image.open(decrypted_file_path), 
                            # Image.open(self.logo_file), 
                            make_grayish_img(logo_file),
                            signature, 
                            opacity
                        )

                        pre, _ = os.path.splitext(file)

                        if file in preview_files:
                            # Add a preview file to the asset folder and don't watermark it because it is already blurred
                            gen_preview_image(decrypted_file_path, paywall_img_path, asset_dir, radius)
                            # Create a separate folder for the watermarked images to uploaded to jianshou.online
                            jianshou_asset_dir = os.path.join(asset_dir, "jianshou")
                            if not os.path.isdir(jianshou_asset_dir):
                                os.mkdir(jianshou_asset_dir)
                            jianshou_asset_file_path = os.path.join(jianshou_asset_dir, pre + ".jpg")
                            
                            if not os.path.isfile(jianshou_asset_file_path) or overwrite:
                                if os.path.isfile(jianshou_asset_file_path) and overwrite:
                                    check = input("Are you sure you want to overwrite the existing jianshou file? (y/n)")
                                    if not check.lower().startswith('y'):
                                        continue
                                    else:
                                        os.remove(jianshou_asset_file_path)

                                watermarked_png_image.convert("RGB").save(jianshou_asset_file_path)
                        else:
                            # Convert to JPEG format to reduce the size
                            asset_file_path = os.path.join(asset_dir, pre + ".jpg")
                            if not os.path.isfile(asset_file_path) or overwrite:
                                if os.path.isfile(asset_file_path) and overwrite:
                                    check = input("Are you sure you want to overwrite the existing asset file? (y/n)")
                                    if not check.lower().startswith('y'):
                                        continue
                                    else:
                                        os.remove(asset_file_path)

                                watermarked_png_image.convert("RGB").save(asset_file_path)


current_dir = os.getcwd()
repo_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir, os.pardir))
posts_dir = os.path.join(repo_dir, "source/_posts")

keyid = "p1slave"
paywall_img_path = os.path.join(repo_dir, "source/images/watermarks/paywall.jpg")
logo_img_path = os.path.join(repo_dir, "source/images/p1slave-logo.png")
manager = AutomatedBlogAssetManager(posts_dir, keyid=keyid)

# The only source of truth lies in the folder of encrypted files
# Do the encryption for the new added files but don't overwrite the existing encrypted files
manager.encrypt_post_assets()
# manager.decrypt_post_assets()

manager.remove_asset_folders()
# manager.remove_preview_folders()

# manager.remove_decryption_folders()
# Don't generate preview for all images
# manager.create_preview_images(paywall_img_path, radius=22)

# manager.decrypt_post_assets()

preview_selected = {
    "pig-smells-like-a-dead-person-lol": ["3.png"],
    "my-thoughts-on-eileen-gu-and-her-family": ["5.png"]
}

# Watermark all pictures in the asset folder except the selected preview images
manager.watermark_post_assets(
    logo_img_path, 
    signature="p1slave.com", 
    opacity=0.5, 
    preview_selected=preview_selected
)

# Upload all files in the asset folder to pcloud
manager.upload_pcloud(site_path="websites/p1slave")
