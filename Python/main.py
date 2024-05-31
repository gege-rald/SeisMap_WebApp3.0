from flask import Flask, redirect, url_for, render_template
import folium

app = Flask(__name__, template_folder='HTML', static_folder='static') 


@app.route("/")
def index():
    return render_template('index.html')

if __name__ == '__main__':
  app.run(debug=True)