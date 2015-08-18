#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: maplogic.py

from configparser import ConfigParser
import os
import sys

import arrow
import mysql.connector
import numpy as np
import yaml
import drawfigure


class Stats:

    ''' here we construct a base class of the result'''

    STATS_TYPES = (
                    'user',
                    'order',
                  )

    CONFIG_YAML_PATH = os.path.abspath(os.path.dirname(__file__))\
        + '/' + 'conf/stats.yaml'
    CONFIG_PATH = os.path.abspath(os.path.dirname(__file__)) \
        + '/conf/stats.conf'
    IMG_PATH = 'static/stats_images/'
    if not os.path.exists(IMG_PATH):
        os.makedirs(IMG_PATH)

    # Here we define the standard return value
    # if success is False， you should flash the err_message
    # data will include what should be showed in a table on page
    result = {
                'success':          False,
                'err_message':      '暂不支持此统计',
                'title':            '',
                'sections':         [],
             }

    def __init__(self):
        # generate general stat dates
        self.line_color = ('orange', 'blue', 'red', 'green',
                           'purple', 'yellow', 'grey', 'black')
        self.today = arrow.now('Asia/Shanghai')
        self.end_date = arrow.now('Asia/Shanghai').replace(days=-1)
        self.start_date_month = self.end_date.replace(days=-30)
        self.stats_dates_month = []
        for dt in arrow.Arrow.range('day', self.start_date_month,
                                    self.end_date):
            self.stats_dates_month.append(dt.format('YY-MM-DD'))
        self.x_data_month = np.arange(0, len(self.stats_dates_month))

    def analyze(self, stats_type):
        # checking if the stats_type is legal
        if not isinstance(stats_type, str)\
           and stats_type not in self.STATS_TYPES:
            self.result['err_message'] = '参数错误'
            return self.result

        # method_name = 'get_{0}_data'.format(stats_type)
        # method = getattr(self, method_name, lambda: self.result)
        # return method()

        try:
            # method_name = 'get_{0}_data'.format(stats_type)
            # method = getattr(self, method_name, lambda: self.result)
            # return method()
            return self.get_data(stats_type)
        except:
            err_message = '{0}: {1}'.format(str(sys.exc_info()[0]),
                                            str(sys.exc_info()[1]))
            self.result['err_message'] = err_message
            return self.result

    def get_data(self, stats_type):
        if not os.path.exists(self.CONFIG_YAML_PATH):
            self.result['err_message'] = '未找到YAML配置文件'
            return self.result

        # the node info to be dealed
        sections = None
        title = None
        with open(self.CONFIG_YAML_PATH, encoding='utf-8') as f:
            yaml_data = yaml.load(f)

            # getting correspoding yaml node
            sections = None
            for job in yaml_data:
                if 'routine jobs' in job.keys():
                    for r_job in job['routine jobs']:
                        if stats_type == r_job["stats"]:
                            title = r_job['title']
                            sections = r_job['sections']
                            config_section = r_job['CONFIG']

        if sections is None:
            self.result['err_message'] = '未找到处理类型 {0}'\
                                         ''.format(stats_type)
            return self.result

        # get connect db info
        if not os.path.exists(self.CONFIG_PATH):
            self.result['err_message'] = '未找到config配置文件'
            return self.result
        config = ConfigParser()
        config.read(self.CONFIG_PATH)

        # get db params
        try:
            db_config = {
                          'host': config.get(config_section, 'Host'),
                          'user': config.get(config_section, 'User'),
                          'password': config.get(config_section, 'Password'),
                          'database': config.get(config_section, 'Database'),
                          'port': config.get(config_section, 'Port'),
                        }
        except:
            db_config = None
        # getting data
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()

        show_legend = True
        show_annotate = True
        for section in sections:
            for figure in section['figures']:
                # Draw every figure
                figure['url'] = self.IMG_PATH\
                                + figure['url']\
                                + '_'\
                                + arrow.now().format('YYDDDD')\
                                + '.png'
                y_data = []
                for line in figure['lines']:
                    # get data
                    stats_data = []
                    start_date = self.start_date_month.format('YYYY-MM-DD')
                    end_date = self.today.format('YYYY-MM-DD')
                    sql_str = line['mysql'].replace('{start_date}',
                                                    start_date)
                    sql_str = sql_str.replace('{end_date}',
                                              end_date)

                    cursor.execute(sql_str)
                    raw_data = cursor.fetchall()
                    for (order_date, order_count) in raw_data:
                        stats_data.append(order_count)

                    y_data.append({'data': np.array(stats_data),
                                   'label': line['label']})

                if y_data:
                    drawfigure.draw_line_chart('month',
                                               figure['url'],
                                               self.x_data_month,
                                               y_data,
                                               self.stats_dates_month,
                                               title=figure['name'],
                                               ylabel=figure['ylabel'],
                                               show_annotate=show_annotate,
                                               show_legend=show_legend)

        cnx.close()

        # build response
        self.result['success'] = True
        self.result['err_message'] = ''
        self.result['title'] = title
        self.result['sections'] = sections

        return self.result
