'''
Descripttion: 
version: 
Author: Catop
Date: 2021-03-09 23:14:51
LastEditTime: 2021-04-10 13:53:36
'''
import sys
import os
import json
import time
import datetime
from flask import Flask,request,jsonify
import goapi_recv
import dbconn
import logging
from flask import Flask
from flask_apscheduler import APScheduler
from apscheduler.schedulers.blocking import BlockingScheduler




############################
TARGET_USER_ID = '2026679347'   #转发目标qq号
SAVE_PRIVATE_MSG = True         #是否存储私聊消息
SAVE_GROUP_MSG = True           #是否存储群聊消息
DAILT_ALERT_HOUR = 23           #每日消息数提醒小时
DAILT_ALERT_MIN = 20            #每日消息数提醒分钟
############################


#读取配置文件
cwd = os.path.dirname(os.path.realpath(__file__))
conf_info = cwd+"/config.json"
with open(conf_info,"r") as f:
    conf_dict = json.load(f)
flask_addr = conf_dict['gocq-recv']['Reverse']['Address']
flask_port = conf_dict['gocq-recv']['Reverse']['Port']

#管理员状态设置
status = []

#定时任务
class SchedulerConfig(object):
    JOBS = [
        {
            'id': 'alert_today_count_job',
            'func': '__main__:alert_today_count_job',
            'args': None, # 执行程序参数
            'trigger': 'cron', 
            'hour' : DAILT_ALERT_HOUR, 
            'minute' : DAILT_ALERT_MIN
        }
    ]
#定义任务执行程序
def alert_today_count_job():
    goapi_recv.sendMsg(TARGET_USER_ID,f"辛苦了❤️，今天共处理了{dbconn.get_today_msg_count()}条消息，晚安~")


app = Flask(__name__)
app.config.from_object(SchedulerConfig())
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
        
        goapi_recv.sendMsg(TARGET_USER_ID,friend_update_ret+'\n'+group_update_ret)
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
            
            goapi_recv.sendMsg(TARGET_USER_ID,msg)


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
            goapi_recv.sendMsg(TARGET_USER_ID,f"回复消息到[{fwd_user_name}]成功")
        else:
            goapi_recv.sendMsg(TARGET_USER_ID,f"消息id{mysql_id}不存在")


    elif(message[0:5] == 'watch'):
        #设置短暂关注功能,命令格式为"watch ${用户昵称或备注} ${关注时间(分钟)}"
        watch_user_name = message.split(' ')[1]
        watch_time = message.split(' ')[2]
        
        #同名群和好友一并设置watch
        affected_rows = dbconn.set_watch(watch_user_name,watch_time)
        goapi_recv.sendMsg(TARGET_USER_ID,f"成功设置{affected_rows}行，关注时间{watch_time}分钟。")


    return 0


def pfm_private(user_id,message,message_id):
    """处理私聊消息"""
    if(user_id==TARGET_USER_ID):
        #管理消息
        admin_conf(user_id,message)
        
    else:
        #其他用户消息
        user_info = dbconn.get_friend_info(user_id)
        ctime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        mid = 0
        #存储消息
        if(SAVE_PRIVATE_MSG):
            mid = dbconn.save_msg(user_id,message)

        #watch功能
        if(ctime <= datetime.datetime.strftime(user_info['watch_endtime'],'%Y-%m-%d %H:%M:%S')):
            send_res = goapi_recv.sendMsg(TARGET_USER_ID,f"[{user_info['mark_name']}]\n\n{message}\n===================\n{ctime}\nid={mid}\n类型=watch")
            return 0
            
        if('all' in status):
            #转发全部消息
            goapi_recv.sendMsg(TARGET_USER_ID,f"[{user_info['mark_name']}]\n{message}")
        else:
            if(user_info['user_type'] in status):
                send_res = goapi_recv.sendMsg(TARGET_USER_ID,f"[{user_info['mark_name']}]\n\n{message}\n===================\n{ctime}\nid={mid}\n类型={user_info['user_type']}")
                
            else:
                #暂时不转发的消息逻辑，建议增加自动回复提示
                pass
        
        #无论是否转发，私聊消息全部计数
        dbconn.count_plus(user_id)


    return 0

def pfm_group(user_id,group_id,sender,message):
    
    group_info = dbconn.get_group_info(group_id)
    user_info = dbconn.get_friend_info(user_id)
    dbconn.count_plus(group_id)
    ctime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    if(SAVE_GROUP_MSG):
        dbconn.save_msg(user_id,message,type='group',group_id=group_id)

    #watch功能
    if(ctime <= datetime.datetime.strftime(group_info['watch_endtime'],'%Y-%m-%d %H:%M:%S')):
        goapi_recv.sendMsg(TARGET_USER_ID,f"[{group_info['group_name']}\n\n{message}\n===================\n{ctime}\n类型=watch")
        return 0

    if(user_info):
        if(user_info['user_type'] in status):
            #关注群内指定成员类型的所有消息，无论群类型如何
            dbconn.count_plus(user_id)
            user_name = user_info['mark_name']
            goapi_recv.sendMsg(TARGET_USER_ID,f"[{user_name}]-{group_info['group_name']}\n\n{message}\n===================\n{ctime}\n类型=user_info触发")
            
            return 0


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
        goapi_recv.sendMsg(TARGET_USER_ID,f"[{user_name}]-{group_info['group_name']}\n{message}")
        
        #群聊消息，仅当成功转发时增加好友计数
        dbconn.count_plus(user_id)
    else:
        #暂时不转发的消息逻辑
        pass



if __name__ == "__main__":
    #每次运行前自动更新好友和群库
    dbconn.update_friends_info(goapi_recv.get_friends_list())
    dbconn.update_group_info(goapi_recv.get_group_list())
    
    scheduler = APScheduler()  # 实例化APScheduler
    scheduler.init_app(app)  # 把任务列表载入实例flask
    scheduler.start()  # 启动任务计划
    app.run(host=flask_addr,port=flask_port,debug=False)
    
