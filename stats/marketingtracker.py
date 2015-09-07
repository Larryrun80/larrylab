#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: marketingtracker.py

import re

import arrow
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
        source = str_source.split('=')
        with open(self.yaml_path, encoding='utf-8') as f:
            yaml_data = yaml.load(f)

            # getting correspoding yaml node
            for job in yaml_data:
                if 'get register info' in job.keys():
                    for sub_job in job['get register info']:
                        if sub_job["id"] == self.yaml_id:
                            db_conf = kits.get_mysql_config(self.config_path,
                                                            sub_job['db_info'])
                            str_bids = ''
                            if source[0] == 'bid':
                                str_bids = '({0})'.format(source[1])
                            if source[0] == 'cid':
                                str_bids = self.get_batch_ids(db_conf,
                                                              source[1])

                            if str_bids == '':
                                raise RuntimeError('查询类型异常')
                            sql_str = sub_job['mysql'].replace('{source_data}',
                                                               str_bids)

                            self.get_campaign_info(db_conf,
                                                   source[0],
                                                   source[1])
                            users = kits.get_mysql_data(db_conf, sql_str)
                            self.appand_general_info(users,
                                                     self.name,
                                                     self.user_amount)

    def get_campaign_info(self, db_conf, data_type, data_id):
        if 'bid' == data_type:
            sql_str_total = 'select name, quantity '\
                            'from prepaid_card_batch '\
                            'where id='\
                            '{0};'.format(data_id)
        if 'cid' == data_type:
            sql_str_total = 'select pcc.name, count(0) '\
                            'from prepaid_card_campaign pcc '\
                            'left join prepaid_card_batch pcb '\
                            'on pcb.prepaid_card_campaign_id=pcc.id '\
                            'left join prepaid_card pc '\
                            'on pc.prepaid_card_batch_id=pcb.id '\
                            'where pcc.id = {0} '\
                            'group by pcc.id;'.format(data_id)

        if sql_str_total:
            campaign_info = kits.get_mysql_data(db_conf, sql_str_total)
            if len(campaign_info) == 1:
                self.name = campaign_info[0][0]
                self.user_amount = campaign_info[0][1]
                return
            else:
                raise RuntimeError('获取卡信息失败')

        raise RuntimeError('异常的获取活动信息请求')

    def get_batch_ids(self, db_conf, campaign_id):
        sql_str = 'select id from prepaid_card_batch where '\
                  'prepaid_card_campaign_id=' + campaign_id
        batches = kits.get_mysql_data(db_conf, sql_str)

        if len(batches) > 0:
            str_bids = ', '.join([str(bid) for (bid,) in batches])
            return '({0})'.format(str_bids)
        raise RuntimeError('活动下没有任何充值卡')

    @staticmethod
    def get_campaigns(yaml_path, config_path, conf_section, month_span=None):
        sql = 'select id, name '\
              'from prepaid_card_campaign '
        db_conf = kits.get_mysql_config(config_path,
                                        conf_section)
        data = []

        if month_span and isinstance(month_span, int):
            start_date = arrow.now('Asia/Shanghai').replace(months=-month_span)
            sql += " where created_at>'{0}'"\
                   "".format(start_date.format('YYYY-MM-DD'))
        sql += " order by created_at desc"
        campaign_info = kits.get_mysql_data(db_conf, sql)

        if len(campaign_info) > 0:
            for (campaign_id, campaign_name) in campaign_info:
                campaign_data = {
                                    'id': campaign_id,
                                    'name': campaign_name,
                                    'batches': [],
                                }
                sql_batch = 'select id, name, quantity '\
                            'from prepaid_card_batch '\
                            'where prepaid_card_campaign_id={0}'\
                            ''.format(campaign_id)
                batch_info = kits.get_mysql_data(db_conf, sql_batch)
                if len(batch_info) > 0:
                    for (batch_id, batch_name, quantity) in batch_info:
                        batch_data = {
                                        'id': batch_id,
                                        'name': batch_name,
                                        'quantity': quantity,
                                     }
                        campaign_data['batches'].append(batch_data)
                data.append(campaign_data)
        return data


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
