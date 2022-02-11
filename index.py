# -*- coding: utf-8 -*-
# 负责每天签到的主程序，调用一次填报一次
# from asyncio.windows_events import NULL
from utils import *
import urllib.parse
import hashlib
import oss2

############配置############
Cookies = {
    'acw_tc': '',
    'MOD_AUTH_CAS': 'rwNauP-dEcbdcSKDx-YW461604882518',
}
sessionToken = '2a537752-53e4-4733-8a81-cf2df72996cb'
#CpdailyInfo = 'DdU824D41oxAjKiM1Rd+7mNQpR3JEvYCcjx2psxMAGtLS8GvAzXSyqpXgd1mYUuBBZ3FCAdnh2IrncYpVW/X9EIQfb+4xMEP3T2HH/etsRCG0uHkjTvhT8F3JMvmdjtM+BZQ7b26DCpZicpo6afjAXQQolQFFtHuPWKFxZfrU3sd9IPCxq9M9iBcVdSYJALcSZHzi9HHUMSvwHy6pByncbh1Ad5xM4/yu6inNnL3zQTEKxyEa0IUmcDFe/qGL/AZW+xYxEFayy1tNxoh7IPxtgj/jpkuXYoC'

############配置############

# 全局
session = requests.session()
session.cookies = requests.utils.cookiejar_from_dict(Cookies)
# config = getYmlConfig('config.yml')
# user = config['user']
# host = getCpdailyApis(user)['host']
deviceID = str(uuid.uuid1())

lon = coordinateOffset(user['lon'])
lat = coordinateOffset(user['lat'])

# Cpdaily-Extension
extension = {
    "lon": lon,
    "lat": lat,
    "model": "iPhone11,8",
    "appVersion": "9.0.18",
    "systemVersion": "14.8.1",
    "userId": user['username'],
    "systemName": "iOS",
    "deviceId": deviceID
}

# 提交表单规范
submitDataFormat = {
    "lon": lon,
    "lat": lat,
    "version": 'first_v3',
    "calVersion": 'firstv',
    "deviceId": deviceID,
    "userId": user['username'],
    "systemName": 'iOS',
    "bodyString": 'bodyString',
    "systemVersion": '14.8.1',
    "appVersion": '9.0.18',
    "model": 'iPhone11,8'
}

# md5加密
def strHash(str_: str, hash_type, charset='utf-8'):
    """计算字符串哈希"""
    hashObj = hashlib.md5()
    bstr = str_.encode(charset)
    hashObj.update(bstr)
    return hashObj.hexdigest()

# 生成表单中sign
def signAbstract(submitData: dict, key="SASEoK4Pa5d4SssO"):
        '''表单中sign项目生成'''
        abstractKey = ["appVersion", "bodyString", "deviceId", "lat",
                       "lon", "model", "systemName", "systemVersion", "userId"]
        abstractSubmitData = {k: submitData[k] for k in abstractKey}
        abstract = urllib.parse.urlencode(abstractSubmitData) + '&' + key
        abstract_md5 = strHash(abstract, 5)
        return abstract_md5

# form表单BodyString加密
def encrypt_BodyString(text, key=b"SASEoK4Pa5d4SssO"):
    """BodyString加密"""
    iv = b'\x01\x02\x03\x04\x05\x06\x07\x08\t\x01\x02\x03\x04\x05\x06\x07'
    cipher = AES.new(key, AES.MODE_CBC, iv)

    text = pkcs7padding(text)  # 填充
    text = text.encode("utf-8")  # 编码
    text = cipher.encrypt(text)  # 加密
    text = base64.b64encode(text).decode("utf-8")  # Base64编码
    return text

