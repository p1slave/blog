
import os
import hashlib
from pcloud import PyCloud

# Checking the MD5 hash of each file is slow so overwrite all files by default
def upload_pcloud(self, email, passwd, site_path="/", overwrite=True):
	pcloud = PyCloud(email, passwd, endpoint="nearest")
	# pcloud = PyCloud(PCLOUD_EMAIL, PCLOUD_PASSWD, endpoint="nearest")

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
			post_folderid = res['metadata']['folderid']
			post_folder_abspath = os.path.join(public_root_folder_name, site_path, post_asset_foldername)

			# Do not have to check the files in the asset folder if we are going to upload and overwrite them.
			if not overwrite:
				post_asset_folder_info = pcloud.listfolder(folderid=post_folderid)
				info_dict = {info['name']: info for info in post_asset_folder_info['metadata']['contents']}
			else:
				info_dict = {}

			print("The direcotry %s has folders: %s and files: %s" % (root_dir, dirs, files))
			for file in files:
				upload_file_path = os.path.join(root_dir, file)

				if not overwrite:
					with open(upload_file_path,"rb") as f:
						bytes = f.read() # read entire file as bytes
						localfile_md5 = hashlib.md5(bytes).hexdigest()
						if file in info_dict:
							fileid = info_dict[file]['fileid']
							pcloud_md5 = pcloud.checksumfile(fileid=fileid)['md5']
							# Do nothing if the file is already uploaded and the md5 is the same
							if localfile_md5 == pcloud_md5:
								print("MD5 of %s is the same as the one on pcloud, skip uploading" % file)
								continue

				res = pcloud.uploadfile(files=[upload_file_path], path=post_folder_abspath)
				print(res)
