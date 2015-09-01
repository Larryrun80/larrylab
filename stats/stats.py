from flask import Flask, render_template, flash, redirect,\
                  url_for, request, send_file, jsonify

import statslogic
import marketinglogic

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
def track_marketing_via_mobile():
    data = {'title': '查看市场数据'}
    data['tab'] = 'mobiles'
    if request.method == 'POST':
        req_type = request.args.get('type')
        form_name = 'input_' + req_type
        str_source = request.form[form_name]
        data['tab'] = req_type
        data['source'] = str_source

        tracker = marketinglogic.MarketingTracker()
        if req_type == 'mobiles':
            str_source = tracker.get_mobiles(str_source)

        if len(str_source) == 0:
            flash('未找到任何注册用户')
        else:
            m_data = tracker.get_marketing_info(str_source, req_type)
            data.update(m_data)
            if not ('success' in data.keys() and data['success']):
                flash(data['err_message'])

    flash(data)
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

    tracker = marketinglogic.MarketingTracker()
    file_url = tracker.get_export_data(quest_scope,
                                       quest_type,
                                       quest_format,
                                       quest_ids)

    if isinstance(file_url, str):
        result['success'] = True
        result['url'] = file_url
    else:
        result['message'] = file_url['message']

    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
