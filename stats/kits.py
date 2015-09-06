#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: kits.py

from configparser import ConfigParser
import csv
import os
import random

import arrow
import mysql.connector
import xlwt


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


def get_mysql_data(db_conf, sql_str):
    if db_conf is None:
        raise RuntimeError('读取数据库配置失败')

    cnx = mysql.connector.connect(**db_conf)
    cursor = cnx.cursor()
    cursor.execute(sql_str)
    data = cursor.fetchall()
    cnx.close()
    return data


def generate_file(file_type, data, export_dir='static/tmp/'):
    '''
        generate correspoding format file using data
    '''
    if not export_dir or export_dir == '':
        export_dir = 'static/tmp/'

    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
    tmp_file_name = arrow.now('Asia/Shanghai').format('YYYY-DDD-X')
    save_file_path = export_dir + tmp_file_name

    # if the file exists, try to generate another one
    # this step is to avoid download a wrong file
    while os.path.isfile(save_file_path):
        save_file_path += '-' + str(random.randint(0, 10000))
    save_file_path += '.' + file_type

    if file_type == 'xls':
        wb = xlwt.Workbook()
        wb.encoding = 'gbk'
        ws = wb.add_sheet('data')
        for row in range(len(data)):
            for col in range(len(data[0])):
                ws.write(row, col, data[row][col])

        wb.save(save_file_path)
        return save_file_path

    if file_type == 'csv':
        with open(save_file_path,
                  mode='w',
                  encoding='utf-8',
                  errors='ignore') as target:
            writer = csv.writer(target)
            writer.writerows(data)
        return save_file_path
