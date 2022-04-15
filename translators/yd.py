import sys
import uuid
import requests
import hashlib
from importlib import reload
import json
import time

reload(sys)


class YDTrans:
    YOUDAO_URL = 'https://openapi.youdao.com/api'
    def __init__(self) -> None:
        self.APP_KEY = ''
        self.APP_SECRET = ''

    def set_api_keys(self, key1, key2):
        self.APP_KEY = key1
        self.APP_SECRET = key2

    def encrypt(self, signStr):
        hash_algorithm = hashlib.sha256()
        hash_algorithm.update(signStr.encode('utf-8'))
        return hash_algorithm.hexdigest()

    def truncate(self, text):
        if text is None:
            return None
        size = len(text)
        return text if size <= 20 else text[0:10] + str(size) + text[size - 10:size]

    def do_request(self, data):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        return requests.post(self.YOUDAO_URL, data=data, headers=headers)

    def translate(self, q, src='en', dest='zh-CHS'):
        curtime = str(int(time.time()))
        salt = str(uuid.uuid1())
        sign_str = self.APP_KEY + self.truncate(q) + salt + curtime + self.APP_SECRET
        sign = self.encrypt(sign_str)
        data = {'from': src, 'to': dest, 'signType': 'v3', 'curtime': curtime, 'appKey': self.APP_KEY, 'q': q,
                'salt': salt, 'sign': sign, 'vocabId': "FF05510A2BE1426E86D62EFAD4D30EDD"}

        response = self.do_request(data)
        content_type = response.headers['Content-Type']
        # if content_type == "audio/mp3":
        #     millis = int(round(time.time() * 1000))
        #     filePath = "合成的音频存储路径" + str(millis) + ".mp3"
        #     fo = open(filePath, 'wb')
        #     fo.write(response.content)
        #     fo.close()
        # else:
        return json.loads(response.content)
        # trans = json.loads(response.content)['translation'][0]
        # return trans.split('\n')


if __name__ == '__main__':
    t = YDTrans()
    s = t.translate(
        '''
        KinWBC.
    We first formulate a kinematic wholebody controller to obtain joint commands given operational space commands.
    The basic idea is to compute incremental joint positions based on operational space position errors and add them to the current joint positions.
    This is done using null-space task prioritization, as follows:
    '''
    )
    print(s)