# 查询表单
def queryForm():
    data = {
        'sessionToken': sessionToken
    }
    getModAuthCas(data)
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 (5133926912)cpdaily/9.0.18  wisedu/9.0.18',
        'content-type': 'application/json',
        'Accept-Encoding': 'gzip,deflate',
        'Accept-Language': 'zh-CN,en-US;q=0.8',
        'Content-Type': 'application/json;charset=UTF-8'
    }
    queryCollectWidUrl = 'https://{host}/wec-counselor-collector-apps/stu/collector/queryCollectorProcessingList'.format(
        host=host)
    params = {
        'pageSize': 6,
        'pageNumber': 1
    }
    res = session.post(queryCollectWidUrl, headers=headers, data=json.dumps(params), verify=False)
    if len(res.json()['datas']['rows']) < 1:
        return None

    collectWid = res.json()['datas']['rows'][0]['wid']
    formWid = res.json()['datas']['rows'][0]['formWid']

    detailCollector = 'https://{host}/wec-counselor-collector-apps/stu/collector/detailCollector'.format(host=host)
    res = session.post(url=detailCollector, headers=headers,
                       data=json.dumps({"collectorWid": collectWid}), verify=False)
    schoolTaskWid = res.json()['datas']['collector']['schoolTaskWid']

    getFormFields = 'https://{host}/wec-counselor-collector-apps/stu/collector/getFormFields'.format(host=host)
    res = session.post(url=getFormFields, headers=headers, data=json.dumps(
        {"pageSize": 100, "pageNumber": 1, "formWid": formWid, "collectorWid": collectWid}), verify=False)

    form = res.json()['datas']['rows']
    return {'collectWid': collectWid, 'formWid': formWid, 'schoolTaskWid': schoolTaskWid, 'form': form}


# 填写form
def fillForm(form):
    sort = 1
    mailContent = []
    for formItem in form:
        # 只处理必填项
        if formItem['isRequired'] == 1:
            default = config['cpdaily']['defaults'][sort - 1]['default']
            if formItem['title'] != default['title']:
                log('第%d个默认配置不正确，请检查' % sort)
                exit(-1)
            # 文本直接赋值
            if formItem['fieldType'] == '1':
                formItem['value'] = default['value']
            # 单选框需要删掉多余的选项
            if formItem['fieldType'] == '2':
                # 填充默认值
                formItem['value'] = default['value']
                fieldItems = formItem['fieldItems']
                for i in range(0, len(fieldItems))[::-1]:
                    if fieldItems[i]['content'] != default['value']:
                        del fieldItems[i]
            # 多选需要分割默认选项值，并且删掉无用的其他选项
            if formItem['fieldType'] == '3':
                fieldItems = formItem['fieldItems']
                defaultValues = default['value'].split(' ')
                for i in range(0, len(fieldItems))[::-1]:
                    flag = True
                    for j in range(0, len(defaultValues))[::-1]:
                        if fieldItems[i]['content'] == defaultValues[j]:
                            # 填充默认值
                            formItem['value'] += defaultValues[j] + ' '
                            flag = False
                    if flag:
                        del fieldItems[i]
            # 图片需要上传到阿里云oss
            if formItem['fieldType'] == '4':
                fileName = uploadPicture(default['value'])
                formItem['value'] = getPictureUrl(fileName)
            item = '必填问题%d：' % sort + formItem['title'] + ": " + formItem['value']
            mailContent.append(item)
            log(item)
            sort += 1

    return form, mailContent


# 上传图片到阿里云oss
def uploadPicture(image):
    url = 'https://{host}/wec-counselor-collector-apps/stu/collector/getStsAccess'.format(host=host)
    res = session.post(url=url, headers={'content-type': 'application/json'}, data=json.dumps({}), verify=False)
    datas = res.json().get('datas')
    fileName = datas.get('fileName')
    accessKeyId = datas.get('accessKeyId')
    accessSecret = datas.get('accessKeySecret')
    securityToken = datas.get('securityToken')
    endPoint = datas.get('endPoint')
    bucket = datas.get('bucket')
    bucket = oss2.Bucket(oss2.Auth(access_key_id=accessKeyId, access_key_secret=accessSecret), endPoint, bucket)
    with open(image, "rb") as f:
        data = f.read()
    bucket.put_object(key=fileName, headers={'x-oss-security-token': securityToken}, data=data)
    res = bucket.sign_url('PUT', fileName, 60)
    # log(res)
    return fileName


