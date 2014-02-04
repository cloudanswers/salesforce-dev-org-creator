import json
import os
import random
import re
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


def signup(driver, url, vals):
    driver.get(url)
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


@app.route('/callback', methods=['POST'])
def callback():
    # mandrill webhook format:
    # http://help.mandrill.com/entries/22092308-What-is-the-format-of-inbound-email-webhooks-

    if request.form.get('mandrill_events'):
        for event in json.loads(request.form.get('mandrill_events')):
            db['email'].save(event)
    return jsonify({'status': 'ok'})


def __expect_text_on_page(driver, text):
    if text not in driver.page_source:
        e = Exception('not expected page ("' + text + '" not found): %s'
                      % driver.page_source)
        driver.quit()
        raise e


def __activate(msg, password):
    search_result = re.search(r'Click (?P<url>.+) to log in now.', msg['text'])
    if search_result:
        url = search_result.group('url')
        driver = __webdriver()
        driver.get(search_result.group('url'))

        if 'Your login attempt has failed' in driver.page_source:
            driver.quit()
            raise Exception('activation link already used')

        # TODO assert we're on the password reset page

        driver.find_element_by_id('p5').send_keys(password[:-1])
        driver.find_element_by_id('p6').send_keys(password[:-1])
        for o in driver.find_element_by_id('p2').find_elements_by_tag_name('option'):
            # pet name
            if o.get_attribute('value') == '3':
                o.click()
                break
        driver.find_element_by_id('p3').send_keys('none')
        driver.find_element_by_name('save').click()

        __expect_text_on_page(driver, 'Force.com Home')

        # expand navs to avoid ElementNotVisibleException
        driver.find_element_by_id('setupNavExpandAll').click()

        driver.find_element_by_id('ManageUsers_font').click()

        __expect_text_on_page(driver, 'System Administrator')

        for e in driver.find_elements_by_tag_name('a'):
            if e.get_attribute('href') and e.get_attribute('href').startswith('/00e'):
                e.click()
                break

        __expect_text_on_page(driver, 'Login IP Ranges')

        driver.find_element_by_name('newIP').click()

        __expect_text_on_page(driver, 'Please specify IP range')

        driver.find_element_by_id('IpStartAddress').send_keys('0.0.0.0')
        driver.find_element_by_id('IpEndAddress').send_keys('255.255.255.255')
        driver.find_element_by_name('save').click()

        # should be returned to profile
        __expect_text_on_page(driver, 'Profile Detail')

        # driver.quit()

@app.route('/account/<id>')
def finish(id):
    result = {
        'id': id,
        'status': 'awaiting_activation_email',
        'details': db['account'].find_one({'id': id})
    }

    result['emails'] = []
    for e in db['email'].find({'msg.text': {'$regex': '.*%s.*' % id}}):
        # neutralize ObjectID serialization problem
        del e['_id']
        result['emails'].append(e)

        if 'Salesforce.com login confirmation' == e['msg']['subject']:
            if not result['details'].get('activation_status') or True:
                result['details']['activation_status'] = 'in_progress'
                db['account'].save(result['details'])
                try:
                    __activate(e['msg'], id)
                except Exception as e:
                    result['details']['activation'] = 'error: %s' % repr(e)
                    db['account'].save(result['details'])
                result['details']['activation_status'] = 'complete'
                db['account'].save(result['details'])

    # neutralize mongo ObjectID json serialization error
    del result['details']['_id']

    return jsonify(result)




if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')