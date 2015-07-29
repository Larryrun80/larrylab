#!/usr/bin/env python
# Filename: maplogic.py

from configparser import ConfigParser
import os
import sys
import time
import mysql.connector


# Defining method to unify format of output info
def print_log(log_text):
    log_prefix = '[{0}]'.format(time.strftime('%Y-%m-%d %H:%M:%S'))
    print(('{0} {1}').format(log_prefix, log_text))


def get_db_config():
    CONFIG_FILE = os.path.abspath(os.path.dirname(__file__)) \
              + '/conf/maps.conf'
    try:
        config = ConfigParser()
        if not os.path.exists(CONFIG_FILE):
            print_log('Config file not found at: {0}, exit'
                      .format(os.path.abspath(CONFIG_FILE)))
            sys.exit()
        config.read(CONFIG_FILE)

        if config.has_section('DB_INFO'):
            db_info = {
                        'host': config.get('DB_INFO', 'Host'),
                        'user': config.get('DB_INFO', 'User'),
                        'password': config.get('DB_INFO', 'Password'),
                        'database': config.get('DB_INFO', 'Database'),
                        'port': config.get('DB_INFO', 'Port'),
                      }
            return db_info
        else:
            print_log('Config section DB_INFO found in {0}, exit'
                      .format(os.path.abspath(CONFIG_FILE)))
            sys.exit()
    except SystemExit:
        print_log('error found, process terminated')
    except:
        print_log('{0}: {1}'.format(str(sys.exc_info()[0]),
                                    str(sys.exc_info()[1])))


def get_shop_info():
    db_info = get_db_config()
    cnx = mysql.connector.connect(
            user=db_info["user"],
            password=db_info["password"],
            host=db_info["host"],
            database=db_info["database"],
            port=db_info["port"],
            connection_timeout=600,
            buffered=True
            )

    sql_str = '''
            SELECT  b.`id`,
                    sum(cb.`stock`),
                    b.`lat`,
                    b.`lng`,
                    z.`name`
             FROM   campaign_branch cb
        LEFT JOIN   campaignbranch_has_branches cbb
               ON   cb.`id`=cbb.`campaignbranch_id`
        LEFT JOIN   branch b
               ON   b.`id`=cbb.`branch_id`
        LEFT JOIN   zone z
               ON   z.`id`=b.`zone_id`
            WHERE   cb.`start_time`<now()
              AND   cb.`end_time`>now()
              AND   cb.`enabled`=1
              AND   cb.type<3
         GROUP BY   b.id
    '''
    cursor = cnx.cursor()
    cursor.execute(sql_str)
    shops = cursor.fetchall()

    branches_info = []
    for (brancd_id, stock, lat, lng, city) in shops:
        branches_info.append({"lng": lng, "lat": lat, "count": int(stock)})
    cnx.close()
    return branches_info
