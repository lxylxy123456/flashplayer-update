# 
# flashplayer-update - Automatically Install the Flash plugin
# Copyright (C) 2019  lxylxy123456
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# 

'''
	Download Adobe Flashplayer automatically and install it for Firefox
'''

import re, os, sys, shutil, requests
import tarfile
from subprocess import Popen
from datetime import datetime, timedelta

PROTO = 'https://'
HOST = 'get.adobe.com'
MASTER_URL = '/cn/flashplayer/'
UserAgent = ('User-Agent: Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:66.0) '
			'Gecko/20100101 Firefox/66.0')
HEADERS =  {'User-Agent': UserAgent }
TMP_NAME = '/tmp/.flashplayer.py-cache/'
TAR_NAME = 'flashplayer.tar.gz'
TAR_FNAME = os.path.join(TMP_NAME, TAR_NAME)
SO_NAME = 'libflashplayer.so'
SO_FNAME = os.path.join(TMP_NAME, SO_NAME)
INSTALL_PATH = '/usr/lib64/mozilla/plugins/'
INSTALL_NAME = os.path.join(INSTALL_PATH, SO_NAME)
VER_NAME = 'libflashplayer.so.version'
VER_FNAME = os.path.join(INSTALL_PATH, VER_NAME)

def get_download_page_1() :
	resp = requests.get(PROTO + HOST + MASTER_URL, headers=HEADERS)
	# search for "setTypeOptions"
	assert resp.text.count('case "1":') == 1	# APT
	assert resp.text.count('case "2":') == 1	# YUM
	assert resp.text.count('case "3":') == 1	# .tar.gz
	assert resp.text.count('case "4":') == 1	# .rpm
	assert resp.text.count('default:')
	case_code = resp.text.split('case "3":', 1)[1].split('case "4":')[0]
	assert case_code.count('$("#buttonDownload").attr("href","') == 1
	exp = '\$\("#buttonDownload"\).attr\("href","(.+)"\);'
	href = re.search(exp, case_code).groups()[0]
	exp2 = '<strong>版本 ([\d\.]+)</strong>'
	version = re.search(exp2, resp.text).groups()[0]
	return href, version

def get_download_page_2(link) :
	assert link.startswith('/cn/flashplayer/download/')
	resp = requests.get(PROTO + HOST + link, headers=HEADERS)
	exp = 'setTimeout\("location.href = \'(.+)\';", 2000\);'
	return re.search(exp, resp.text).groups()[0]

def download(link, tar_name=TAR_FNAME) :
	resp = requests.get(link, headers=HEADERS, stream=True)
	os.makedirs(TMP_NAME, exist_ok=True)
	open(tar_name, 'wb').write(resp.raw.read())
	return tar_name

def extract(tar_name=TAR_FNAME, tmp_path=TMP_NAME) :
	tar = tarfile.open(tar_name)
	tar.extract(SO_NAME, path=tmp_path)
	return os.path.join(tmp_path, SO_NAME)

def install(so_name=SO_FNAME, install_path=INSTALL_PATH) :
	# requires root privilege
	install_name = os.path.join(install_path, SO_NAME)
	if os.path.exists(install_name) :
		target = datetime.now().strftime('backup-%Y%m%d%H%M%S.so')
		full_target = os.path.join(TMP_NAME, target)
		assert not os.path.exists(full_target)
		shutil.move(install_name, full_target)
	assert not os.path.exists(install_name)
	shutil.move(so_name, install_name)
	os.chmod(install_name, 0o755)
	return install_name

def get_version() :
	if os.path.exists(VER_FNAME) :
		return open(VER_FNAME).read().strip()

def set_version(version) :
	open(VER_FNAME, 'w').write(version)

def main() :
	link, version = get_download_page_1()
	if version == get_version() :
		print('Installed version is latest')
		return
	link2 = get_download_page_2(link)
	tar_name = download(link2)
	so_name = extract(tar_name)
	set_version('0.0.0.0')
	install_name = install(so_name)
	print('Installed')
	set_version(version)
	print('Updated version record')

if __name__ == '__main__' :
	main()

