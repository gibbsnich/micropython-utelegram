
from config import utelegram_config
from config import wifi_config
from config import github_config

import utelegram
import network
#import utime
#import ujson
import urequests
import ntptime 
import time as _time
import base64

def wlan_connect(ssid, password):
    import network
    wlan = network.WLAN(network.STA_IF)
    if not wlan.active() or not wlan.isconnected():
        wlan.active(True)
        print('connecting to:', ssid)
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())

def padstr(num):
    t = str(num)
    if num < 10: t = '0' + t
    return t

def get_timestr():
    t = _time.time()
    y, m, d, hh, mm, ss, weekday, jday = _time.localtime(t)
    return str(y) + '-' + padstr(m) + '-' + padstr(d), padstr(hh) + ':' + padstr(mm)


# sta_if = network.WLAN(network.STA_IF)
# sta_if.active(True)
# sta_if.scan()
# sta_if.connect(wifi_config['ssid'], wifi_config['password'])

# if debug: print('WAITING FOR NETWORK - sleep 20')
# utime.sleep(20)

def get_message(message):
    print(message)
    #bot.send(message['message']['chat']['id'], message['message']['text'].upper())
    bot.send(message['message']['chat']['id'], 'unknown command: "' + message['message']['text'] + "'")

def reply_ping(message):
    print(message)
    bot.send(message['message']['chat']['id'], 'pong')

def reply_btc(message):
    import re
    import urequests
    print(message)
    btc_body = urequests.get('https://bitcoin.de')
    print(btc_body.content)
    btc_re = re.compile('id="ticker_price".*?>([^<]+)')
    m = btc_re.match(btc_body.content)
    btc_body.close()
    bot.send(message['message']['chat']['id'], m.group())

def store_github(message):
    print(message)
    cmd_index = message['message']['text'].index(' ')
    text = message['message']['text'][(cmd_index+1):]
    today_str, time_str = get_timestr()
    #from datetime import datetime
    #today_str = datetime.today().strftime('%Y-%m-%d')
    
    todays_path = 'daily_notes/' + today_str + '.md'
    #todays_path = 'daily_notes/demo.txt'
    print('storing: ' + text + ', @' + todays_path)
    
    headers = {
        'User-Agent': 'esp32-github-bot',
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': 'token ' + github_config['token']
    }
    contents_path = github_config['api'] + '/repos/' + github_config['owner'] + '/' + github_config['repo'] + '/contents/' + todays_path
    print('remote path: ' + contents_path)
    resp_exists = urequests.get(contents_path, headers=headers)

    new_content = None
    old_sha = None
    print('status_code: ' + str(resp_exists.status_code))
    if resp_exists.status_code > 400: #create new
        new_content = base64.b64encode(bytes(time_str + '\r\n' + text, 'utf-8'))
    else: #update existing
        resp_json = resp_exists.json() 
        if 'type' in resp_json:
            if resp_json['type'] != 'file':
                raise ValueError('Not a file @' + github_config['owner'] + '/' + github_config['repo'] + '/' + todays_path)
        else:
            raise ValueError('Unexpected value: ' + resp_json)
        if 'content' in resp_json:
            new_content = base64.b64decode(resp_json['content']) + '\r\n\r\n' + time_str + '\r\n' + text
            print("new content: " + str(new_content))
            new_content = base64.b64encode(bytes(new_content, 'utf-8'))
        else:
            raise ValueError('Missing content: ' + resp_json)
        if 'sha' in resp_json:
            old_sha = resp_json['sha']
        else:
            raise ValueError('Missing old SHA! ' + resp_json) 
    resp_exists.close()
    query_updates = {
        'message': 'Added "' + text + '"',
        'content': new_content
    }
    if old_sha is not None:
        query_updates['sha'] = old_sha
    resp_put = urequests.put(contents_path, json=query_updates, headers=headers).json()
    print(resp_put)
    #print(resp_put.content)
    commit_url = resp_put['commit']['html_url']
    print("commited to: " + commit_url)
    #return 'OK'
    bot.send(message['message']['chat']['id'], commit_url)

wlan_connect(ssid=wifi_config['ssid'], password=wifi_config['password'])
ntptime.settime()

debug = True

#if debug:
#    test_msg = {
#        'message': {
#            'text': '/put https://github.com\r\nhello world'
#        }
#    }
#    store_github(test_msg)
#else:

#if sta_if.isconnected():
bot = utelegram.ubot(utelegram_config['token'])
#bot.register('/ping', reply_ping)
bot.register('/btc', reply_btc)
bot.register('/put', store_github)
bot.set_default_handler(get_message)

print('BOT LISTENING')
bot.listen()
#else:
#    print('NOT CONNECTED - aborting')
