import os
import json
import shutil
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class CosmicFileLocker:
    def __init__(self):
        self.vault_dir = "cosmic_vault"
        self.recycle_dir = "recycle_bin"
        self.metadata_file = "metadata.json"
        os.makedirs(self.vault_dir, exist_ok=True)
        os.makedirs(self.recycle_dir, exist_ok=True)

    def _generate_key(self, password, salt=None):
        if not password or not isinstance(password, str):
            raise ValueError("Password must be a non-empty string")
        if salt is None:
            salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return Fernet(key), salt

    def lock_file(self, user_id, password, file_path):
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Source file not found: {file_path}")
            with open(file_path, 'rb') as f:
                file_data = f.read()
            cipher_suite, salt = self._generate_key(password)
            encrypted_data = cipher_suite.encrypt(file_data)
            file_name = f"{user_id}_{os.path.basename(file_path)}.enc"
            vault_path = os.path.join(self.vault_dir, file_name).replace('\\', '/')
            os.makedirs(os.path.dirname(vault_path) or '.', exist_ok=True)
            with open(vault_path, 'wb') as f:
                f.write(salt + encrypted_data)
            metadata = self._load_metadata()
            metadata[file_name] = {
                'user_id': user_id,
                'original_name': os.path.basename(file_path),
                'salt': base64.b64encode(salt).decode('utf-8')
            }
            self._save_metadata(metadata)
            os.remove(file_path)
            logging.debug(f"Successfully locked file: {file_name}")
            return file_name
        except Exception as e:
            logging.exception(f"Error locking file: {e}")
            return None

    def list_files(self, user_id):
        metadata = self._load_metadata()
        return [f for f, info in metadata.items() if info['user_id'] == user_id and f not in self._get_recycled_files()]

    def retrieve_file(self, file_name, user_id, password):
        metadata = self._load_metadata()
        if file_name in metadata and metadata[file_name]['user_id'] == user_id:
            file_path = os.path.join(self.vault_dir, file_name).replace('\\', '/')
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    salt = base64.b64decode(metadata[file_name]['salt'])
                    encrypted_data = f.read()[16:]  # Skip the 16-byte salt prefix
                cipher_suite, _ = self._generate_key(password, salt)
                return cipher_suite.decrypt(encrypted_data)
        logging.error(f"Failed to retrieve file: {file_name} for user: {user_id}")
        return None

    def delete_file(self, file_name, user_id, password):
        metadata = self._load_metadata()
        if file_name in metadata and metadata[file_name]['user_id'] == user_id:
            src_path = os.path.join(self.vault_dir, file_name).replace('\\', '/')
            dst_path = os.path.join(self.recycle_dir, file_name).replace('\\', '/')
            if os.path.exists(src_path):
                try:
                    os.makedirs(os.path.dirname(dst_path) or '.', exist_ok=True)
                    shutil.move(src_path, dst_path)  # Use shutil.move for better cross-device support
                    logging.debug(f"Moved {file_name} to recycle bin")
                    return True
                except Exception as e:
                    logging.exception(f"Error moving file {file_name} to recycle bin: {e}")
                    return False
            else:
                logging.error(f"Source file not found: {src_path}")
                return False
        logging.error(f"Unauthorized delete attempt for file: {file_name} by user: {user_id}")
        return False

    def list_recycle_bin(self, user_id):
        metadata = self._load_metadata()
        return [f for f in os.listdir(self.recycle_dir) if f in metadata and metadata[f]['user_id'] == user_id]

    def restore_file(self, file_name, user_id, password):
        metadata = self._load_metadata()
        if file_name in metadata and metadata[file_name]['user_id'] == user_id:
            src_path = os.path.join(self.recycle_dir, file_name).replace('\\', '/')
            dst_path = os.path.join(self.vault_dir, file_name).replace('\\', '/')
            if os.path.exists(src_path):
                os.makedirs(os.path.dirname(dst_path) or '.', exist_ok=True)
                shutil.move(src_path, dst_path)  # Use shutil.move for consistency
                logging.debug(f"Restored {file_name} from recycle bin")
                return True
        logging.error(f"Failed to restore file: {file_name}")
        return False

    def _load_metadata(self):
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                logging.error(f"Failed to decode metadata.json: {e}")
                return {}
        return {}

    def _save_metadata(self, metadata):
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=4)
        except IOError as e:
            logging.error(f"Failed to save metadata.json: {e}")

    def _get_recycled_files(self):
        return set(os.listdir(self.recycle_dir))