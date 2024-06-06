from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
import requests
import time

app = Flask(__name__)
user_response = None

def wait_for_user_response():
    while True:
        response = requests.get('http://localhost:4000/get_response').json()
        if response['response'] is not None:
            return response['response']
        time.sleep(1)

driver = webdriver.Chrome()
driver.get('https://yandex.ru/maps')

@app.route('/get_coordinates', methods=['POST'])
def get_coordinates():
    data = request.json
    city = data.get('city')
    district = data.get('district')
    address = data.get('address')

    if not city or not address:
        return jsonify({'error': 'Missing city or address'}), 400

    try:
        # Ожидание появления элемента input и замена его значения
        if 'Новая' in address:
            pass
        search_input = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//input[@class='input__control _bold']")))
        action = ActionChains(driver)
        action.click(search_input).key_down(Keys.COMMAND).send_keys('a').key_up(Keys.COMMAND).send_keys(Keys.BACKSPACE).perform()
        full_adress = f"{city} {district} {address}"
        # time.sleep(0.5); 
        search_input.send_keys(full_adress)
        # time.sleep(1); 
        search_input.send_keys(Keys.DOWN)
        # time.sleep(0.5); 
        search_input.send_keys(Keys.ENTER)

        # Ожидание загрузки новой страницы и поиска координат
        coords_div = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "toponym-card-title-view__coords-badge")))
        coords_text = coords_div.text
        coords = coords_text

        return jsonify({'coordinates': coords})
    except Exception as e:
        driver.execute_script("window.open('http://localhost:4000');")
        response = wait_for_user_response()
        if response == 'continue':
            # Ожидание загрузки новой страницы и поиска координат
            coords_div = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "toponym-card-title-view__coords-badge")))
            time.sleep(1); coords_text = coords_div.text
            coords = coords_text
            if coords == []:
                return jsonify({'error': str(e)}), 500
            else: return jsonify({'coordinates': coords})
        else:
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)
