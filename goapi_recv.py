'''
Descripttion: 
version: 
Author: Catop
Date: 2021-03-08 22:51:06
LastEditTime: 2021-03-12 07:35:34
'''
import os
import sys
import json
import requests

cwd = os.path.dirname(os.path.realpath(__file__))

#读取配置
conf_info = cwd+"/config.json"
with open(conf_info,"r") as f:
    conf_dict = json.load(f)

conf_dict = conf_dict['gocq-recv']
gocq_addr = conf_dict['Forward']['Address']
gocq_port = conf_dict['Forward']['Port']

host = f'http://{gocq_addr}:{gocq_port}'

def sendMsg(user_id,message):

    url = f'{host}/send_private_msg'
    data = {'user_id':user_id,'message':message}
    res = requests.get(url,params=data)
    print(f"回复私聊消息@{user_id}：{str(message)[:30]}")
    
    res_dict = eval(res.text)
    return res_dict

def sendGroupMsg(group_id,message):
    url = f'{host}/send_group_msg'
    data = {'group_id':group_id,'message':message}
    res = requests.get(url,params=data)
    print(f"回复群消息@{group_id}：{str(message)[:30]}")
    return res.text

def get_friends_list():
    url = f'{host}/get_friend_list'
    res = requests.get(url).text
    res = json.loads(res)
    res = res['data']

    return res

def get_group_list():
    url = f'{host}/get_group_list'
    res = requests.get(url).text
    res = json.loads(res)
    res = res['data']

    return res

def get_msg(message_id):
    url = f'{host}/get_msg'
    data = {'message_id':message_id}
    res = requests.get(url,params=data).text
    res = json.loads(res)
    #res = res['data']

    #message = res['message']

    return res

if __name__ == "__main__":
    #print(get_group_list())
    #print(sendMsg('29242764','hello'))
    print(get_msg(-713955801))