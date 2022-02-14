
import os
import gnupg
import logging
from pprint import pprint

# Use the public key (keyid) of the recipient to encrypt the file
def gpg_encrypt_file(file_path, keyid, output_dir=None, overwrite=False):
    gpg = gnupg.GPG()
    # pprint(gpg.list_keys())
    stream = open(file_path, "rb")
    crypt = gpg.encrypt_file(stream, keyid)
    
    # Return the error code if the encryption fails
    if not crypt.ok:
        message = crypt.status + ": " + keyid
        logging.error(message)
        return None

    dirname, filename = os.path.split(file_path) 

    if output_dir is None:
        # Create a new folder to hold all encrypted files if output folder is not specified
        output_file_path = os.path.join(dirname, "encrypted", filename + ".asc")
        encrypted_dir = os.path.join(dirname, "encrypted")
        if not os.path.isdir(encrypted_dir):
            os.mkdir(encrypted_dir)
    else:
        # Create the output folder if it does not exist
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
        output_file_path = os.path.join(output_dir, filename + ".asc")

    # File does not exist or needs to be overwritten
    if not os.path.isfile(output_file_path) or overwrite:
        if os.path.isfile(output_file_path) and overwrite:
            check = input("Are you sure you want to overwrite the existing encrypted file? (y/n)")
            if not check.lower().startswith('y'):
                message = format("Choose not to overwrite the existing encrypted file")
                logging.info(message)
                return None
            else:
                os.remove(output_file_path)

        f = open(output_file_path, "wb")
        f.write(crypt.data)
        f.close()
        logging.info(crypt.status)
        return output_file_path

    message = format("File %s already exists and will not be overwritten" % output_file_path)
    logging.info(message)
    return None


# The passphrase will be cached after the first successful decryption
def gpg_decrypt_file(encrypted_file_path, passphrase, output_dir=None, overwrite=False):
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

    output_file_path = os.path.join(output_dir, original_filename)

    if not os.path.isfile(output_file_path) or overwrite:
        if os.path.isfile(output_file_path) and overwrite:
            check = input("Are you sure you want to overwrite the existing decrypted file? (y/n)")
            if not check.lower().startswith('y'):
                return format("Choose not to overwrite the existing decrypted file")
            else:
                os.remove(output_file_path)
        f = open(output_file_path, "wb")
        f.write(crypt.data)
        f.close()
        return crypt.status

    return format("File %s already exists and will not be overwritten" % output_file_path)