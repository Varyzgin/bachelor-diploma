from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
response = None

# Рендерим страницу с кнопками
@app.route('/')
def home():
    return render_template('index.html')

# Обработка кнопки "Исправлено"
@app.route('/continue', methods=['POST'])
def continue_process():
    global response
    response = 'continue'
    return jsonify({'status': 'continue'})

# Обработка кнопки "Невозможно исправить"
@app.route('/abort', methods=['POST'])
def abort_process():
    global response
    response = 'abort'
    return jsonify({'status': 'abort'})

# сюда долбится плагин Яндекс карт, пытающийся получить результат
@app.route('/get_response', methods=['GET'])
def get_response():
    global response
    tmp = response
    response = None  # Reset user_response after reading
    return jsonify({'response': tmp})

if __name__ == '__main__':
    app.run(port=4000)