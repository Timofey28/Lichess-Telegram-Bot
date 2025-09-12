import os
import traceback

from fabric import Connection, Result
from colorama import init as colorama_init
import humanize

from data import HOST, USER, PRIVATE_KEY_PATH, SERVER_WD

LOGS_FOLDER = 'logs'
SUBFOLDER_INDENT = ' ' * 4


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    ENDC = '\033[0m'
    PURPLE = '\033[35m'
    DARKGRAY = '\033[90m'


class SFTPConnection:
    def __init__(self):
        self.conn = Connection(host=HOST, user=USER, connect_kwargs={'key_filename': PRIVATE_KEY_PATH})

    def folder_exists(self, folder_path: str) -> bool:
        result: Result = self.conn.run(f'test -d "{folder_path}"', hide=True, warn=True)
        return result.ok

    is_folder: callable = folder_exists

    def get_folder_items(self, remote_path: str):
        result: Result = self.conn.run(f'find "{remote_path}" -maxdepth 1 -print', hide=True, encoding='utf-8')
        if not result:
            raise Exception(f'Failed to get folder objects: {remote_path}. Error: {result.stderr}')
        files_and_dirs = result.stdout.strip().split('\n')
        return sorted([item for item in files_and_dirs if item and item != remote_path])

    def get(self, remote_path: str, local_path: str) -> None:
        result: Result = self.conn.get(remote_path, local_path)
        if not result:
            raise Exception(f'Failed to download file: {remote_path}. Error: {result.stderr}')

    def close(self):
        self.conn.close()


if __name__ == '__main__':
    SERVER_WD = SERVER_WD.rstrip('/')
    colorama_init()
    sftp = SFTPConnection()
    print('Connection succesfully established ...')
    try:
        files_to_download = ['info.log']
        for file in files_to_download:
            print(f'{Colors.BOLD}- {file}... {Colors.ENDC}', end='')
            try:
                sftp.get(f'{SERVER_WD}/{file}', file)
                file_size = humanize.naturalsize(os.path.getsize(file))
                print(f'{Colors.GREEN}downloaded  {Colors.PURPLE}({file_size}){Colors.ENDC}')
            except Exception as e:
                print(f'{Colors.RED}failed ({e}){Colors.ENDC}')

        print('\n*** Файл на базе! ***\n')

    except Exception as e:
        print(f'{e}\n{traceback.format_exc()}')
    finally:
        sftp.close()
