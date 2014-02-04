import random
import sys
import time
from selenium import webdriver
from flask import Flask, jsonify, redirect
app = Flask(__name__)
app.debug = True


__email_chars = 'abcdefghijklmnopqrstuvwxyz1234567890'


def __random():
    res = ''
    while len(res) < 10:
        res += random.choice(__email_chars)
    return res


def __email(id):
    return 'salesforce-dev-org+%s@bulkify.com' % id

def __webdriver():
    if '--firefox' in sys.argv:
        return webdriver.Firefox()
    elif '--macphantom' in sys.argv:
        return webdriver.PhantomJS('phantomjs/bin/phantomjs')
    else:
        return webdriver.PhantomJS('phantomjs-1.9.7-linux-x86_64/bin/phantomjs')

    # helps avoid element visibility errors by setting a realistic size
    driver.set_window_size(1028, 768)


@app.route("/")  # TODO set to post
def hello():
    rand = __random()
    email = __email(rand)
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
    driver.find_element_by_id('submit_btn').click()

    # TODO wait for email and set password
    
    driver.close()

    return jsonify({'email': email})


@app.route('/callback')
def callback():
    return jsonify({'status': 'ok'})


@app.route('/account/<rand>')
def finish(rand):
    pass




if __name__ == "__main__":
    app.run(debug=True)