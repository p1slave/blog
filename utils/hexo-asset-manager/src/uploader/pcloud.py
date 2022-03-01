
import logging
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

	# Add index.html to every folder so the content of subfolders won't be listed
	def add_empty_index_html(self, folderid=0, folder_path="/"):
		root_info = self.pcloud.listfolder(folderid=folderid)
		public_folder_infos = list(filter(lambda x: 'ispublic' in x and x['isfolder'] == True, root_info['metadata']['contents']))
		# Put an empty index.html to the current folder and recursively add it to all subfolders
		self.pcloud.uploadfile(data=b"", filename="index.html", path=folder_path)
		logging.info("Add index.html to {}".format(folder_path))
		for public_folder_info in public_folder_infos:
			subfolderid = public_folder_info['folderid']
			subfolder_path = os.path.join(folder_path, public_folder_info['name'])
			self.add_empty_index_html(folderid=subfolderid, folder_path=subfolder_path)