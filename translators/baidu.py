# -*- coding: utf-8 -*-

# This code shows an example of text translation from English to Simplified-Chinese.
# This code runs on Python 2.7.x and Python 3.x.
# You may install `requests` to run this code: pip install requests
# Please refer to `https://api.fanyi.baidu.com/doc/21` for complete api document

import requests
import random
from hashlib import md5


class BDTrans:
    # Set your own appid/appkey.

    def __init__(self):
        self.appid = ''
        self.appkey = ''

    # For list of language codes, please refer to `https://api.fanyi.baidu.com/doc/21`
    def translate(self, query, src='en', dest='zh'):
        endpoint = 'http://api.fanyi.baidu.com'
        path = '/api/trans/vip/translate'
        url = endpoint + path

        # Generate salt and sign
        def make_md5(s, encoding='utf-8'):
            return md5(s.encode(encoding)).hexdigest()

        salt = random.randint(32768, 65536)
        sign = make_md5(self.appid + query + str(salt) + self.appkey)

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {'appid': self.appid, 'q': query, 'from': src, 'to': dest, 'salt': salt, 'sign': sign}
        r = requests.post(url, params=payload, headers=headers)
        return r.json()

    def set_api_keys(self, key1, key2):
        self.appid = key1
        self.appkey = key2


if __name__ == '__main__':
    t = BDTrans()
    r = t.translate('WBC')
    print(r)
