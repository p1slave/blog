
import os
import hashlib
from pcloud import PyCloud

class PcloudUploader():
	def __init__(self, email, passwd, site_path="/", overwrite=True) -> None:
		self.pcloud = PyCloud(email, passwd, endpoint="nearest")

	def find_public_folder(self):
		root_info = self.pcloud.listfolder(folderid=0)
		public_folder_info = list(filter(lambda x: 'ispublic' in x, root_info['metadata']['contents']))[0]
		public_folderid = public_folder_info['folderid']
		public_root_folder_name = public_folder_info['path'] # e.g. "/public"

		return public_folderid, public_root_folder_name

	def create_path(self, init_folderid, dir_path="/"):
		# e.g. "/mysites/p1slave/blog" without the root folder name
		subfolders = dir_path.split('/')         
		folderid = init_folderid
		# Create the subfolders under pcloud public folder
		for subfolder_name in subfolders:
			# In case the user put slash at the end or the beginning of the path
			if subfolder_name != "":
				res = self.pcloud.createfolderifnotexists(folderid=folderid, name=subfolder_name)
				folderid = res['metadata']['folderid']

		return folderid

	# By default, do not create path and return the folder id of the root of public folder
	def create_path_from_public_folder(self, site_path="/"):
		public_folderid, _ = self.find_public_folder()
		folderid = self.create_path(public_folderid, site_path)
		return folderid