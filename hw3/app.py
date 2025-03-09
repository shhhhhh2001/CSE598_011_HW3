import os
import json
import random
import time
from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)

STATIC_FOLDER = os.path.join(os.path.dirname(__file__), 'static')

@app.route('/')
def home():
    file_path = os.path.join(STATIC_FOLDER, 'data/data.json')

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    idx = random.randint(0, len(data) - 1)
    
    context = {
        'idx': idx,
        's1': data[idx]["long_sentence"],
        's2': data[idx]["incorrect_causation_summary"],
    }
    
    return render_template('index.html', **context)


@app.route('/generate_ai_judgement')
def generate_ai_judgement():
    time.sleep(5)  # Simulate AI processing time
    ai_text = "The AI judgment is complete. Here is the result..."
    return jsonify({'ai_judgement': ai_text})


@app.route('/submit', methods=['POST'])
def submit():
    print(request.form)
    return render_template('submit.html')


if __name__ == '__main__':
    app.run(debug=True)
