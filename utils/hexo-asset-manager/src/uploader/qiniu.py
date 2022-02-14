import os
from qiniu import Auth, put_file, etag
from dotenv import load_dotenv

# I probably won't use qiniu anymore because the uploading is slow.
# The local government also requires domain registration and identity verification.
def upload_qiniu(self, qiniu_auth, bucket_name, overwrite=False):
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