from flask import Flask, render_template, flash, redirect,\
                  url_for, request
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

        tracker = marketinglogic.MarketingTracker()
        if req_type == 'mobiles':
            str_source = tracker.get_mobiles(str_source)

        if len(str_source) == 0:
            flash('未找到任何注册用户')
        else:
            data = tracker.get_marketing_info(str_source, req_type)
            data['tab'] = req_type
            data['title'] = ''
            if 'success' in data.keys() and data['success']:
                data['source'] = str_source
            else:
                flash(data['err_message'])

    return render_template('trackmarketing.html', data=data)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
