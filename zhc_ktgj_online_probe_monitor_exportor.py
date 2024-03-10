#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2023/02/14 14:49
# @Author  : Weizhang45
# @File    :  zhc_ktgj_online_probe_monitor_exportor.py
# @Software: PyCharm
import web
import logging
import json
import requests
import subprocess


#todo 设置日志级别和格式
logging.basicConfig(level=logging.NOTSET,format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
#todo 0代表httpdns功能正常，1表示不存活
httpdns_alive = {"name":"httpdns_alive","value":0}
urls = (
    '/metrics', 'getdata'
)

setUrlsArgs = {'cp_name':'zhc-ktgj-device-online-probe',
     'url':'https://linkapi.xf-yun.com/api/v1/mt/sip/resolver',
     'label':'httpdns@linkapi.xf-yun.com','ips':['42.62.42.22','42.62.42.21','42.62.116.20']}


def ips_isallin(ip):
    res = ip in setUrlsArgs['ips']
    return res

def ips_ischange(ip_list):
    #todo 判异条件，httpdns返回的ips长度，不等于当前缓存的数据，且ips数据内容有变更
    if len(setUrlsArgs['ips']) == len(ip_list) and all(map(ips_isallin,ip_list)):
        return True
    else:
        return False

def ip_pingres(ip):
    res = subprocess.getstatusoutput('ping -c 1 -w 1 %s'%ip)
    return str(res[0])+'_'+ip

def split_alive(data):
    return int(data.split('_')[0])



#todo 请求函数
def req_data(url,cp_name,label):
    ds = requests.get(url)
    res = json.loads(ds.text)
    try:
        if res['code'] == 0:
            ips = res['data']['ips']
            if not ips_ischange(ips):
                #todo 1代表内容有变更
                iplist_ischange = 1
            else:
                iplist_ischange = 0
            ping_res = list(map(ip_pingres,ips))
            alive_res = list(map(split_alive,ping_res))
            if not any(alive_res):
                #todo 全部能ping通
                iplist_isallive = 0
            else:
                iplist_isallive = 1
        else:
            httpdns_alive['value'] = 1
    except KeyError:
        httpdns_alive['value'] = 2
    # todo  拼接数据
    kv_ips_res = []
    kv_iplist_change = 'zhc_ktgj_httpdns_online_probe{instance="%s",label="%s",tag_name="iplist_ischange"} %s' %(cp_name,label,iplist_ischange)
    kv_iplist_alive = 'zhc_ktgj_httpdns_online_probe{instance="%s",label="%s",tag_name="iplist_isallive"} %s' %(cp_name,label,iplist_isallive)
    kv_httpdns_alive = 'zhc_ktgj_httpdns_online_probe{instance="%s",label="%s",tag_name="%s"} %s' % (
    cp_name, label, httpdns_alive['name'],httpdns_alive['value'])
    for i in ping_res:
        kv_ip_res = 'zhc_ktgj_httpdns_online_probe{instance="%s",label="%s",tag_name="%s"} %s' %(cp_name,label,i.split('_')[-1],i.split('_')[0])
        kv_ips_res.append(kv_ip_res)
    ips_kvs = '\n'.join(kv_ips_res)
    # todo 拼接指标包
    return kv_iplist_change + '\n' + kv_iplist_alive + '\n' + kv_httpdns_alive + '\n' + ips_kvs + '\n'


class getdata:
    def GET(self):
        data = req_data(setUrlsArgs['url'],setUrlsArgs['cp_name'],setUrlsArgs['label'])
        return data



if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()