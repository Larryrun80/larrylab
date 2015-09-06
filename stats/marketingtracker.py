#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: marketingtracker.py

import re

import yaml

import kits
from basemarketingtracker import MarketingTracker


class MobileMarketingTracker(MarketingTracker):
    """
        Marketing Tracker using Mobile info
    """
    def __init__(self, yaml_path, config_path, str_source):
        super().__init__(yaml_path, config_path)
        self.name = '用户手机信息'
        self.yaml_id = 'from_mobiles'
        self.user_amount = 0
        self.get_ids(str_source)

    def get_ids(self, str_source):
        str_mobiles = '({0})'.format(self.get_mobiles(str_source))

        with open(self.yaml_path, encoding='utf-8') as f:
            yaml_data = yaml.load(f)

            # getting correspoding yaml node
            for job in yaml_data:
                if 'get register info' in job.keys():
                    for sub_job in job['get register info']:
                        if sub_job["id"] == self.yaml_id:
                            sql_str = sub_job['mysql'].replace('{source_data}',
                                                               str_mobiles)
                            db_conf = kits.get_mysql_config(self.config_path,
                                                            sub_job['db_info'])
                            users = kits.get_mysql_data(db_conf, sql_str)
                            self.appand_general_info(users,
                                                     self.name,
                                                     self.user_amount)

    def get_mobiles(self, str_source):
        regex = re.compile(r'1\d{10}', re.IGNORECASE)
        str_source = str_source.replace('，', ',')
        str_source = str_source.replace('\r', ',')
        str_source = str_source.replace('\n', ',')
        str_source = str_source.replace(' ', ',')
        mobiles = filter(None, str_source.split(','))

        checked = []
        for mobile in mobiles:
            if re.match(regex, mobile):
                checked.append(mobile)

        self.user_amount = len(checked)
        return ', '.join(checked)


class CampaignMarketingTracker(MarketingTracker):
    """
        Marketing Tracker using Prepaid card info
    """
    def __init__(self, yaml_path, config_path, str_source):
        super().__init__(yaml_path, config_path)
        self.name = '充值卡信息'
        self.yaml_id = 'from_cards'
        self.user_amount = 0
        self.get_ids(str_source)

    def get_ids(self, str_source):
        with open(self.yaml_path, encoding='utf-8') as f:
            yaml_data = yaml.load(f)

            # getting correspoding yaml node
            for job in yaml_data:
                if 'get register info' in job.keys():
                    for sub_job in job['get register info']:
                        if sub_job["id"] == self.yaml_id:
                            sql_str = sub_job['mysql'].replace('{source_data}',
                                                               str_source)
                            db_conf = kits.get_mysql_config(self.config_path,
                                                            sub_job['db_info'])
                            self.get_campaign_info(db_conf, str_source)
                            users = kits.get_mysql_data(db_conf, sql_str)
                            self.appand_general_info(users,
                                                     self.name,
                                                     self.user_amount)

    def get_campaign_info(self, db_conf, str_source):
        sql_str_total = 'select name, quantity '\
                        'from prepaid_card_batch '\
                        'where id='\
                        '{0};'.format(str_source)
        campaign_info = kits.get_mysql_data(db_conf, sql_str_total)

        if len(campaign_info) == 1:
            self.name = campaign_info[0][0]
            self.user_amount = campaign_info[0][1]
        else:
            raise RuntimeError('获取卡信息失败')


class WechatMarketingTracker(MarketingTracker):
    """
        Marketing Tracker using wechat info
    """
    def __init__(self, yaml_path, config_path, str_source):
        super().__init__(yaml_path, config_path)
        self.name = '用户微信账号'
        self.yaml_id = 'from_wechat'
        self.user_amount = 0
        self.get_ids(str_source)

    def get_ids(self, str_source):
        str_wechat = '({0})'.format(self.get_usernames(str_source))

        with open(self.yaml_path, encoding='utf-8') as f:
            yaml_data = yaml.load(f)

            # getting correspoding yaml node
            for job in yaml_data:
                if 'get register info' in job.keys():
                    for sub_job in job['get register info']:
                        if sub_job["id"] == self.yaml_id:
                            sql_str = sub_job['mysql'].replace('{source_data}',
                                                               str_wechat)
                            db_conf = kits.get_mysql_config(self.config_path,
                                                            sub_job['db_info'])
                            users = kits.get_mysql_data(db_conf, sql_str)
                            self.appand_general_info(users,
                                                     self.name,
                                                     self.user_amount)

    def get_usernames(self, str_source):
        str_source = str_source.replace('\r', ',')
        str_source = str_source.replace('\n', ',')
        usernames = filter(None, str_source.split(','))

        dealed = []
        for name in usernames:
            dealed.append("'{0}'".format(name))

        self.user_amount = len(dealed)
        return ', '.join(dealed)
