import json
import os
from dotenv import load_dotenv
from src.manager import AutomatedBlogAssetManager
from src.uploader import PcloudUploader

load_dotenv()
PCLOUD_EMAIL = os.environ.get('PCLOUD_EMAIL')
PCLOUD_PASSWD = os.environ.get('PCLOUD_PASSWD')
GPG_PASSPHRASE = os.environ.get('GPG_PASSPHRASE')

repo_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir, os.pardir))
posts_dir = os.path.join(repo_dir, "source/_posts")

keyid = "p1slave"
paywall_img_path = os.path.join(repo_dir, "source/images/watermarks/paywall.jpg")
logo_img_path = os.path.join(repo_dir, "source/images/p1slave-logo.png")
manager = AutomatedBlogAssetManager(posts_dir, keyid=keyid)

# uploader = PcloudUploader(PCLOUD_EMAIL, PCLOUD_PASSWD)
# uploader.add_empty_index_html()

# The only source of truth lies in the folder of encrypted files
# Do the encryption for the new added files but don't overwrite the existing encrypted files
# manager.encrypt_post_assets()

# manager.generate_assets(logo_img_path, paywall_img_path, 
# 	opacity=0.5, 
# 	signature="p1slave.com", 
# 	preview_selected=preview_selected
# )

# Upload all files in the asset folder to pcloud
# manager.upload_pcloud(site_path="websites/p1slave")

# f = open("preview.json")
# preview_selected = json.load(f)
# manager.upload_jianshou(preview_selected=preview_selected)

