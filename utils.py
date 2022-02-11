# -*- coding: utf-8 -*-
# 工具类集合
# from asyncio.windows_events import NULL
import sys
import json
import uuid
import yaml
import time
import urllib3
import requests
# from tkinter import E
from encrypt import *
from urllib.parse import urlparse
from email.utils import formatdate
from datetime import datetime, timedelta, timezone
urllib3.disable_warnings()

# 读取yml配置
def getYmlConfig(yaml_file='config.yml'):
    file = open(yaml_file, 'r', encoding="utf-8")
    file_data = file.read()
    file.close()
    config = yaml.load(file_data, Loader=yaml.FullLoader)
    return dict(config)

# 输出调试信息，并及时刷新缓冲区
def log(content):
    print(getTimeStr() + ' ' + str(content))
    sys.stdout.flush()

# 获取当前utc时间，并格式化为北京时间
def getTimeStr():
    utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
    bj_dt = utc_dt.astimezone(timezone(timedelta(hours=8)))
    return bj_dt.strftime("%Y-%m-%d %H:%M:%S")

# 将cookieStr转换为字典
def cookieStrToDict(cookieStr):
    cookies = {}
    for line in cookieStr.split(';'):
        name, value = line.strip().split('=', 1)
        cookies[name] = value
    return cookies


# 获取当前的GMT格式时间
def getNowGMTTIme():
    dt = formatdate(None, usegmt=True)
    return dt

# 获取今日校园api
def getCpdailyApis(user, debug=False):
    apis = {}
    schools = requests.get(url='https://mobile.campushoy.com/v6/config/guest/tenant/list', verify=False).json()['data']
    flag = True
    for one in schools:
        if one['name'] == user['school']:
            if one['joinType'] == 'NONE':
                log(user['school'] + ' 未加入今日校园')
                exit(-1)
            flag = False
            params = {
                'ids': one['id']
            }
            apis['tenantId'] = one['id']
            res = requests.get(url='https://mobile.campushoy.com/v6/config/guest/tenant/info', params=params,
                               verify=False)
            data = res.json()['data'][0]
            joinType = data['joinType']
            idsUrl = data['idsUrl']
            ampUrl = data['ampUrl']
            ampUrl2 = data['ampUrl2']
            if 'campusphere' in ampUrl or 'cpdaily' in ampUrl:
                parse = urlparse(ampUrl)
                host = parse.netloc
                apis[
                    'login-url'] = idsUrl + '/login?service=' + parse.scheme + r"%3A%2F%2F" + host + r'%2Fportal%2Flogin'
                apis['host'] = host
            if 'campusphere' in ampUrl2 or 'cpdaily' in ampUrl2:
                parse = urlparse(ampUrl2)
                host = parse.netloc
                apis[
                    'login-url'] = idsUrl + '/login?service=' + parse.scheme + r"%3A%2F%2F" + host + r'%2Fportal%2Flogin'
                apis['host'] = host
            if joinType == 'NOTCLOUD':
                res = requests.get(url=apis['login-url'], verify=not debug)
                if urlparse(apis['login-url']).netloc != urlparse(res.url):
                    apis['login-url'] = res.url
            break
    if user['school'] == '云南财经大学':
        apis[
            'login-url'] = 'http://idas.ynufe.edu.cn/authserver/login?service=https%3A%2F%2Fynufe.cpdaily.com%2Fportal%2Flogin'
    if flag:
        log(user['school'] + ' 未找到该院校信息，请检查是否是学校全称错误')
        exit(-1)
    log(apis)
    return apis

# 全局配置
config = getYmlConfig()
session = requests.session()
user = config['user']
apis = getCpdailyApis(user)
host = apis['host']

# 获取Cpdaily-Extension
def getCpdailyInfo(user):
    extension = {
        "lon": user['lon'],
        "model": "PCRT00",
        "appVersion": "",
        "systemVersion": "4.4.4",
        "userId": user['username'],
        "systemName": "android",
        "lat": user['lat'],
        "deviceId": str(uuid.uuid1())
    }
    CpdailyInfo = DESEncrypt(json.dumps(extension))
    print('CpdailyInfo')
    print(CpdailyInfo)
    return CpdailyInfo

# 获取MOD_AUTH_CAS
def getModAuthCas(data):
    log('正在获取MOD_AUTH_CAS')
    sessionToken = data['sessionToken']
    headers = {
        'Host': host,
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 4.4.4; PCRT00 Build/KTU84P) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/33.0.0.0 Safari/537.36 cpdaily/8.0.8 wisedu/8.0.8',
        'Accept-Encoding': 'gzip,deflate',
        'Accept-Language': 'zh-CN,en-US;q=0.8',
        'X-Requested-With': 'com.wisedu.cpdaily'
    }
    url = 'https://{host}/wec-counselor-collector-apps/stu/mobile/index.html?timestamp='.format(host=host) + str(
        int(round(time.time() * 1000)))
    res = session.get(url=url, headers=headers, allow_redirects=False, verify=False)
    location = res.headers['location']
    # print(location)
    headers2 = {
        'Host': 'mobile.campushoy.com',
        'Connection': 'keep-alive',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 4.4.4; PCRT00 Build/KTU84P) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/33.0.0.0 Safari/537.36 cpdaily/8.0.8 wisedu/8.0.8',
        'Accept-Encoding': 'gzip,deflate',
        'Accept-Language': 'zh-CN,en-US;q=0.8',
        'Cookie': 'clientType=cpdaily_student; tenantId=' + apis['tenantId'] + '; sessionToken=' + sessionToken,
    }
    res = session.get(url=location, headers=headers2, allow_redirects=False, verify=False)
    location = res.headers['location']
    # print(location)
    session.get(url=location, headers=headers, verify=False)
    cookies = requests.utils.dict_from_cookiejar(session.cookies)
    if 'MOD_AUTH_CAS' not in cookies:
        log('获取MOD_AUTH_CAS失败')
        exit(-1)
    log('获取MOD_AUTH_CAS成功')

def coordinateOffset(val):
    try:
        val = float(val)
        val += random.uniform(-0.000003, 0.000003)
    except ValueError:
        return NULL
    return str(round(val, 6))

def pkcs7padding(text: str):
    """明文使用PKCS7填充"""
    remainder = 16 - len(text.encode("utf-8")) % 16
    return str(text + chr(remainder) * remainder)

def pkcs7unpadding(text: str):
    """去掉填充字符"""
    return text[:-ord(text[-1])]
