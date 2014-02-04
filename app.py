import os
import random
import sys
import time
import pymongo
import requests
from selenium import webdriver
from flask import Flask, jsonify, redirect, request
app = Flask(__name__)
app.debug = True

db = pymongo.Connection(os.getenv('MONGOLAB_URI')).get_default_database()

__email_chars = 'abcdefghijklmnopqrstuvwxyz1234567890'


def __random():
    res = ''
    while len(res) < 10:
        res += random.choice(__email_chars)
    return res


def __webdriver():
    if '--firefox' in sys.argv:
        return webdriver.Firefox()
    elif '--macphantom' in sys.argv:
        return webdriver.PhantomJS('phantomjs/bin/phantomjs')
    else:
        return webdriver.PhantomJS('phantomjs-1.9.7-linux-x86_64/bin/phantomjs')

    # helps avoid element visibility errors by setting a realistic size
    driver.set_window_size(1028, 768)


def signup(driver, url, params):
    driver.get('https://events.developerforce.com/signup')
    time.sleep(1)
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

    # TODO assert that we see the thanks page with status code 200


@app.route("/")  # TODO set to post
def hello():
    request_time = time.time()
    rand = __random()
    driver = __webdriver()
    vals = {
        'email': 'salesforce-dev-org@bulkify.com',
        'username': '%s@bulkify.com' % rand,
        'first_name': 'developer',
        'last_name': 'developer',
        'company': 'developer',
        'postal_code': '02144',
    }
    try:
        signup(driver, 'https://events.developerforce.com/signup', vals)
    except Exception as e:
        vals.update({'exception': repr(e)})

    vals.update({'headers': dict(request.headers.items())})
    vals.update({'id': rand})
    vals.update({'request_time': request_time})
    db['account'].save(vals)

    driver.quit()

    return redirect('/account/%s' % rand)


@app.route('/callback')
def callback():
    db['email'].save(request.json)
    return jsonify({'status': 'ok'})


@app.route('/account/<id>')
def finish(id):
    result = {
        'id': id,
        'status': 'awaiting_activation_email',
        'details': db['account'].find_one({'id': id})
    }
    # can't url json mongo id
    del result['details']['_id']

    return jsonify(result)




if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')