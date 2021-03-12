'''
Descripttion: 
version: 
Author: Catop
Date: 2021-03-09 23:14:51
LastEditTime: 2021-03-12 09:13:58
'''
import sys
import os
import json
import time
from flask import Flask,request,jsonify
import goapi_recv
import dbconn


cwd = os.path.dirname(os.path.realpath(__file__))
conf_info = cwd+"/config.json"
with open(conf_info,"r") as f:
    conf_dict = json.load(f)

flask_addr = conf_dict['gocq-recv']['Reverse']['Address']
flask_port = conf_dict['gocq-recv']['Reverse']['Port']

status = []

pusher_user_id = '2026679347'

app = Flask(__name__)
@app.route('/', methods=['POST'])
def getEvent():
    

    data = request.json
    post_type = data.get('post_type')
    if(post_type == 'message'):
        message_type = data.get('message_type')
        message = data.get('message')
        message_id = data.get('message_id')
        user_id = str(data.get('user_id'))
        sender = data.get('sender')
        #sender为dict

        if(message_type == 'private'):
            pfm_private(user_id,message,message_id)
            
        elif(message_type == 'group'):
            group_id = str(data.get('group_id'))
            pfm_group(user_id,group_id,sender,message)

        else:
            #其他message_type
            pass
    else:
        #其他post_type
        pass
            
    return "0"


def admin_conf(user_id,message):
    """接收主人设置"""
    if('set' in message):
        if('@' in message):
            #设置指定用户状态
            message = message.split(' ')[1]
            friend_type = message.split('@')[0]
            friend_id = message.split('@')[1]
            friend_info = dbconn.get_friend_info(friend_id)
            dbconn.set_type(friend_id,friend_type)
            goapi_recv.sendMsg(user_id,f"成功设置用户{friend_id}\n类型:{friend_type}")

        else:
            status_all = message.split(' ')[1]
            if('+' in status_all):
                status_list = status_all.split('+')
                status.clear()
                for i in range(0,len(status_list)):
                    status.append(status_list[i])
            else:
                status.clear()
                status.append(status_all)
            goapi_recv.sendMsg(user_id,f'☀️当前状态:{status}')
    elif('update' in message):
        #接收更新列表指令
        friend_update_ret = dbconn.update_friends_info(goapi_recv.get_friends_list())
        group_update_ret = dbconn.update_group_info(goapi_recv.get_group_list())
        
        goapi_recv.sendMsg(pusher_user_id,friend_update_ret+'\n'+group_update_ret)
    elif('list' in message):
        #列出好友和群类型
        user_type = message.split(' ')[1]
        if(len(user_type)>0):
            friends_group_type = dbconn.get_type_list(user_type)
            
            msg = f"{user_type} 好友:\n"
            user_count = 0
            for i in range(0,len(friends_group_type['friends'])):
                msg += friends_group_type['friends'][i]['mark_name']
                msg += f"({friends_group_type['friends'][i]['user_id']})\n"
                user_count += 1
            msg += f"共计{user_count}\n\n"
            
            msg += f"{user_type} 群组:\n"
            group_count = 0 
            for i in range(0,len(friends_group_type['group'])):
                msg += friends_group_type['group'][i]['group_name']
                msg += f"({friends_group_type['group'][i]['group_id']})\n"
                user_count += 1
            msg += f"共计{group_count}\n\n"
            
            mid = goapi_recv.sendMsg(pusher_user_id,msg)
            #goapi_recv.sendMsg(pusher_user_id,mid['data']['message_id'])
            #goapi_recv.sendMsg(pusher_user_id,f"[CQ:reply,id={mid['data']['message_id']}]")
    elif(message[0:2] == 're'):
        #处理回复消息
        end_index = 0
        for end_index in range(2,len(message)):
            if (message[end_index] == ' ' or message[end_index]=='\n'):
                break
        mysql_id = int(message[2:end_index+1]) #QF_msg的id主键
        fwd_info = dbconn.get_msg(mysql_id)  #原消息内容
        if(fwd_info):
            fwd_user_id = fwd_info['user_id']
            fwd_message = message[end_index+1:]

            goapi_recv.sendMsg(fwd_user_id,fwd_message)
            fwd_user_name = dbconn.get_friend_info(fwd_user_id)['mark_name']
            goapi_recv.sendMsg(pusher_user_id,f"回复消息到[{fwd_user_name}]成功")
        else:
            goapi_recv.sendMsg(pusher_user_id,f"消息id{mysql_id}不存在")

        
        

    return 0

def pfm_private(user_id,message,message_id):
    """处理私聊消息"""
    if(user_id==pusher_user_id):
        admin_conf(user_id,message)
        
    else:
        #接收其他人消息
        user_info = dbconn.get_friend_info(user_id)
        if('all' in status):
            #转发全部消息
            goapi_recv.sendMsg(pusher_user_id,f"[{user_info['mark_name']}]\n{message}")
            return "0"
        else:

            if(user_info['user_type'] in status):
                mid = dbconn.save_msg(user_id,message)
                ctime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                send_res = goapi_recv.sendMsg(pusher_user_id,f"[{user_info['mark_name']}]\n\n{message}\n===================\n{ctime}\nid={mid}")
                fwd_mid = send_res['data']['message_id']
                


            else:
                #暂时不转发的消息逻辑
                pass
        
        #无论是否转发，私聊消息全部计数
        dbconn.count_plus(user_id)

    return 0

def pfm_group(user_id,group_id,sender,message):
    
    group_info = dbconn.get_group_info(group_id)
    user_info = dbconn.get_friend_info(user_id)

    if(user_info):
        if(user_info['user_type'] in status):
            #关注群内指定成员类型的所有消息，无论群类型如何
            dbconn.count_plus(user_id)
            user_name = user_info['mark_name']
            ctime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            goapi_recv.sendMsg(pusher_user_id,f"[{user_name}]-{group_info['group_name']}\n\n{message}\n===================\n{ctime}")
            
            return "0"
        


    if((group_info['group_type'] in status) and (sender['role']=='owner' or sender['role']=='admin')):

        if(sender['card']==""):
            #没设置群名片
            user_info = dbconn.get_friend_info(user_id)
            if(user_info):
                #好友库中有此人
                user_name = user_info['mark_name']
            else:
                user_name = sender['nickname']
        else:
            user_name = sender['card']
        goapi_recv.sendMsg(pusher_user_id,f"[{user_name}]-{group_info['group_name']}\n{message}")
        
        #群聊消息，仅当成功转发时增加好友计数
        dbconn.count_plus(user_id)
    else:
        #暂时不转发的消息逻辑
        pass

    dbconn.count_plus(group_id)

    



if __name__ == "__main__":
    dbconn.update_friends_info(goapi_recv.get_friends_list())
    dbconn.update_group_info(goapi_recv.get_group_list())

    app.run(host=flask_addr,port=flask_port,debug=True)
    
