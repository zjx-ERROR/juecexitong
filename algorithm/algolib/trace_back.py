#!/usr/bin/python
__author__ = 'zJx'

import logging


def traceback_log(file_name):
    logger = logging.getLogger()
    fh = logging.FileHandler(file_name, 'a+', encoding='utf-8')
    formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s\n")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    def get_func(func):
        def wapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except Exception as e:
                logger.exception(e)

        return wapper

    return get_func
