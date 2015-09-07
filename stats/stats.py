import os
import sys

from flask import Flask, render_template, flash, redirect,\
                  url_for, request, jsonify

import statslogic
from basemarketingtracker import MarketingTracker
from marketingtracker import MobileMarketingTracker,\
                             CampaignMarketingTracker,\
                             WechatMarketingTracker

# configuration
DEBUG = True
SECRET_KEY = 'larry de stats key'

app = Flask(__name__)
app.config.from_object(__name__)


@app.route('/')
def index():
    return render_template('index.html')


# 用户统计
@app.route('/user')
def show_user_stats():
    stats = statslogic.Stats()
    data = stats.analyze('user')
    if 'success' in data.keys() and data['success']:
        return render_template('stats.html', data=data)
    else:
        flash(data['err_message'])
        return redirect(url_for('index'))


# 订单统计
@app.route('/order')
def show_order_stats():
    stats = statslogic.Stats()
    data = stats.analyze('order')
    if 'success' in data.keys() and data['success']:
        return render_template('stats.html', data=data)
    else:
        flash(data['err_message'])
        return redirect(url_for('index'))


# 市场数据追踪
@app.route('/tm', methods=['GET', 'POST'])
def track_marketing():
    yaml_path = os.path.abspath(os.path.dirname(__file__))\
        + '/' + 'conf/marketing.yaml'
    conf_path = os.path.abspath(os.path.dirname(__file__)) \
        + '/conf/stats.conf'
    db_conf_name = 'DB_INFO'

    data = {'title': '查看市场数据'}
    data['tab'] = 'Mobile'
    # 装载下拉列表信息
    try:
        data['campaign_info'] = CampaignMarketingTracker.get_campaigns(
                                    yaml_path,
                                    conf_path,
                                    db_conf_name,
                                    6)
    except:
        err_message = '{0}: {1}'.format(str(sys.exc_info()[0]),
                                        str(sys.exc_info()[1]))
        flash(err_message)

    if request.method == 'POST':
        try:
            req_type = request.args.get('type')
            form_name = 'input_' + req_type
            str_source = request.form[form_name]
            data['tab'] = req_type
            data['source'] = str_source

            yaml_path = os.path.abspath(os.path.dirname(__file__))\
                + '/' + 'conf/marketing.yaml'
            conf_path = os.path.abspath(os.path.dirname(__file__)) \
                + '/conf/stats.conf'

            # building corresponding class object
            classname = req_type + 'MarketingTracker'
            tracker = globals()[classname](yaml_path, conf_path, str_source)
            m_data = tracker.get_marketing_info()
            data.update(m_data)
            if not ('success' in data.keys() and data['success']):
                flash(data['err_message'])
        except:
            err_message = '{0}: {1}'.format(str(sys.exc_info()[0]),
                                            str(sys.exc_info()[1]))
            flash(err_message)

    return render_template('trackmarketing.html', data=data)


# 下载文件
@app.route('/getfile', methods=['GET', 'POST'])
def get_file():
    result = {
                'success': False,
                'message': "test",
                'url':  ''
             }

    quest_scope = request.form['scope']
    quest_type = request.form['type']
    quest_format = request.form['format']
    quest_ids = request.form['ids']

    if not quest_type or\
       not quest_format or\
       not quest_scope or\
       not quest_ids:
        result['message'] = '没有获取到正确的下载请求'
        return jsonify(result)

    yaml_path = os.path.abspath(os.path.dirname(__file__))\
        + '/' + 'conf/marketing.yaml'
    conf_path = os.path.abspath(os.path.dirname(__file__)) \
        + '/conf/stats.conf'
    f_url = MarketingTracker.get_export_data(quest_scope,
                                             quest_type,
                                             quest_format,
                                             quest_ids,
                                             yaml_path,
                                             conf_path)

    if isinstance(f_url, str):
        result['success'] = True
        result['url'] = f_url
    else:
        result['message'] = f_url['message']

    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
