import random
import sys
import time
from selenium import webdriver
from flask import Flask, jsonify
app = Flask(__name__)


__email_chars = 'abcdefghijklmnopqrstuvwxyz1234567890'


def __random_email():
    res = ''
    while len(res) < 10:
        res += random.choice(__email_chars)
    return 'dev-%s@ccp0.com' % res


def __webdriver():
    if '--firefox' in sys.argv:
        return webdriver.Firefox()
    else:
        return webdriver.PhantomJS('phantomjs/bin/phantomjs')

    # helps avoid element visibility errors by setting a realistic size
    driver.set_window_size(1028, 768)


@app.route("/")
def hello():
    email = __random_email()
    driver = __webdriver()

    driver.get('https://events.developerforce.com/signup')
    time.sleep(2)

    vals = {
        'email': email,
        'username': email,
        'first_name': 'developer',
        'last_name': 'developer',
        'company': 'developer',
        'postal_code': '02144',
    }
    for k, v in vals.items():
        f = driver.find_element_by_id(k)
        if f and f.is_displayed() and f.is_enabled():
            f.send_keys(v)

    country_field = driver.find_element_by_id('country')
    for o in country_field.find_elements_by_tag_name('option'):
        if o.get_attribute('value').lower() == 'us':
            o.click()
            break
    driver.find_element_by_id('eula').click()
    # driver.find_element_by_id('submit_btn').click()

    # TODO wait for email and set password
    

    driver.close()

    return jsonify({
        'email': email
    })

if __name__ == "__main__":
    app.run(debug=True)