from flask import Flask, render_template
import maplogic

# configuration
DEBUG = False
SECRET_KEY = 'larry de key'

app = Flask(__name__)
app.config.from_object(__name__)


@app.route('/helloworld')
def helloworld():
    return 'hello, world.'


# 热力图
@app.route('/heatmap')
def show_map():
    points = maplogic.get_shop_info()
    return render_template('heatmap.html', points=points)


# 聚点图
@app.route('/dotmap')
def show_dotmap():
    points = maplogic.get_shop_info()
    return render_template('dotmap.html', points=points)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
