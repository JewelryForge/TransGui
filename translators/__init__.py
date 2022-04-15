import httpcore
import requests.exceptions

from .baidu import BDTrans
from .yd import YDTrans
from googletrans import Translator as GTrans


class Translator:
    all_translators = {'youdao': YDTrans, 'google': GTrans, 'baidu': BDTrans}

    def __init__(self, api='google'):
        if api not in self.all_translators:
            api = 'google'
        self.api = api
        self.trans = self.all_translators[self.api]()

    def translate(self, string):
        status, translation = '', ''
        try:
            if self.api == 'youdao':
                data = self.trans.translate(string, src='en', dest='zh-CHS')
                if data['errorCode'] == '0':
                    translation = data['translation'][0]
                else:
                    status = f"youdao API: unauthorized user"
            elif self.api == 'google':
                data = self.trans.translate(string, src='en', dest='zh-cn')
                translation = data.text if data.src != data.dest else '翻译过于频繁，请等待片刻后重新尝试！'
            elif self.api == 'baidu':
                data = self.trans.translate(string, src='en', dest='zh')
                if 'error_msg' in data:
                    status = f"baidu API: {data['error_msg'].lower()}"
                else:
                    translation = '\n'.join(s['dst'] for s in data['trans_result'])
        except httpcore.NetworkError:
            status = 'network error'
        except httpcore.TimeoutException:
            status = 'time out'
        except requests.exceptions.ProxyError:
            status = 'proxy error'
        return status, translation

    def set_api_keys(self, key1, key2):
        if self.api != 'google':
            self.trans.set_api_keys(key1, key2)
