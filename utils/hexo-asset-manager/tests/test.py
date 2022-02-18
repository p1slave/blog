from PIL import Image
import pytest
import logging
import os
import shutil
import numpy

from src.manager import AutomatedBlogAssetManager
from src.encryption import gpg_encrypt_file, gpg_decrypt_file

keyid = os.getenv("GPG_KEYID")
passphrase = os.getenv("GPG_PASSPHRASE")

def clean_dir(mock_posts_dir):
    if os.path.isdir(mock_posts_dir):
        shutil.rmtree(mock_posts_dir)

def create_image(file_path, width = 1920, height = 1080):
    width = int(width)
    height = int(height)
    _, filename = os.path.split(file_path)
    _, ext = os.path.splitext(filename)
    rgb_array = numpy.random.rand(height,width,3) * 255
    raw_image = Image.fromarray(rgb_array.astype('uint8'))
    if ext == ".png":
        image = raw_image.convert('RGBA')
        image.save(file_path)
    elif ext == ".jpg":
        image = raw_image.convert('RGB')
        image.save(file_path)
    else:
        logging.error("The given file path is not a valid image file")

# Generate two mock posts and watermark their assets with selected preview images
def mocking_posts_and_watermarking(mock_posts_dir, asset_manager): 
    create_mock_post(mock_posts_dir, "post1", ["new_file.txt", "new_file2.txt", "1.png", "2.jpg"])
    create_mock_post(mock_posts_dir, "post2", ["new_file.txt", "1.png", "2.jpg"])

    repo_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir, os.pardir))
    logo_img_path = os.path.join(repo_dir, "source/images/p1slave-logo.png")
    preview_selected = {
        "post1": ["1.png"],
        "post2": ["2.jpg"]
    }

    # Watermark all pictures in the asset folder except the selected preview images
    asset_manager.watermark_post_assets(
        logo_img_path, 
        signature="p1slave.com", 
        preview_selected=preview_selected
    )

    paywall_img_path = os.path.join(repo_dir, "source/images/watermarks/paywall.jpg")
    asset_manager.create_preview_images(paywall_img_path, preview_selected)

def create_mock_post(mock_posts_dir, post_name, files=[]):
    testing_post_folder = os.path.join(mock_posts_dir, post_name)
    if not os.path.isdir(testing_post_folder):
        os.mkdir(testing_post_folder)

    # Create a fake markdown file for the post
    testing_post_markdown = os.path.join(testing_post_folder, post_name + ".md")
    with open(testing_post_markdown, "w") as f:
        f.write("A testing post\n")
        f.close()

    testing_encrypted_folder = os.path.join(testing_post_folder, "encrypted")
    testing_decrypted_folder = os.path.join(testing_post_folder, "decrypted")

    if not os.path.isdir(testing_decrypted_folder):
        os.mkdir(testing_decrypted_folder)

    if not os.path.isdir(testing_encrypted_folder):
        os.mkdir(testing_encrypted_folder)

    for file in files:
        testing_new_file = os.path.join(testing_decrypted_folder, file)
        _, ext = os.path.splitext(file)
        if ext == ".txt":
            with open(testing_new_file, "w") as f:
                f.write("Hello World")
                f.close()
        elif ext == ".png" or ext == ".jpg":
            create_image(testing_new_file)

@pytest.fixture
def mock_posts_dir():
    mock_posts_dir = os.path.join(os.getcwd(), "mock_posts")
    clean_dir(mock_posts_dir)
    os.mkdir(mock_posts_dir)
    return mock_posts_dir

@pytest.fixture
def asset_manager(mock_posts_dir):
    asset_manager = AutomatedBlogAssetManager(mock_posts_dir, keyid=keyid)
    return asset_manager

def test_gpg_encrypt_and_decrypt(mock_posts_dir):
    testing_post_name = "a_testing_post"
    testing_post_folder = os.path.join(mock_posts_dir, testing_post_name)

    # Clean up the folder and create a mock post
    clean_dir(testing_post_folder)
    create_mock_post(mock_posts_dir, testing_post_name, ["new_file.txt", "1.png", "2.jpg"])

    testing_encrypted_folder = os.path.join(mock_posts_dir, testing_post_name, "encrypted")
    testing_encrypted_file = os.path.join(mock_posts_dir, testing_post_name, "encrypted", "new_file.txt.asc")
    testing_decrypted_folder = os.path.join(mock_posts_dir, testing_post_name, "decrypted")
    testing_decrypted_file = os.path.join(mock_posts_dir, testing_post_name, "decrypted", "new_file.txt")

    gpg_encrypt_file(testing_decrypted_file, keyid, output_dir=testing_encrypted_folder, overwrite=True)
    assert os.path.isfile(testing_encrypted_file)

    # Remove the original file and decrypt the encrypted file to check the content
    os.remove(testing_decrypted_file)
    gpg_decrypt_file(testing_encrypted_file, passphrase, output_dir=testing_decrypted_folder)
    with open(testing_decrypted_file, "r") as f:
        assert f.read() == "Hello World"

def test_asset_manager_gpg(mock_posts_dir, asset_manager):
    create_mock_post(mock_posts_dir, "post1", ["new_file.txt", "new_file2.txt", "1.png", "2.jpg"])
    create_mock_post(mock_posts_dir, "post2", ["new_file.txt", "1.png", "2.jpg"])
    asset_manager.encrypt_post_assets(overwrite=True)
    asset_manager.decrypt_post_assets(overwrite=True)

    # Remove the whole folder and its files
    asset_manager.remove_decryption_folders()
    asset_manager.remove_encryption_folders()

    posts = asset_manager.posts()
    for post_name in posts:
        post_folder = os.path.join(mock_posts_dir, post_name)
        post_decrypted_folder = os.path.join(post_folder, "decrypted")
        post_encrypted_folder = os.path.join(post_folder, "encrypted")
        assert not os.path.isdir(post_decrypted_folder)
        assert not os.path.isdir(post_encrypted_folder)

def test_watermarking(mock_posts_dir, asset_manager):
    mocking_posts_and_watermarking(mock_posts_dir, asset_manager)
    # Check if those files exist
    preview1_path = os.path.join(mock_posts_dir, "post1", "1-preview.jpg")
    preview2_path = os.path.join(mock_posts_dir, "post2", "2-preview.jpg")
    jianshou1_path = os.path.join(mock_posts_dir, "post1", "jianshou", "1.jpg")
    jianshou2_path = os.path.join(mock_posts_dir, "post2", "jianshou", "2.jpg")
    assert os.path.isfile(preview1_path)
    assert os.path.isfile(preview2_path)
    assert os.path.isfile(jianshou1_path)
    assert os.path.isfile(jianshou2_path)

def test_pcloud(mock_posts_dir, asset_manager):
    mocking_posts_and_watermarking(mock_posts_dir, asset_manager)
    # Upload all files in the asset folder to pcloud
    asset_manager.upload_pcloud(site_path="websites/p1slave")