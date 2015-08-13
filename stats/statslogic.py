#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: maplogic.py

from configparser import ConfigParser
import os

import arrow
import mysql.connector
import numpy as np

import drawfigure


class Stats:

    ''' here we construct a base class of the result'''

    STATS_TYPES = (
                    'user',
                    'order',
                  )
    IMG_PATH = 'static/images/'

    # Here we define the standard return value
    # if success is False， you should flash the err_message
    # data will include what should be showed in a table on page
    result = {
                'success':          False,
                'err_message':      '暂不支持此统计',
                'title':            '',
                'sections':         [],
             }
    # Here is a sample of section format:
    # section = {
    #               'section_seq':  10000,
    #               'section':      'section name',
    #               'figures':      [
    #                                   {
    #                                       'figure_seq':  123
    #                                       'alt_text': 'figure_name',
    #                                       'figure_url': 'figure_url',
    #                                   }
    #                               ]
    #           }

    def __init__(self):
        config_file = os.path.abspath(os.path.dirname(__file__)) \
                  + '/conf/maps.conf'
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

        # get connect db info
        try:
            config = ConfigParser()
            config.read(config_file)

            # get db params
            self.db_config = {
                               'host': config.get('DB_INFO', 'Host'),
                               'user': config.get('DB_INFO', 'User'),
                               'password': config.get('DB_INFO', 'Password'),
                               'database': config.get('DB_INFO', 'Database'),
                               'port': config.get('DB_INFO', 'Port'),
                             }
        except Exception as e:
            self.result['err_message'] = str(e)
            return self.result

    def analyze(self, stats_type):
        # checking if the stats_type is legal
        if not isinstance(stats_type, str)\
           and stats_type not in self.STATS_TYPES:
            self.result['err_message'] = '参数错误'
            return self.result

        try:
            method_name = 'get_{0}_data'.format(stats_type)
            method = getattr(self, method_name, lambda: self.result)
            return method()
        except Exception as e:
            self.result['err_message'] = str(e)
            return self.result

    def get_user_data(self):
        # generating image path to restore
        img_path = os.path.abspath(os.path.dirname(__file__)) \
                   + '/' \
                   + self.IMG_PATH
        save_file_name = 'user_month_stats_{0}.png'\
                         ''.format(arrow.now().format('YYDDDD'))

        # getting data
        cnx = mysql.connector.connect(**self.db_config)
        sql_str = '''
                    SELECT date_format(u.created_at, '%Y-%m-%d') reg_date,
                           count(0) user_count
                      FROM user u
                     WHERE u.created_at>'{start_date}'
                       AND u.created_at<'{end_date}'
                  GROUP BY date_format(u.created_at, '%Y-%m-%d')
                  ORDER BY date_format(u.created_at, '%Y-%m-%d')
                  '''.format(start_date=self.start_date_month
                                            .format('YYYY-MM-DD'),
                             end_date=self.today.format('YYYY-MM-DD'))
        cursor = cnx.cursor()
        cursor.execute(sql_str)
        raw_data = cursor.fetchall()
        cnx.close()

        # building figure data
        stats_data = []
        for (reg_date, user_count) in raw_data:
            stats_data.append(user_count)
        # y_data include 3 part: 1. data 2. line_label
        y_data = []
        y_data.append({'data': np.array(stats_data),
                       'label': u'注册数'})
        y_data.append({'data': np.random.randint(1000, 2000,
                                                 size=len(self.x_data_month)),
                       'label': u'随机对比'})

        show_legend = True
        show_annotate = True
        drawfigure.draw_line_chart('month',
                                   img_path + save_file_name,
                                   self.x_data_month,
                                   y_data,
                                   self.stats_dates_month,
                                   title=u'用户统计',
                                   ylabel=u'注册数',
                                   show_annotate=show_annotate,
                                   show_legend=show_legend)

        # build response
        self.result['success'] = True
        self.result['err_message'] = ''
        self.result['title'] = '用户统计'

        sections = []
        figures = []
        figures.append({
                         'alt_text': '30天用户统计',
                         'figure_url': self.IMG_PATH + save_file_name,
                         'figure_seq':  1
                      })
        sections.append({
                          'section_seq': 1,
                          'section': '30天用户统计',
                          'figures': figures,
                       })
        self.result['sections'] = sections

        return self.result
