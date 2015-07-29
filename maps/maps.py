from flask import Flask, render_template, request
import maplogic

# configuration
DEBUG = True
SECRET_KEY = 'larry de key'

app = Flask(__name__)
app.config.from_object(__name__)


@app.route('/helloworld')
def helloworld():
    return 'hello, world.'


# 热力图
@app.route('/itemdist')
def show_item_distribution():
    points = maplogic.get_shop_info()
    mode = request.args.get('mode')
    if mode == 'heat':
        return render_template('heatmap.html', points=points)
    else:
        return render_template('dotmap.html', points=points)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
