import time
import gc
import ujson
import urequests


class ubot:
    
    def __init__(self, token):
        self.url = 'https://api.telegram.org/bot' + token
        self.commands = {}
        self.default_handler = None
        self.message_offset = 0
        self.sleep_btw_updates = 3
        self.read_old_messages()
        #print('offset: ',self.message_offset)
        

    def read_old_messages(self):
        messages = self.read_messages(limit=100)
        if messages:
            for message in messages:
                #print('old id: ', message['update_id'])
                if message['update_id'] > self.message_offset:
                    self.message_offset = message['update_id'] + 1
                    self.read_old_messages()

    def send(self, chat_id, text):
        data = {'chat_id': chat_id, 'text': text}
        try:
            headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
            response = urequests.post(self.url + '/sendMessage', json=data, headers=headers)
            response.close()
            return True
        except:
            return False

    def read_messages(self, limit=1):
        result = []
        self.query_updates = {
            'offset': self.message_offset,
            'limit': limit,
            'timeout': 30,
            'allowed_updates': ['message']}

        try:
            update_messages = urequests.post(self.url + '/getUpdates', json=self.query_updates).json() 
            if 'result' in update_messages:
                for item in update_messages['result']:
                    if 'text' in item['message']:
                        result.append(item)
            update_messages.close()
            return result
        except:
            return None

    def listen(self):
        while True:
            self.read_once()
            time.sleep(self.sleep_btw_updates)
            gc.collect()

    def read_once(self):
        #print('reading once, cur offset: ', self.message_offset)
        messages = self.read_messages()
        if messages:
            for message in messages:
                #print('got new msg: ', message)
                if message['update_id'] >= self.message_offset:
                    self.message_handler(message)
                    self.message_offset = message['update_id'] + 1
    
    def register(self, command, handler):
        self.commands[command] = handler

    def set_default_handler(self, handler):
        self.default_handler = handler

    def set_sleep_btw_updates(self, sleep_time):
        self.sleep_btw_updates = sleep_time

    def message_handler(self, message):
        parts = message['message']['text'].split(' ')
        #print('handle msg:')
        if parts[0] in self.commands:
            #print('exec command: ', parts[0])
            self.commands[parts[0]](message)
        else:
            #print('exec default command')
            if self.default_handler:
                self.default_handler(message)
