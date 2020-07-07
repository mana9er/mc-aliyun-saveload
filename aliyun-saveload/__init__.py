import os
import sys
dependencies = ['mcBasicLib']


def load(log, core):
    try:
        import oss2
    except:
        log.error('dependency: python package "oss2" is not installed. \
        Please see https://help.aliyun.com/document_detail/85288.html for help.')
        log.error('Plugin aliyun-saveload is not going to work')
        return
    try:
        # noinspection PyProtectedMember
        import crcmod._crcfunext
    except:
        log.error('The C extension of python package "crcmod" is not correctly installed. \
        Please see https://help.aliyun.com/document_detail/85288.html for help.')
        log.error('Plugin aliyun-saveload is not going to work')
        return
    from . import main, conf, utils
    root_dir = os.path.join(core.root_dir, 'aliyun-saveload')
    config_filename = os.path.join(root_dir, 'config.json')
    timer_filename = os.path.join(root_dir, 'auto-backup-timer.txt')
    try:
        conf.config = conf.Config(config_filename)
    except:
        log.error(str(sys.exc_info()[0]) + str(sys.exc_info()[1]))
        log.error('Plugin aliyun-saveload is not going to work.')
        return
    conf.config.timer_filename = timer_filename
    conf.config.log = log
    conf.help_message = conf.load_text()
    main.SaveLoad(log, core)
    return None
