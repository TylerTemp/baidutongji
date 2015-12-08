"""
Usage: baidulocation [options] <date>

Options:
    -u --username=<username>    baidu tongji username (required)
    -p --password=<password>    baidu tongji password (required)
    -s --siteid=<site_id>       baidu tongji siteid (required)

Arguments:
    <date>  format: yyyy-mm-dd
"""
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import datetime
import logging
import json
import time
from bs4 import BeautifulSoup
import os
import tempfile
import subprocess
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

__all__ = ['logger', 'LocationError', 'NotLoginError', 'Location']
__version__ = '0.0.1'

logger = logging.getLogger('baidulocation')


class LocationError(Exception):
    pass


class NotLoginError(LocationError):
    pass


class BaiduTongji(object):
    _session = None
    post_url = 'http://tongji.baidu.com/web/11237910/ajax/post'
    home_url = 'http://tongji.baidu.com/web/11237910/overview/sole'
    regions = [
        {
            "name": "\u5e7f\u4e1c",
            "area": "province,4"
        },
        {
            "name": "\u4e0a\u6d77",
            "area": "province,2"
        },
        {
            "name": "\u6d59\u6c5f",
            "area": "province,32"
        },
        {
            "name": "\u6c5f\u82cf",
            "area": "province,19"
        },
        {
            "name": "\u5176\u4ed6",
            "area": "province,0"
        },
        {
            "name": "\u5c71\u897f",
            "area": "province,26"
        },
        {
            "name": "\u6e56\u5317",
            "area": "province,16"
        },
        {
            "name": "\u5c71\u4e1c",
            "area": "province,25"
        },
        {
            "name": "\u9655\u897f",
            "area": "province,27"
        },
        {
            "name": "\u5317\u4eac",
            "area": "province,1"
        },
        {
            "name": "\u798f\u5efa",
            "area": "province,5"
        },
        {
            "name": "\u6cb3\u5357",
            "area": "province,14"
        },
        {
            "name": "\u5b89\u5fbd",
            "area": "province,9"
        },
        {
            "name": "\u6e56\u5357",
            "area": "province,17"
        },
        {
            "name": "\u6cb3\u5317",
            "area": "province,13"
        },
        {
            "name": "\u5e7f\u897f",
            "area": "province,12"
        },
        {
            "name": "\u6c5f\u897f",
            "area": "province,20"
        },
        {
            "name": "\u56db\u5ddd",
            "area": "province,28"
        },
        {
            "name": "\u8fbd\u5b81",
            "area": "province,21"
        },
        {
            "name": "\u91cd\u5e86",
            "area": "province,33"
        },
        {
            "name": "\u9ed1\u9f99\u6c5f",
            "area": "province,15"
        },
        {
            "name": "\u5409\u6797",
            "area": "province,18"
        },
        {
            "name": "\u5929\u6d25",
            "area": "province,3"
        },
        {
            "name": "\u5185\u8499\u53e4",
            "area": "province,22"
        },
        {
            "name": "\u8d35\u5dde",
            "area": "province,10"
        },
        {
            "name": "\u4e91\u5357",
            "area": "province,31"
        },
        {
            "name": "\u65b0\u7586",
            "area": "province,30"
        },
        {
            "name": "\u53f0\u6e7e",
            "area": "province,35"
        },
        {
            "name": "\u7518\u8083",
            "area": "province,11"
        },
        {
            "name": "\u6d77\u5357",
            "area": "province,8"
        }
    ]

    def __init__(self, username, password, site_id,
                 save_image_file=os.path.join(tempfile.gettempdir(), 'validate.png'),
                 save_code_file=os.path.join(tempfile.gettempdir(), 'validate')):
        self.username = username
        self.password = password
        self.site_id = site_id
        self.img_file = save_image_file
        self.code_file = save_code_file

    def login(self, sleep=1):
        self.pre_login(sleep)
        code = self.get_code(self.img_file, self.code_file)
        logger.debug('code: %s', code)
        while not self.check_code(code):
            time.sleep(sleep)
            self.save_validate_image()
            code = self.get_code(self.img_file, self.code_file)
            logger.debug('code: %s', code)
        return self.do_login(code)

    def pre_login(self, sleep=1):
        logger.debug('new session')
        del self.session

        logger.debug('get home page')
        self.get('http://tongji.baidu.com/web/welcome/login')

        time.sleep(sleep)
        self.save_validate_image()

    def save_validate_image(self):
        logger.debug('save validate code')
        code_resp = self.get(
                'http://cas.baidu.com/',
                params={'action': 'image', 'key': int(time.time())})
        logger.debug('save to %s', self.img_file)
        with open(self.img_file, 'wb') as f:
            f.write(code_resp.content)

    def do_login(self, code):
        logger.debug('do login: %s', code)
        resp_text = self.post('https://cas.baidu.com/',
                              params={'action': 'login'},
                              data=self._get_login_data(code))
        soup = BeautifulSoup(resp_text, 'html5lib')
        red_url = soup.find(
                'meta', {'http-equiv': 'ReFresh'}).attrs.get('content', None)
        if not red_url:
            return False

        for s in red_url.split(';'):
            find_url = s.strip()
            if find_url.startswith('url'):
                logger.debug('find: %s', find_url)
                _, _, url = find_url.partition('=')
                splited_url = urlparse(url.strip())
                if splited_url.netloc == 'cas.baidu.com':
                    logger.debug('login succeed')
                    self.get('http://tongji.baidu.com/web/11237910/overview/sole',
                             params={'siteId': self.site_id})
                    return True

        logger.info('failed to login: %s', red_url)
        return False

    def _get_login_data(self, code):
        return {
            'appscope': [6, 7, 12],
            'appid': '12',
            'entered_login': self.username,
            'entered_password': self.password,
            'entered_imagecode': code,
            'charset': 'utf-8',
            'fromu': 'http://tongji.baidu.com/web/welcome/index',
            'selfu': 'http://tongji.baidu.com/web/welcome/login',
            'senderr': 1
        }

    def get_region(self, date):
        data = self._get_region_data(date)
        content = self.post(self.post_url, data=data)
        return self._parse_result(content)

    def _get_region_data(self, date):
        t = self.js_time(date)
        return {
            'st': t,
            'et': t,
            'st2': '0',
            'et2': '0',
            'indicators': ('pv_count,pv_ratio,visit_count,visitor_count,'
                           'new_visitor_count,new_visitor_ratio,ip_count,'
                           'bounce_ratio,avg_visit_time,avg_visit_pages,'
                           'trans_count,trans_ratio'),
            'method': 'visit/district/a',
            'offset': '0',
            'order': 'ip_count,desc',
            'pageSize': '100',
            'reportId': '16',
            'siteId': self.site_id,
            'viewType': 'city'}

    def get_city(self, region, date):
        logger.debug(region)
        if region[-1].isdigit():
            area = region
        else:
            # name to area
            area = self._get_region_area(region)

        data = self._get_city_data(area, date)
        content = self.post(self.post_url, data=data)
        return self._parse_result(content, area)

    def _get_city_data(self, area, date):
        t = self.js_time(date)
        return {
            'area': area,
            'st': t,
            'et': t,
            'st2': '0',
            'et2': '0',
            'indicators': ('pv_count,pv_ratio,visit_count,visitor_count,'
                           'new_visitor_count,new_visitor_ratio,ip_count,'
                           'bounce_ratio,avg_visit_time,avg_visit_pages,'
                           'trans_count,trans_ratio'),
            'method': 'visit/district/top',
            'offset': '0',
            'order': 'ip_count,desc',
            'reportId': '16',
            'siteId': self.site_id,
            'viewType': 'city'}

    def _parse_result(self, result, area=None):
        obj = json.loads(result)
        if obj['status'] != 0:
            logger.warning('region result(%s): %s', obj['status'], obj['msg'])
            logger.debug(obj)
        data = obj['data']
        fields = data['fields'][1:]
        items = data['items']
        places = []
        # del self.regions[:]
        for each in items[0]:
            each = each[0]
            # self.regions.append(dict(each))
            name = each.pop('name')
            if 'cityId' in each:
                if each['cityId'] == 0:
                    each['city'] = name
                    each['region'] = self._get_region_name(area)
                else:
                    each['region'] = self._get_region_name(each['area'])
                    each['city'] = name
            else:
                each['region'] = name
                each['city'] = None
            places.append(each)

        for place, each_num_results in zip(places, items[1]):
            for field, value in zip(fields, each_num_results):
                if value == '--':
                    value = None
                elif field != 'pv_ratio' and field.endswith('ratio'):
                    if value > 0 and value < 1:
                        logger.warning('%s: %s', field, value)
                    value /= 100.0
                place[field] = value

        total = data['sum'][0]
        total_result = dict(zip(fields, total))
        total_result['city'] = 'sum'
        if area:
            total_result['region'] = self._get_region_name(area)
        else:
            total_result['region'] = 'sum'
        places.append(total_result)
        return places

    def _get_region_name(self, region):
        if not hasattr(self, '_region_to_name'):
            self._region_to_name = {}
            for each in self.regions:
                area = each['area']
                name = each['name']
                self._region_to_name[area] = name

        return self._region_to_name[region]

    def _get_region_area(self, name):
        if not hasattr(self, '_region_to_area'):
            if hasattr(self, '_region_to_name'):
                self._region_to_area = {
                    v: k for k, v in self._region_to_name.items()}
            else:
                self._region_to_area = {
                    e['name']: e['area'] for e in self.regions
                }

        return self._region_to_area[name]

    def get_preview(self):
        response = self.get(self.home_url,
                            {'siteId': self.site_id}, allow_redirects=False)
        if response.status_code == 302:
            raise NotLoginError('Not Logged in')

        content = response.text
        soup = BeautifulSoup(content, "html5lib")
        js = soup.find_all('script')[9]
        raw_text = js.text.strip()
        js_text = raw_text[raw_text.find('T.config,') + 9:-2]
        result = json.loads(js_text)
        target_data = result['outline']

        titles = target_data['fields'][1:]
        datas = target_data['items']

        result = {}
        for index, main_title in enumerate(
                ('today', 'yesterday', 'forecase_today', 'yesterday_now',
                 'everyday_avg')):
            this_result = datas[index][1:]
            for this_index, val in enumerate(this_result):
                if main_title == 'forecase_today':
                    if val['val'] == '--':
                        val['val'] = None
                else:
                    if val == '--':
                        this_result[this_index] = None
            logger.debug(main_title)
            logger.debug(titles)
            logger.debug(this_result)
            result[main_title] = dict(zip(titles, this_result))

        return result

 #        {'fields': ['null',
 #            'pv_count',
 #            'visitor_count',
 #            'ip_count',
 #            'bounce_ratio',
 #            'avg_visit_time',
 #            'trans_count'],
 # 'items': [['今日', 17018, 1097, 504, 21.12, 506, '--'],
 #           ['昨日', 26488, 1740, 745, 15.51, 423, '--'],
 #           ['预计今日',
 #            {'flag': 1, 'val': 35179},
 #            {'flag': 1, 'val': 2572},
 #            {'flag': 1, 'val': 839},
 #            {'flag': 0, 'val': '--'},
 #            {'flag': 0, 'val': '--'},
 #            {'flag': 0, 'val': '--'}],
 #           ['昨日此时', 12413, 719, 434, 22.85, 569, '--'],
 #           ['每日平均', 56819, 2330, 1142, 20, 591, '--'],
 #           ['历史峰值',
 #            {'date': '2015年11月24日', 'show': 1, 'val': 144424},
 #            {'date': '2015年11月04日', 'show': 1, 'val': 4506},
 #            {'date': '2015年11月20日', 'show': 1, 'val': 1722},
 #            {'date': '2015年11月21日', 'show': 0, 'val': 39.26},
 #            {'date': '2015年11月24日', 'show': 0, 'val': 1235},
 #            '--']]}

    def get(self, url, params=None, verify=False, **kwargs):
        return self.session.get(url, params=params, verify=verify, **kwargs)

    def post(self, url, data=None, json=None,
             allow_redirects=False, verify=False, **kwargs):
        resp = self.session.post(url, data=data, json=json,
                                 allow_redirects=allow_redirects,
                                 verify=verify, **kwargs)

        if resp.status_code == 302 and 'Location' in resp.headers:
            location = resp.headers['Location']
            parsed = urlparse(location)
            if parsed.netloc == 'cas.baidu.com':
                raise NotLoginError('Login expired')

        return resp.text

    def has_city_regions(self):
        # Shanghai, Other, Beijing, Tianjing,
        not_have = ('province,2', 'province,0', 'province,3', 'province,33')
        for each in self.regions:
            area = each['area']
            if area in not_have:
                continue
            yield area

    def logout(self):
        del self.session

    @staticmethod
    def js_time(date):
        d = datetime.datetime(year=date.year, month=date.month, day=date.day)
        return int(d.timestamp() * 1000)

    @staticmethod
    def get_code(img_file, out_prefix):
        sp = subprocess.Popen(['tesseract', img_file, out_prefix],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
        out, err = sp.communicate()
        logger.debug('%s / %s', out, err)
        if sp.returncode != 0:
            return ''

        with open(out_prefix + '.txt', 'r', encoding='utf-8') as f:
            return f.read().strip()

    @staticmethod
    def check_code(code):
        if len(code) != 4:
            return False
        if len(set(code).intersection(('ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                                       'abcdefghijklmnopqrstuvwxyz'
                                       '0123456789'))) != 4:
            return False
        return True

    @property
    def session(self):
        if self._session is None:
            self._session = requests.Session()
        return self._session

    @session.deleter
    def session(self):
        self._session = None


if __name__ == '__main__':
    from bashlog import stdoutlogger, DEBUG
    from pprint import pprint
    from docpie import docpie
    import sys

    args = docpie(__doc__)
    stdoutlogger(logger, DEBUG)
    logger.setLevel(logging.DEBUG)
    hdlr = logging.StreamHandler(sys.stdout)
    hdlr.setFormatter(logging.Formatter())

    username = args['--username']
    password = args['--password']
    site_id = args['--siteid']
    # assert username and password and site_id, __doc__
    l = Location(username=username, password=password, site_id=site_id)

    logged = False
    while not logged:
        l.pre_login()
        code = input('please input code in file %s: ' % l.img_file)
        logged = l.do_login(code)
    # while not l.login():
    #     print('retry...')
    pprint(l.get_preview())
    year, month, day = args['<date>'].split('-')
    d = datetime.date(year=int(year), month=int(month), day=int(day))
    r = l.get_region(d)
    for each in r:
        if each['city'] == 'sum':
            print(each['region'], each['city'])

    for each in l.has_city_regions():
        r = l.get_city(each, d)
        for each in r:
            if each['city'] == 'sum':
                print(each['region'], each['city'])