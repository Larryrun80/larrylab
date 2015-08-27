#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: marketinglogic.py

import os
import re
import sys

import arrow
import mysql.connector
import yaml

import kits


class MarketingTracker():
    """methods collection for Marketing tracking"""

    CONFIG_YAML_PATH = os.path.abspath(os.path.dirname(__file__))\
        + '/' + 'conf/marketing.yaml'
    CONFIG_PATH = os.path.abspath(os.path.dirname(__file__)) \
        + '/conf/stats.conf'
    DATA_TYPE = ('count', 'avg', 'sum', 'max', 'min')

    def __init__(self, **kwargs):
        self.type = None
        self.result = {
                        'success':          False,
                        'err_message':      '未知错误',
                        'title':            '',
                        'sections':         [],
                      }
        if 'mobiles' in kwargs.keys():
            self.user_source = 'mobile'
            self.users = self.get_mobiles(kwargs['mobiles'])

    def get_data_value(self, data_type, data):
        if data_type not in self.DATA_TYPE:
            return None
        if data_type == 'count':
            return len(data)
        else:
            if len(data) == 0:
                return 0
            return data[0][0]

    def get_mobiles(self, str_mobiles):
        regex = re.compile(r'1\d{10}', re.IGNORECASE)
        str_mobiles = str_mobiles.replace('，', ',')
        str_mobiles = str_mobiles.replace('\r', ',')
        str_mobiles = str_mobiles.replace('\n', ',')
        str_mobiles = str_mobiles.replace(' ', ',')
        mobiles = filter(None, str_mobiles.split(','))

        res = ''
        checked = []
        for mobile in mobiles:
            if not re.match(regex, mobile):
                res = 'wrong no: {0}'.format(mobile)
                break
            else:
                checked.append(mobile)

        if res == '':
            res = ', '.join(checked)
        return res

    def get_user_ids(self, str_source, data_type):
        if data_type is None:
            raise RuntimeError('未定义的数据源类型')

        ids = []
        general_name = ''
        r_dates = []
        with open(self.CONFIG_YAML_PATH, encoding='utf-8') as f:
            yaml_data = yaml.load(f)

            # getting correspoding yaml node
            for job in yaml_data:
                if 'get register info' in job.keys():
                    for sub_job in job['get register info']:
                        sub_job_key = 'from_' + data_type
                        if sub_job["id"] == sub_job_key:
                            total_user = 0
                            section_name = sub_job['db_info']
                            sql_str = sub_job['mysql']
                            display_name = sub_job['name']
                            db_config = kits.get_mysql_config(self.CONFIG_PATH,
                                                              section_name)
                            if db_config is None:
                                raise RuntimeError('读取数据库配置失败')

                            cnx = mysql.connector.connect(**db_config)
                            cursor = cnx.cursor()
                            sql_str = sql_str.replace('{source_data}',
                                                      '({0})'
                                                      ''.format(str_source))
                            cursor.execute(sql_str)
                            users = cursor.fetchall()

                            if len(users) > 10000:
                                cnx.close()
                                raise RuntimeError('处理数据过多，请分批处理，'
                                                   '单次处理数据应小于10000条')
                            if len(users) == 0:
                                cnx.close()
                                raise RuntimeError('未找到注册用户')

                            # dealing general info
                            for (user_id, r_date) in users:
                                ids.append(str(user_id))
                                r_dates.append(arrow.get(r_date, 'YYYY-MM-DD'))

                            if data_type == 'cards':
                                sql_str_total = 'select name, quantity '\
                                                'from prepaid_card_batch '\
                                                'where id='\
                                                '{0};'.format(str_source)
                                cursor.execute(sql_str_total)
                                cards_info = cursor.fetchall()
                                if len(cards_info) == 1:
                                    general_name = cards_info[0][0]
                                    total_user = cards_info[0][1]
                                else:
                                    cnx.close()
                                    raise RuntimeError('获取卡信息失败')

                            if data_type == 'mobiles':
                                general_name = '用户手机信息'
                                total_user = len(str_source.split(', '))

                            min_r_date = min(r_dates).format('YYYY-MM-DD')
                            max_r_date = max(r_dates).format('YYYY-MM-DD')
                            general_info = {
                                                'name': '{0} <br> [{1} ~ {2}]'
                                                ''.format(general_name,
                                                          min_r_date,
                                                          max_r_date),
                                                'value': total_user
                            }
                            cnx.close()

                            # dealing register info
                            value = self.get_data_value(sub_job['type'],
                                                        users)
                            register_info = {
                                                'name':     display_name,
                                                'value':    value,
                                            }

                            # add to list
                            self.result['sections'].append(general_info)
                            self.result['sections'].append(register_info)

        return ids

    def get_marketing_info(self, str_mobiles, data_type):
        try:
            ids = self.get_user_ids(str_mobiles, data_type)

            with open(self.CONFIG_YAML_PATH, encoding='utf-8') as f:
                yaml_data = yaml.load(f)

                # getting correspoding yaml node
                for job in yaml_data:
                    if 'user track' in job.keys():
                        for sub_job in job['user track']:
                            section_name = sub_job['db_info']
                            sql_str = sub_job['mysql']
                            db_config = kits.get_mysql_config(self.CONFIG_PATH,
                                                              section_name)
                            if db_config is None:
                                raise RuntimeError('读取数据库配置失败')

                            cnx = mysql.connector.connect(**db_config)
                            cursor = cnx.cursor()
                            str_ids = ', '.join(ids)
                            sql_str = sql_str.replace('{ids}',
                                                      '({0})'
                                                      ''.format(str_ids))
                            cursor.execute(sql_str)
                            user_stats = cursor.fetchall()
                            cnx.close()

                            value = self.get_data_value(sub_job['type'],
                                                        user_stats)
                            stats_info = {
                                             'name':     sub_job['name'],
                                             'value':    value,
                                         }
                            self.result['sections'].append(stats_info)

            self.result['success'] = True
            self.result['err_message'] = ''
            return self.result
        except TypeError:
            err_message = '{0}: {1}'.format(str(sys.exc_info()[0]),
                                            str(sys.exc_info()[1]))
            self.result['err_message'] = err_message
            return self.result
