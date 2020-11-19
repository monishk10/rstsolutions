import requests
import os
import gc
import shutil


class OTAUpdater:
    def __init__(self, github_repo):
        self.github_repo = github_repo.rstrip(
            '/').replace('https://github.com', 'https://api.github.com/repos')
        self.working_dir = '/home/pi/rstsolutions/'

    def get_latest_version(self):
        latest_release = requests.get(self.github_repo + '/releases/latest')
        version = latest_release.json()["tag_name"]
        return version

    def get_current_version(self, version_file_name='.version'):
        if version_file_name in os.listdir(self.working_dir + 'main/'):
            f = open(self.working_dir + 'main/' + version_file_name, 'r')
            version = f.read()
            f.close()
            return version
        return '0.0'

    def check_for_update(self):
        current_version = self.get_current_version()
        latest_version = self.get_latest_version()
        print('Checking version... ')
        print('\tCurrent version: ', current_version)
        print('\tLatest version: ', latest_version)
        if latest_version > current_version:
            print('New version available, will download and install on next reboot')
            os.mkdir(self.working_dir + 'next')
            with open(self.working_dir + 'next/.version_on_reboot', 'w') as versionfile:
                versionfile.write(latest_version)
        return latest_version

    def download_and_install_update_if_available(self):
        latest_version = self.check_for_update()
        if 'next' in os.listdir(self.working_dir):
            if '.version_on_reboot' in os.listdir(self.working_dir + 'next'):
                self.download_all_files(
                    self.github_repo + '/contents/main', latest_version)
                self.rmtree(self.working_dir + 'main')
                os.rename(self.working_dir + 'next/.version_on_reboot',
                          self.working_dir + 'next/.version')
                os.rename(self.working_dir + 'next', self.working_dir + 'main')
                print("Updated to ({})".format(latest_version))

    def download_all_files(self, root_url, version):
        file_list = requests.get(root_url + '?ref=refs/tags/' + version)
        file_list = file_list.json()
        for file in file_list:
            if file['type'] == 'file':
                download_url = file['download_url']
                download_path = self.working_dir + 'next/' + file['name']
                self.download_file(download_url.replace(
                    'refs/tags/', ''), download_path)

    def download_file(self, url, path):
        print('\tDownloading: ', path)
        with open(path, 'w') as outfile:
            try:
                response = requests.get(url)
                outfile.write(response.text)
            finally:
                outfile.close()
                gc.collect()

    def rmtree(self, directory):
        shutil.rmtree(directory)
