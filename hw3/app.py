import os
import json
import random
import time
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
# from pyngrok import ngrok
# from transformers import pipeline

# pipe = pipeline("text-generation", model="Qwen/Qwen2.5-1.5B-Instruct", max_new_tokens=256)

app = Flask(__name__)
# CORS(app)

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


@app.route('/generate_ai_judgement', methods=['POST'])
def generate_ai_judgement():
    data = request.get_json()  # Get JSON data from request
    sentence1 = data.get('sentence1', '')
    sentence2 = data.get('sentence2', '')
    
    if sentence1 == '' or sentence2 == '':
        return jsonify({'ai_judgement': 'Error! Refresh the page and try again.'})

    # Simulate AI processing time
    # time.sleep(3)

    # Dummy AI processing logic
    # ai_text = f"AI Judgement based on:\nSentence 1: {sentence1}\nSentence 2: {sentence2}"
    ai_text = gen(sentence1, sentence2)

    return jsonify({'ai_judgement': ai_text})


@app.route('/submit', methods=['POST'])
def submit():
    print(request.form)
    return render_template('submit.html')


def gen(s1, s2):
    messages = [
        {"role": "user",
        "content": f"""
        I will give you 2 sentences. Judge whether the causation is the same.
        Give short explanation first and then indicate whether the causation is the same.
        In explanation, simply point out what causes what for each sentence. Using => to indicate causation.
        If the causation is different, generate a correct summary of sentence 1.

        For example:
        Sentence 1: Because the road was icy and the driver was speeding, the car skidded off the highway and crashed into a tree, causing significant damage to the front bumper and injuring the driver.
        Sentence 2: The car crashed into a tree, which made the road icy and caused the driver to speed.

        Output:
        Sentence 1: Icy road and speeding => car crash.
        Sentence 2: Car crash => icy road and speeding.
        The causation is different.
        Correct summary of sentence 1: Icy road and speeding caused car crash.


        Here is your task:
        Sentence 1: {s1}
        Sentence 2: {s2}

        Output:
        """},
    ]
    
    return f"AI Judgement based on:\nSentence 1: {s1}\nSentence 2: {s2}"
    # out = pipe(messages)
    # return out[0]["generated_text"][-1]['content']


if __name__ == '__main__':
    # public_url = ngrok.connect(5000).public_url
    # print(f"Public URL: {public_url}")

    # Start the Flask app
    app.run(port=5000)
