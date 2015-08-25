#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: kits.py

import os
from configparser import ConfigParser


def get_mysql_config(config_file_path, section_name):
    # get connect db info
    if not os.path.exists(config_file_path):
        return None

    config = ConfigParser()
    config.read(config_file_path)

    # get db params
    try:
        db_config = {
                      'host': config.get(section_name, 'Host'),
                      'user': config.get(section_name, 'User'),
                      'password': config.get(section_name, 'Password'),
                      'database': config.get(section_name, 'Database'),
                      'port': config.get(section_name, 'Port'),
                    }
        return db_config
    except:
        return None
