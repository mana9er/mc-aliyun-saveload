import sys
import os
import json
import shutil
import time
import oss2
from . import conf
from zipfile import ZipFile, ZIP_DEFLATED

class InitError(Exception):
    pass

def init_assert(expr, msg):
    if not expr:
        raise InitError(msg)
        
def convert_info(info_dict):
    return {
        'x-oss-meta-time': str(info_dict['time']),
        'x-oss-meta-creator': info_dict['creator'],
        'x-oss-meta-description': bytes(info_dict['description'], encoding='utf-8')
    }

def convert_info_back(headers):
    return {
        'time': int(headers['x-oss-meta-time']),
        'creator': headers['x-oss-meta-creator'],
        'description': str(bytes(headers['x-oss-meta-description'], encoding='latin-1'), encoding='utf-8')
    }

def checkobj(name):
    try:
        headers = conf.config.bucket.head_object(name).headers
        info = convert_info_back(headers)
        if name != headers['x-oss-meta-time']:
            return None
        return info
    except:
        return None

def get_backup_list():
    res = []
    for obj in oss2.ObjectIterator(conf.config.bucket):
        info = checkobj(obj.key)
        if info:
            res.append(info)
    res.sort(key=lambda v: v['time'])
    return res

def dump_timer(timer):
    filename = conf.config.timer_filename
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(str(timer))

def load_timer():
    filename = conf.config.timer_filename
    if not os.path.exists(filename):
        conf.config.log.warning('Failed to find previous auto backup timer')
        conf.config.log.info('Creating new timer file')
        timer = conf.config.auto_backup_interval
        dump_timer(timer)
        return timer
    with open(filename, 'r', encoding='utf-8') as timer_f:
        timer = int(timer_f.read())
    init_assert(timer > 0, 'Expecting positive timer')

def pack_upload(info):
    headers = convert_info(info)
    name = str(info['time'])
    tmp_filename = os.path.join(conf.config.tmp_path, name + '.zip')
    with ZipFile(tmp_filename, 'w', compression=ZIP_DEFLATED, allowZip64=True, compresslevel=1) as zipf:
        for root, dirs, files in os.walk('.'):
            for f in files:
                zipf.write(os.path.join(root, f))
    conf.config.bucket.put_object_from_file(name, tmp_filename, headers=headers)
    os.remove(tmp_filename)

def download_unpack(info):
    name = str(info['time'])
    tmp_filename = os.path.join(conf.config.tmp_path, name + '.zip')
    conf.config.bucket.get_object_to_file(name, tmp_filename)
    for filename in os.listdir('.'):
        if os.path.isdir(filename):
            shutil.rmtree(filename)
        else:
            os.remove(filename)
    shutil.unpack_archive(tmp_filename, '.')
    os.remove(tmp_filename)

def try_remove(info):
    name = str(info['time'])
    conf.config.bucket.delete_object(name)

def format_description(backup):
    time_string = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(backup['time']))
    return 'Backup made at {} by {}. Description: {}'.format(time_string, backup['creator'], backup['description'])