# 获取图片上传位置
def getPictureUrl(fileName):
    url = 'https://{host}/wec-counselor-collector-apps/stu/collector/previewAttachment'.format(host=host)
    data = {
        'ossKey': fileName
    }
    res = session.post(url=url, headers={'content-type': 'application/json'}, data=json.dumps(data), verify=False)
    photoUrl = res.json().get('datas')
    return photoUrl

# 生成Cpdaily-Extension
def generateCpdailyExtension():
    return DESEncrypt(json.dumps(extension))

# 提交表单
def submitForm(formWid, address, collectWid, schoolTaskWid, instanceWid, form):
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 (5133926912)cpdaily/9.0.18  wisedu/9.0.18',# cpdaily/8.2.14 wisedu/8.2.14
        'CpdailyStandAlone': '0',
        'extension': '1',
        'Cpdaily-Extension': generateCpdailyExtension(),
        'Content-Type': 'application/json; charset=utf-8',
        # 请注意这个应该和配置文件中的host保持一致
        'Host': host,
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip'
    }

    # 默认正常的提交参数json
    params = {"formWid": formWid, "address": address, "collectWid": collectWid, "schoolTaskWid": schoolTaskWid,
              "uaIsCpadaily": True, "latitude": lat, "longitude": lon, "instanceWid": instanceWid, "form": form}
    # print(params)
    bodyString = encrypt_BodyString(json.dumps(params))
    submitDataFormat["bodyString"] = bodyString
    submitDataFormat["sign"] = signAbstract(submitDataFormat)
    submitUrl = 'https://{host}/wec-counselor-collector-apps/stu/collector/submitForm'.format(host=host)
    r = session.post(url=submitUrl, headers=headers, data=json.dumps(submitDataFormat), verify=False)
    msg = r.json()['message']
    return msg


# 发送邮件通知
def sendMessage(send, msg):
    if send != '':
        header = {'Content-Type': 'application/json; charset=utf-8'}
        log('正在发送邮件通知')
        content = getTimeStr()
        for each in msg:
            content += '\n'
            content += each
        res = requests.post(url='http://1.15.137.116:8799/sendMail', headers=header,
                            json={'title': '今日校园疫情上报自动提交结果通知', 'content': content, 'to': send})
        if res.status_code == 200:
            print('发送邮件通知成功')
        else:
            print('发送邮件通知失败')


# 腾讯云函数启动函数
def main_handler(event, context):
    try:
        user = config['user']
        log('当前用户：' + str(user['username']))
        log('脚本开始执行')
        log('正在查询最新待填写问卷')
        params = queryForm()
        if str(params) == 'None':
            log('获取最新待填写问卷失败，可能是辅导员还没有发布')
            exit(-1)
        log('查询最新待填写问卷成功')
        log('正在自动填写问卷')
        form, mailContent = fillForm(params['form'])
        
        log('填写问卷成功')
        log('正在自动提交')
        msg = submitForm(params['formWid'], user['address'], params['collectWid'],
                        params['schoolTaskWid'], params.get('instanceWid', ''), form)
        if msg == 'SUCCESS':
            log('自动提交成功！')
            mailContent.append("自动提交成功！")
            sendMessage(user['email'], mailContent)
        elif msg == '该收集已填写无需再次填写':
            log('今日已提交！')
        else:
            log('自动提交失败')
            log('错误是' + msg)
            sendMessage(user['email'], '自动提交失败！错误是' + msg)
            exit(-1)
    except:
        return 'auto submit fail.'
    else:
        return 'auto submit success.'

# 配合Windows计划任务等使用
if __name__ == '__main__':
    print(main_handler({}, {}))
    # for user in config['users']:
    #     log(getCpdailyApis(user))
