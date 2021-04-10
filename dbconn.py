'''
Descripttion: 
version: 
Author: Catop
Date: 2021-03-08 22:38:09
LastEditTime: 2021-03-12 12:00:14
'''
#coding:utf-8
import os
import sys
import pymysql
import json
import goapi_recv
import time


cwd = os.path.dirname(os.path.realpath(__file__))
conf_info = cwd+"/config.json"

with open(conf_info,"r") as f:
    conf_dict = json.load(f)
db_info = conf_dict['DataBase']

conn = pymysql.connect(host=db_info['Address'],user = db_info['UserName'],passwd = db_info['PassWord'],db = db_info['DBname'])

def get_all_info():
    """拉取最新用户信息"""
    sql = "TRUNCATE TABLE QF_user"
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    conn.ping(reconnect=True)
    cursor.execute(sql)
    conn.commit()

    return

def update_friends_info(friends_list):
    """更新好友信息"""
    succ_count = 0
    fali_count = 0
    
    for i in range(0,len(friends_list)):
        try:
            user_id = str(friends_list[i]['user_id'])
            sql = f"SELECT * FROM QF_user WHERE user_id=%s LIMIT 1"
            params = [user_id]
            cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
            conn.ping(reconnect=True)
            cursor.execute(sql,params)

            #判断是否存在该用户
            user_info = cursor.fetchone()
            if(user_info):
                #判断用户备注是否有修改
                if(user_info['mark_name'] == friends_list[i]['remark']):
                    pass
                else:
                    sql = f"UPDATE QF_user SET mark_name=%s WHERE user_id=%s LIMIT 1"
                    params = [friends_list[i]['remark'],user_id]
                    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
                    conn.ping(reconnect=True)
                    cursor.execute(sql,params)
            else:
                if(len(friends_list[i]['remark'])>0):
                    #备注可能不存在
                    sql = f"INSERT INTO QF_user(user_id,mark_name) VALUES (%s,%s)"
                    params = [friends_list[i]['user_id'],friends_list[i]['remark']]
                else:
                    sql = f"INSERT INTO QF_user(user_id) VALUES (%s)"
                    params = [friends_list[i]['user_id']]
                cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
                conn.ping(reconnect=True)
                cursor.execute(sql,params)


        except:
            fali_count += 1
        else:
            succ_count += 1

    
    conn.commit()
    ret_msg = f"成功更新用户列表，成功{succ_count}个,失败{fali_count}个"
    print(ret_msg)
    return ret_msg


def update_group_info(group_list):
    """拉取最新群信息"""
    succ_count = 0
    fali_count = 0
    for i in range(0,len(group_list)):
        try:
            group_id = str(group_list[i]['group_id'])
            sql = f"SELECT * FROM QF_group WHERE group_id=%s LIMIT 1"
            params = [group_id]
            cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
            conn.ping(reconnect=True)
            cursor.execute(sql,params)

            group_info = cursor.fetchone()
            if(group_info):
                pass
            else:
                sql = f"INSERT INTO QF_group(group_id,group_name) VALUES (%s,%s)"
                params = (group_id,group_list[i]['group_name'])
                cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
                conn.ping(reconnect=True)
                cursor.execute(sql,params)
        except:
            fali_count += 1
        else:
            succ_count += 1
    
    conn.commit()
    ret_msg = f"成功更新群列表，成功{succ_count}个,失败{fali_count}个"
    print(f"成功更新群列表，成功{succ_count}个,失败{fali_count}个")
    
    return ret_msg
    
def count_plus(user_id):
    sql = f"UPDATE QF_user SET user_count=user_count+1 WHERE user_id=%s"
    params = [user_id]
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    conn.ping(reconnect=True)
    cursor.execute(sql,params)

    sql = f"UPDATE QF_group SET group_count=group_count+1 WHERE group_id=%s"
    params = [user_id]
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    conn.ping(reconnect=True)
    cursor.execute(sql,params)

    conn.commit()

def set_type(user_id,user_type):
    sql = f"UPDATE QF_user SET user_type=%s WHERE user_id=%s"
    params = [user_type,user_id]
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    conn.ping(reconnect=True)
    cursor.execute(sql,params)

    sql = f"UPDATE QF_group SET group_type=%s WHERE group_id=%s"
    params = [user_type,user_id]
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    conn.ping(reconnect=True)
    cursor.execute(sql,params)

    conn.commit()

def get_friend_info(user_id):
    sql = f"SELECT * FROM QF_user WHERE user_id=%s"
    params = [user_id]
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    conn.ping(reconnect=True)
    cursor.execute(sql,params)

    user_info = cursor.fetchone()
    conn.commit()

    return user_info
    
def get_group_info(user_id):
    sql = f"SELECT * FROM QF_group WHERE group_id=%s"
    params = [user_id]
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    conn.ping(reconnect=True)
    cursor.execute(sql,params)

    user_info = cursor.fetchone()
    conn.commit()

    return user_info
    
def get_type_list(user_type):
    type_dict = {}
    sql = f"SELECT * FROM QF_user WHERE user_type=%s"
    params = [user_type]
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    conn.ping(reconnect=True)
    cursor.execute(sql,params)
    user_info = cursor.fetchall()
    type_dict['friends'] = user_info
    
    sql = f"SELECT * FROM QF_group WHERE group_type=%s"
    params = [user_type]
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    conn.ping(reconnect=True)
    cursor.execute(sql,params)
    user_info = cursor.fetchall()
    type_dict['group'] = user_info
    
    
    return type_dict
    
def save_msg(user_id,message,type='private',group_id=''):
    ctime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    #ctime = '2021-03-11 23:44:23'
    
    if(type == 'private'):
        sql = "INSERT INTO QF_msg(user_id,message,time) VALUES(%s,%s,%s)"
        params = [user_id,message,ctime]
    elif(type == 'group'):
        sql = "INSERT INTO QF_msg_group(user_id,group_id,message,time) VALUES(%s,%s,%s,%s)"
        params = [user_id,group_id,message,ctime]

    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    conn.ping(reconnect=True)
    cursor.execute(sql,params)
    mid = conn.insert_id()
    conn.commit()

    return mid
    
def get_msg(mid):
    sql = "SELECT user_id FROM QF_msg WHERE id=%s LIMIT 1"
    params = [mid]
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    conn.ping(reconnect=True)
    cursor.execute(sql,params)
    msg_info = cursor.fetchone()
    
    return msg_info


def get_today_msg_count():
    """获取当日接受到的私聊消息数量"""
    ctime = time.strftime("%Y-%m-%d", time.localtime())
    time_start = str(ctime)+" 00:00:00"
    time_end = str(ctime)+" 24:00:00"
    sql = f"SELECT COUNT(*) FROM QF_msg WHERE time>='{time_start}' AND time<='{time_end}'"
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    conn.ping(reconnect=True)    
    cursor.execute(sql)
    count_num = cursor.fetchone()['COUNT(*)']
    
    return count_num


if __name__ == "__main__":
    #update_friends_info(goapi_recv.get_friends_list())
    #update_group_info(goapi_recv.get_group_list())
    
    #count_plus('1157994379')
    #set_type('1157994379','work')
    #print(get_friend_info('29242764'))
    #print(get_group_info('275733157'))
    #print(get_type_list('work'))
    #print(save_msg('601179193','test'))
    #print(get_msg(18))
    print(get_today_msg_count())
