#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: basemarketingtracker.py

from abc import ABCMeta, abstractmethod
import os
import sys

import arrow
import mysql.connector
import yaml

import kits


class MarketingTracker(metaclass=ABCMeta):
    """methods collection for Marketing tracking"""

    AVAILABLE_DATA_TYPE = ('count', 'avg', 'sum', 'max', 'min')

    def __init__(self, yaml_path, config_path):
        # input_source type
        self.type = None
        self.ids = []
        if not os.path.isfile(yaml_path):
            raise RuntimeError('Not found yaml file!')
        if not os.path.isfile(config_path):
            raise RuntimeError('Not found config file!')

        self.yaml_path = yaml_path
        self.config_path = config_path
        self.result = {
                        'success':          False,
                        'err_message':      '未知错误',
                        'title':            '',
                        'res_data':         [],
                      }

    def return_stats_value(self, data_type, data):
        '''
        return a value via stats type, 'count' or 'sum' or 'avg' etc.
        '''
        if data_type not in self.AVAILABLE_DATA_TYPE:
            return None
        if data_type == 'count':
            if len(data) == 0:
                return '-'
            else:
                return len(data)
        else:
            if len(data) == 0 or not data[0][0]:
                return '-'
            else:
                return data[0][0]

    def appand_general_info(self, user_data, name, user_amount):
        '''
        user_data: ((user_id1, register_date1),
                    (user_id2, register_date2),
                    (user_id3, register_date3),
                    ......)
        '''
        if len(user_data) > 10000:
            raise RuntimeError('处理数据过多，请分批处理，'
                               '单次处理数据应小于10000条')
        if len(user_data) == 0:
            raise RuntimeError('未找到注册用户')

        unzip_data = zip(*user_data)
        self.ids = next(unzip_data)
        r_dates = next(unzip_data)

        reg_date_str = '[{0} ~ {1}]'\
                       ''.format(arrow.get(min(r_dates)).format('YYYY-MM-DD'),
                                 arrow.get(max(r_dates)).format('YYYY-MM-DD'))
        general_info = {
                            'name': '{0} <br> {1}'
                            ''.format(name, reg_date_str),
                            'value': str(user_amount)
                        }

        # add to list
        self.result['res_data'].append(general_info)

    @abstractmethod
    def get_ids(self, type, str_source):
        '''
        get user ids from input value
        should return an list of id
        '''
        pass

    def get_marketing_info(self):
        try:
            if not self.ids or len(self.ids) == 0:
                raise RuntimeError('未获取到用户id')
            str_ids = '({0})'.format(', '.join(str(x) for x in self.ids))
            self.result['ids'] = str_ids

            with open(self.yaml_path, encoding='utf-8') as f:
                yaml_data = yaml.load(f)

                # getting correspoding yaml node
                for job in yaml_data:
                    if 'user track' in job.keys():
                        for sub_job in job['user track']:
                            if sub_job['type'] not in self.AVAILABLE_DATA_TYPE:
                                raise RuntimeError('{}: 未定义的数据处理类型'
                                                   ''.format(sub_job['id']))
                            sql = sub_job['mysql'].replace('{ids}', str_ids)

                            db_conf = kits.get_mysql_config(self.config_path,
                                                            sub_job['db_info'])
                            print(sql)
                            user_stats = kits.get_mysql_data(db_conf, sql)
                            value = self.return_stats_value(sub_job['type'],
                                                            user_stats)
                            stats_info = {
                                             'name':     sub_job['name'],
                                             'id':       sub_job['id'],
                                             'value':    value,
                                             'type':     sub_job['type'],
                                         }
                            self.result['res_data'].append(stats_info)

            self.result['success'] = True
            self.result['err_message'] = ''
            return self.result

        except IndexError:
            err_message = '{0}: {1}'.format(str(sys.exc_info()[0]),
                                            str(sys.exc_info()[1]))
            self.result['err_message'] = err_message
            return self.result

    @staticmethod
    def get_export_data(r_scope, r_type, r_format, r_ids,
                        yaml_path, config_path,
                        export_dir=None):
        '''
            export data to excel or csv
            r_scope for top level of yaml data
            r_type for specfic data to get
            r_format for export file type
            r_ids for user string format ids
            like (id1, id2, id3 ...)
        '''
        AVAILABLE_FILE_FORMAT = ('csv', 'xls')

        if r_format not in AVAILABLE_FILE_FORMAT:
            raise RuntimeError('您请求了不支持的导出格式')

        try:
            with open(yaml_path, encoding='utf-8') as f:
                yaml_data = yaml.load(f)

                # getting correspoding yaml node
                for job in yaml_data:
                    if r_scope in job.keys():
                        for sub_job in job[r_scope]:
                            if r_type == sub_job['id']:
                                sql_str = sub_job['mysql']
                                db_config = kits.get_mysql_config(
                                                    config_path,
                                                    sub_job['db_info'])
                                if db_config is None:
                                        raise RuntimeError('读取数据库配置失败')
                                cnx = mysql.connector.connect(**db_config)
                                cursor = cnx.cursor()
                                sql_str = sql_str.replace('{ids}', r_ids)
                                cursor.execute(sql_str)
                                res_data = [cursor.column_names]
                                res_data += cursor.fetchall()
                                return kits.generate_file(r_format,
                                                          res_data,
                                                          export_dir)
                raise RuntimeError('没有找到需要导出的数据')
        except IndexError:
            err_message = '{0}: {1}'.format(str(sys.exc_info()[0]),
                                            str(sys.exc_info()[1]))
            return {'message': err_message}
