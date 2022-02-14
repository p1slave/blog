import pytest

def test_gpg_encrypt_and_decrypt():
	pass
	# print(gpg_encrypt_file("hello.txt", "p1slave"))
	# print(gpg_decrypt_file("encrypted/hello.txt.asc", "", output_dir="decrypted"))

	# manager.decrypt_post_assets()
	# manager.encrypt_post_assets()

def test_watermarking():
	pass
	# add_string_watermark(image, "p1slave.com", opacity=0.5).save("watermarked.png", "PNG")
	# wm_image = add_string_watermark(image, "p1slave.com", opacity=0.5)
	# add_double_watermarks(image, mark, "p1slave.com", opacity=0.8).save("watermarked.png", "PNG")

	# logo_file = os.path.join(repo_dir, "source/images/p1slave-logo.png")
	# signature = "p1slave"
	# manager.watermark_post_assets(logo_file, signature)

	# manager.remove_watermarked_assets(logo_file, signature)

def test_qiniu():
	pass
	# qiniu_auth = Auth(QINIU_ACCESS_KEY, QINIU_SECRET_KEY)
	# bucket_name = 'p1slave'
	# manager.upload_qiniu(qiniu_auth, bucket_name)


def test_pcloud():
	pass
	# pcloud = PyCloud(PCLOUD_EMAIL, PCLOUD_PASSWD, endpoint="nearest")
	# root_info = pcloud.listfolder(folderid=0)
	# public_folder_info = list(filter(lambda x: 'ispublic' in x, root_info['metadata']['contents']))[0]
	# public_folderid = public_folder_info['folderid']
	# public_foldername = public_folder_info['path']
	# print(public_folderid, public_foldername)

	# public_info = pcloud.listfolder(folderid=public_folderid)
	# pprint(public_info)
	# res = pcloud.createfolderifnotexists(folderid=public_folderid, name='websites')
	# websites_folderid = res['metadata']['folderid']
	# res = pcloud.createfolderifnotexists(folderid=websites_folderid, name='p1slave')
	# p1slave_folderid = res['metadata']['folderid']
	# pprint(p1slave_folderid)

	# res = pcloud.uploadfile(files=[logo_file], path="/public/websites/p1slave")
	# print(res)