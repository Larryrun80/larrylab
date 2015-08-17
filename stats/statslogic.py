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

    IMG_PATH = 'static/stats_images/'
    IMG_PATH_REAL = os.path.abspath(os.path.dirname(__file__))
    IMG_PATH_REAL += '/' + IMG_PATH
    if not os.path.exists(IMG_PATH_REAL):
        os.makedirs(IMG_PATH_REAL)

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
                  + '/conf/stats.conf'
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

    def analyze(self, stats_type):
        # checking if the stats_type is legal
        if not isinstance(stats_type, str)\
           and stats_type not in self.STATS_TYPES:
            self.result['err_message'] = '参数错误'
            return self.result

        method_name = 'get_{0}_data'.format(stats_type)
        method = getattr(self, method_name, lambda: self.result)
        return method()

        try:
            method_name = 'get_{0}_data'.format(stats_type)
            method = getattr(self, method_name, lambda: self.result)
            return method()
        except Exception as e:
            self.result['err_message'] = str(e)
            return self.result

    def get_user_data(self):
        # generating image path to restore
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

        show_legend = True
        show_annotate = True
        drawfigure.draw_line_chart('month',
                                   self.IMG_PATH_REAL + save_file_name,
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

    def get_order_data(self):
        bargain_img = 'bargain_order_month_stats_{0}.png'\
                      ''.format(arrow.now().format('YYDDDD'))
        countdown_img = 'countdown_order_month_stats_{0}.png'\
                        ''.format(arrow.now().format('YYDDDD'))
        shake_img = 'shake_order_month_stats_{0}.png'\
                    ''.format(arrow.now().format('YYDDDD'))

        sections = [
                    {
                      'section_seq': 1,
                      'section': '往下拍',
                      'figures': []
                    },
                    {
                      'section_seq': 2,
                      'section': '倒计时',
                      'figures': []
                    },
                    {
                      'section_seq': 3,
                      'section': '睡前摇',
                      'figures': []
                    },
                   ]

        figures = [
                    {
                      'section_seq': 1,
                      'figure_seq': 1,
                      'alt_text': '30天往下拍订单',
                      'figure_url': '{0}{1}'
                                    ''.format(self.IMG_PATH,
                                              bargain_img),
                      'y_label': '订单数'
                    },
                    {
                      'section_seq': 2,
                      'figure_seq': 1,
                      'alt_text': '30天倒计时订单',
                      'figure_url': '{0}{1}'
                                    ''.format(self.IMG_PATH,
                                              countdown_img),
                      'y_label': '订单数'
                    },
                    {
                      'section_seq': 3,
                      'figure_seq': 1,
                      'alt_text': '30天睡前摇订单',
                      'figure_url': '{0}{1}'
                                    ''.format(self.IMG_PATH,
                                              shake_img),
                      'y_label': '订单数'
                    },
                  ]

        lines = [
                  # 往下拍全部订单
                  {
                    'section_seq': 1,
                    'figure_seq': 1,
                    'sql':   '''
                   SELECT date_format(o.created_at, '%Y-%m-%d') o_date,
                          count(0) order_count
                     FROM product_order o
                    WHERE o.created_at>'{start_date}'
                      AND o.created_at<'{end_date}'
                      AND (o.type=1 OR o.type=2)
                      AND o.status in (2, 3, 4, 6, 8, 11)
                 GROUP BY date_format(o.created_at, '%Y-%m-%d')
                 ORDER BY date_format(o.created_at, '%Y-%m-%d')
                 '''.format(start_date=self.start_date_month
                                           .format('YYYY-MM-DD'),
                            end_date=self.today.format('YYYY-MM-DD')),
                    'label': '全部订单',
                  },
                  # 往下拍支付宝支付
                  {
                    'section_seq': 1,
                    'figure_seq': 1,
                    'sql':   '''
                   SELECT date_format(o.created_at, '%Y-%m-%d') o_date,
                          count(0) order_count
                     FROM product_order o
                LEFT JOIN order_payment_record opr ON o.id=opr.product_order_id
                    WHERE o.created_at>'{start_date}'
                      AND o.created_at<'{end_date}'
                      AND (o.type=1 OR o.type=2)
                      AND o.status in (2, 3, 4, 6, 8, 11)
                      AND opr.is_active=1
                      AND opr.payment_method in (2, 4, 5)
                 GROUP BY date_format(o.created_at, '%Y-%m-%d')
                 ORDER BY date_format(o.created_at, '%Y-%m-%d')
                 '''.format(start_date=self.start_date_month
                                           .format('YYYY-MM-DD'),
                            end_date=self.today.format('YYYY-MM-DD')),
                    'label': '支付宝订单',
                  },
                  # 往下拍微信支付
                  {
                    'section_seq': 1,
                    'figure_seq': 1,
                    'sql':   '''
                   SELECT date_format(o.created_at, '%Y-%m-%d') o_date,
                          count(0) order_count
                     FROM product_order o
                LEFT JOIN order_payment_record opr ON o.id=opr.product_order_id
                    WHERE o.created_at>'{start_date}'
                      AND o.created_at<'{end_date}'
                      AND (o.type=1 OR o.type=2)
                      AND o.status in (2, 3, 4, 6, 8, 11)
                      AND opr.is_active=1
                      AND opr.payment_method=3
                 GROUP BY date_format(o.created_at, '%Y-%m-%d')
                 ORDER BY date_format(o.created_at, '%Y-%m-%d')
                 '''.format(start_date=self.start_date_month
                                           .format('YYYY-MM-DD'),
                            end_date=self.today.format('YYYY-MM-DD')),
                    'label': '微信订单',
                  },
                  # 往下拍余额支付
                  {
                    'section_seq': 1,
                    'figure_seq': 1,
                    'sql':   '''
                   SELECT date_format(t.created_at, '%Y-%m-%d') o_date,
                          count(0) order_count
                     FROM (
                 SELECT o.id, o.created_at, max(opr.payment_method) method
                     FROM product_order o
                LEFT JOIN order_payment_record opr ON o.id=opr.product_order_id
                    WHERE o.created_at>'{start_date}'
                      AND o.created_at<'{end_date}'
                      AND (o.type=1 OR o.type=2)
                      AND o.status in (2, 3, 4, 6, 8, 11)
                      AND opr.`is_active`=1
                 GROUP BY o.id)t
                    WHERE t.method=1
                 GROUP BY date_format(t.created_at, '%Y-%m-%d')
                 ORDER BY date_format(t.created_at, '%Y-%m-%d')
                 '''.format(start_date=self.start_date_month
                                           .format('YYYY-MM-DD'),
                            end_date=self.today.format('YYYY-MM-DD')),
                    'label': '余额订单',
                  },
                  # 倒计时所有订单
                  {
                    'section_seq': 2,
                    'figure_seq': 1,
                    'sql':   '''
                   SELECT date_format(o.created_at, '%Y-%m-%d') o_date,
                          count(0) order_count
                     FROM product_order o
                    WHERE o.created_at>'{start_date}'
                      AND o.created_at<'{end_date}'
                      AND o.type=3
                      AND o.status in (2, 3, 4, 6, 8, 11)
                 GROUP BY date_format(o.created_at, '%Y-%m-%d')
                 ORDER BY date_format(o.created_at, '%Y-%m-%d')
                 '''.format(start_date=self.start_date_month
                                           .format('YYYY-MM-DD'),
                            end_date=self.today.format('YYYY-MM-DD')),
                    'label': '全部订单',
                  },
                  # 倒计时支付宝支付
                  {
                    'section_seq': 2,
                    'figure_seq': 1,
                    'sql':   '''
                   SELECT date_format(o.created_at, '%Y-%m-%d') o_date,
                          count(0) order_count
                     FROM product_order o
                LEFT JOIN order_payment_record opr ON o.id=opr.product_order_id
                    WHERE o.created_at>'{start_date}'
                      AND o.created_at<'{end_date}'
                      AND o.type=3
                      AND o.status in (2, 3, 4, 6, 8, 11)
                      AND opr.is_active=1
                      AND opr.payment_method in (2, 4, 5)
                 GROUP BY date_format(o.created_at, '%Y-%m-%d')
                 ORDER BY date_format(o.created_at, '%Y-%m-%d')
                 '''.format(start_date=self.start_date_month
                                           .format('YYYY-MM-DD'),
                            end_date=self.today.format('YYYY-MM-DD')),
                    'label': '支付宝订单',
                  },
                  # 倒计时微信支付
                  {
                    'section_seq': 2,
                    'figure_seq': 1,
                    'sql':   '''
                   SELECT date_format(o.created_at, '%Y-%m-%d') o_date,
                          count(0) order_count
                     FROM product_order o
                LEFT JOIN order_payment_record opr ON o.id=opr.product_order_id
                    WHERE o.created_at>'{start_date}'
                      AND o.created_at<'{end_date}'
                      AND o.type=3
                      AND o.status in (2, 3, 4, 6, 8, 11)
                      AND opr.is_active=1
                      AND opr.payment_method=3
                 GROUP BY date_format(o.created_at, '%Y-%m-%d')
                 ORDER BY date_format(o.created_at, '%Y-%m-%d')
                 '''.format(start_date=self.start_date_month
                                           .format('YYYY-MM-DD'),
                            end_date=self.today.format('YYYY-MM-DD')),
                    'label': '微信订单',
                  },
                  # 睡前摇全部订单
                  {
                    'section_seq': 3,
                    'figure_seq': 1,
                    'sql':   '''
                   SELECT date_format(o.created_at, '%Y-%m-%d') o_date,
                          count(0) order_count
                     FROM product_order o
                    WHERE o.created_at>'{start_date}'
                      AND o.created_at<'{end_date}'
                      AND o.type=6
                 GROUP BY date_format(o.created_at, '%Y-%m-%d')
                 ORDER BY date_format(o.created_at, '%Y-%m-%d')
                 '''.format(start_date=self.start_date_month
                                           .format('YYYY-MM-DD'),
                            end_date=self.today.format('YYYY-MM-DD')),
                    'label': '全部订单',
                  },
                ]

        # getting total bargain data
        cnx = mysql.connector.connect(**self.db_config)
        cursor = cnx.cursor()

        for figure in figures:
            # Draw every figure
            s_seq = figure['section_seq']
            f_seq = figure['figure_seq']
            show_legend = True
            show_annotate = True

            # building figure data
            # y_data include 3 part: 1. data 2. line_label
            y_data = []
            for line in lines:
                if line['section_seq'] == s_seq and\
                   line['figure_seq'] == f_seq:
                    # get data
                    stats_data = []
                    cursor.execute(line['sql'])
                    raw_data = cursor.fetchall()
                    for (order_date, order_count) in raw_data:
                        stats_data.append(order_count)

                    y_data.append({'data': np.array(stats_data),
                                   'label': line['label']})

            if y_data:
                drawfigure.draw_line_chart('month',
                                           figure['figure_url'],
                                           self.x_data_month,
                                           y_data,
                                           self.stats_dates_month,
                                           title=figure['alt_text'],
                                           ylabel=figure['y_label'],
                                           show_annotate=show_annotate,
                                           show_legend=show_legend)

        cnx.close()

        # build response
        self.result['success'] = True
        self.result['err_message'] = ''
        self.result['title'] = '订单统计'

        for section in sections:
            for figure in figures:
                if figure['section_seq'] == section['section_seq']:
                    section['figures'].append(figure)
            self.result['sections'].append(section)

        return self.result
