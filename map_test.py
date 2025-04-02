from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')  # Φορτώνει το kalts.html

@app.route('/get_map')
def get_map():
    with open("AOI1_map.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return jsonify({"map_html": html_content})

if __name__ == '__main__':
    app.run(debug=True, port=5020)
