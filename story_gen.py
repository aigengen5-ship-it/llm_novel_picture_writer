from llm_def import *
#import lmstudio as lms
from openai import OpenAI
import os
import json
import sys
import random as rand
import time
import requests
import re
import uuid
import websocket
import datetime
import config
import copy
from urllib import request

story_full    = []
story_item    = []
story_guide = ""
chr1 = ""
chr2 = ""
story_data = ""
story_data_final = ""
story_progress = [""] * 5
title = ""
background = ""
theme = ""
template_fix = -1
story_summary = ""
ending = ""
template_sub = ""
city_org = ""
city_chg = ""
rag_diag = ""
writing_style = ""
sub_job = ""
sub_job2 = ""
pov = ""

def story_get_align(line, n):
    margin = 1
    data_len = len(line)
    if n > data_len:
        print(f"wrong number -> {line}, {n}")
        exit()
        return []

    result = []
    result_line = []
    
    # 1. 전체 길이를 n개로 나눈 '한 구역의 크기'
    # (정수 나눗셈으로 대략적인 크기를 구함)
    segment_size = data_len / n 

    for i in range(n):
        # 2. 이번 구역의 이론적 시작점과 끝점 계산
        # int()를 써서 인덱스로 변환
        seg_start = int(i * segment_size)
        seg_end = int((i + 1) * segment_size)
        
        # 3. 마진 적용 (범위를 안쪽으로 좁힘)
        # 예: 0~250 구간에 마진 10이면 -> 10~240 사이에서 뽑음
        valid_start = seg_start + margin
        valid_end = seg_end - margin
        
        # [예외처리] 마진이 너무 커서 시작이 끝보다 커지면?
        # 그냥 마진 없이 해당 구역 전체에서 뽑도록 안전장치
        if valid_start >= valid_end:
            valid_start = seg_start
            valid_end = seg_end

        # 4. 범위 내 랜덤 선택
        # randrange는 끝점(valid_end)을 포함하지 않으므로 안전함
        pick = rand.randrange(valid_start, valid_end)
        result.append(pick)

    for i in result:
        result_line.append(line[i])
        
    return result_line

def story_get(wildcard, num):
    with open(wildcard, 'r', encoding='utf-8') as r1:
        prompt_org = r1.readlines()

    prestory = []
    epi = ""
    line_valid = 0
    for line in prompt_org:
        if line.strip():
            if (line.find("###") > -1):
                pass
            else:                
                line = line.replace("**", "")
                line = re.sub(r'^\d+\.\s*', '', line)
                line_valid = 1
                epi += line
        elif not line.strip() and line_valid == 1:
            line_valid = 0
            if len(epi.splitlines()) >= 2:
                epi = epi.replace("\n", " -> ")
                epi = epi[:-3]
            else:                
                epi = epi.replace("\n", "")
            prestory.append(epi)
            epi = ""

    temp = story_get_align(prestory,num)

    if num == 1:
        return temp[0]
    else:
        return temp

def name_chg (line, name, name2):
    has_batchim1 = (ord(name[-1]) - 0xAC00) % 28 > 0
    has_batchim2 = (ord(name2[-1]) - 0xAC00) % 28 > 0

    if has_batchim1 == True:
        line = line.replace('[NAME]가', '[NAME]이')
        line = line.replace('[NAME]가', '[NAME]가')
        line = line.replace('[NAME]를', '[NAME]을')
        line = line.replace('[NAME]를', '[NAME]를')
        line = line.replace('[NAME]는', '[NAME]은')
        line = line.replace('[NAME]는', '[NAME]는')
        line = line.replace('[NAME]와', '[NAME]과')
        line = line.replace('[NAME]와', '[NAME]와')
    else:        
        line = line.replace('[NAME]이', '[NAME]가')
        line = line.replace('[NAME]가', '[NAME]가')
        line = line.replace('[NAME]을', '[NAME]를')
        line = line.replace('[NAME]를', '[NAME]를')
        line = line.replace('[NAME]은', '[NAME]는')
        line = line.replace('[NAME]는', '[NAME]는')
        line = line.replace('[NAME]과', '[NAME]와')
        line = line.replace('[NAME]와', '[NAME]와')

    if has_batchim2 == True:
        line = line.replace('[NAME2]가', '[NAME2]이')
        line = line.replace('[NAME2]가', '[NAME2]가')
        line = line.replace('[NAME2]를', '[NAME2]을')
        line = line.replace('[NAME2]를', '[NAME2]를')
        line = line.replace('[NAME2]는', '[NAME2]은')
        line = line.replace('[NAME2]는', '[NAME2]는')
        line = line.replace('[NAME2]와', '[NAME2]과')
        line = line.replace('[NAME2]와', '[NAME2]와')
    else:        
        line = line.replace('[NAME2]이', '[NAME2]가')
        line = line.replace('[NAME2]가', '[NAME2]가')
        line = line.replace('[NAME2]을', '[NAME2]를')
        line = line.replace('[NAME2]를', '[NAME2]를')
        line = line.replace('[NAME2]은', '[NAME2]는')
        line = line.replace('[NAME2]는', '[NAME2]는')
        line = line.replace('[NAME2]과', '[NAME2]와')
        line = line.replace('[NAME2]와', '[NAME2]와')

    line = line.replace('[NAME]', name)
    line = line.replace('[NAME2]', name2)

    return line

def char_override(char_txt):
    temp2 = char_txt.split("\n")
    for temp in temp2:
        if temp.find("[NAME]") > -1 and temp.find("나이") > -1:
            config.age = int(temp[temp.find("나이:")+3:])
        if temp.find("[NAME2]") > -1 and temp.find("나이") > -1:
            config.age2 = int(temp[temp.rfind("나이:")+3:])
        if temp.find("[NAME]") > -1 and temp.find("직업") > -1:
            config.job = temp[temp.rfind("직업:")+3:]
            if temp.find("긍지") > -1:
                config.job_attribute = "긍지"
            elif temp.find("의무") > -1:
                config.job_attribute = "의무"
            elif temp.find("평범") > -1:
                config.job_attribute = "평범"
            elif temp.find("불만") > -1:
                config.job_attribute = "불만"
        if temp.find("[NAME]") > -1 and temp.find("성격:") > -1:
            config.personality_real = temp[temp.rfind("성격:")+3:]
        if temp.find("[NAME]") > -1 and temp.find("가슴크기:") > -1:
            config.breasts_size = int(temp[temp.rfind("가슴크기:")+5:])
        if temp.find("[NAME2]") > -1 and temp.find("직업") > -1:
            config.job2 = temp[temp.rfind("직업:")+3:]
        if temp.find("[NAME]") > -1 and temp.find("성별") > -1:
            if temp.find("남성") > -1 or temp.find("남자") > -1 or temp.find("male") > -1:
                config.sex = "male"
                print("NAME->남성으로 변경")
                config.fem_enb = True
            elif temp.find("여성") > -1 or temp.find("여자") > -1 or temp.find("female") > -1:
                config.sex = "female"
                print("NAME->여성으로 변경")
        elif temp.find("[NAME2]") > -1 and temp.find("성별") > -1:
            if temp.find("남성") > -1:
                config.sex2 = "male"
                print("NAME2->남성으로 변경")
            elif temp.find("여성") > -1:
                config.sex2 = "female"
                print("NAME2->여성으로 변경")

def story_override(override_txt):
    global title
    global background
    global theme
    global template_fix
    global story_summary
    global ending
    global writing_style
    global pov

    flag = 0
    temp2 = override_txt.split("\n")
    story_summary = ""
    ending = ""
    for temp in temp2:
        if temp.find("###BACKUP###") > -1:
            flag = 1
        if flag == 0:            
            if temp.find("plump") > -1:
                print("plump detected")
                config.plump_enb = True
            if temp.find("제목:") == 0:
                title = temp.replace("제목:","")
            elif temp.find("주제:") == 0:
                theme = temp.replace("주제:","")
            elif temp.find("작성 스타일 템플릿") == 0:
                template_fix = int(temp.replace("작성 스타일 템플릿:",""))
                temp = line_merge("./story/COMMON/writing_style_long.txt")
                a = template_fix 
                writing_style = temp[temp.find("### 템플릿 " + str(a)): temp.find("### 템플릿 " + str(a+1))]
                for line in writing_style.splitlines():
                    if line.find("- 시점") == 0:
                        pov = line[5:]
            elif temp.find("플롯 스타일 템플릿") == 0:
                template_fix = int(temp.replace("플롯 스타일 템플릿:",""))
            elif temp.find("상황") == 0:
                story_summary += temp.replace("상황:","") + "\n"
            elif temp.find("결말") == 0:
                ending += temp.replace("결말:","") + "\n"

    #plot_sub(template_fix)
    story_set()

def story_headline(char_override):
    global story_data
    global story_data_final
    global background
    global story_summary
    global ending
    global city_org
    global city_chg
    global writing_style
    global sub_job
    global sub_job2

    temp = line_merge("./story/COMMON/writing_style_long.txt")
    if (template_fix != -1):
        a = template_fix
    else:        
        a = rand.randint(1,21)

    writing_style = temp[temp.find("### 템플릿 " + str(a)): temp.find("### 템플릿 " + str(a+1))]

    #temp = random_prompt("./story/COMMON/city.txt", -1)
    #city_org = temp.split(",")[0]
    #city_chg = temp.split(",")[1] + "(원 장소: " + city_org + ")"

    config.objective = temp.split("#")[0]
    config.objective_hidden = temp.split("#")[1]
    # story read
    a = rand.randint(0,2)
    flag = 0
    #while (flag == 0):
    #    temp = random_prompt("./story/SHORT/shortstory.txt", -1)
    #    temp2 = temp[temp.find("]")+2:].split("#")
    #    if temp2[0].find("남") > -1 and a == 2:
    #        flag = 1
    #    elif temp2[0].find("펨") > -1 and a == 2:
    #        flag = 1
    #    elif temp2[0].find("여") > -1 and a < 2:
    #        flag = 1

    #background
    #title = temp[:temp.find("]")].replace("[","")

    ## Story
    #count = temp[temp.find("]")+2:].count("#")
    ##temp2 = temp[temp.find("]")+2:].split("#")
    #story_summary = temp2[2]
    #ending = temp2[3]

    #if config.job == "":
    #    config.job = random_prompt("./story/COMMON/job.txt", -1)
    #    if temp2[0].find("남") > -1 and config.job.split(",")[1].find("남") > -1:
    #        flag = 1
    #        if config.sex == "":
    #            config.sex = "male"
    #    elif temp2[0].find("펨") > -1 and config.job.split(",")[1].find("남") > -1:
    #        flag = 1
    #        if config.sex == "":
    #            config.sex = "male"
    #    elif temp2[0].find("여") > -1 and config.job.split(",")[1].find("여") > -1:
    #        flag = 1
    #        if config.sex == "":
    #            config.sex = "female"

    # set character 2 as male
    #if config.job2 == "":
    #    config.job2 = random_prompt("./story/COMMON/job2.txt", -1)        
    #if config.sex2 == "":        
    #    config.sex2 = "male"

    #config.job_raw = config.job
    #config.job2_raw = config.job2
    #config.job = config.job.split(",")[0]
    #config.job2 = config.job2.split(",")[0]
    #sub_job  = temp2[0][:temp2[0].find("(")]        
    #sub_job2 = temp2[1][:temp2[1].find("(")]        

    #plot_sub(-1)
    story_set()

# def plot_sub(a = -1):
#     global template_sub
#     # Read story tempplate
# 
#     temp = line_merge("./story/SHORT/plot_sub.txt")
#     if a == 0:
#         template_sub = ""
#     else:        
#         tempplate_sub = " * 아래 템플릿은 스토리 전개를 도와주는 전개 과정임. 참고를 하되, 캐릭터 시트, 상황, 갈등 트리거, 결말에 더 촛점을 둘 것.\n"
# 
#         if a == -1:
#             template_num = rand.randint(1,22)
#         else:
#             template_num = a        
#         
#         template_sub += temp[temp.find("### 템플릿 " + str(a)): temp.find("### 템플릿 " + str(a+1))]

def story_set ():
    story_data = "스토리 제목: " + title + " 이야기(배경은 아래 참조해서 변경할 것)\n"
    story_data += "스토리 배경: " + city_chg + "(원래 지명:" + city_org + ",  원 지명과 비슷하나 이상하게 변형된 다른 세계의 장소)\n"
    story_data += "[NAME]의 성별: " + config.sex + "\n"
    story_data += "[NAME]의 직업: 스토리 제목/배경 참조하여 변경\n"
    story_data += "[NAME2]의 성별: " + config.sex2 + "\n"
    story_data += "[NAME2]의 숨겨진 직업: " + config.job2.split(",")[0] + "(" + sub_job2 + ")\n"
    story_data += "참고) 주어진 상황에 맞추어 등장인물의 복장, 외모 및 체형을 변경할 것.\n"
    story_data += "참고) 특히 [NAME]가 남성일 경우 남성복으로 무조건 변경할 것.\n\n"
    story_data_final  = " * 스토리 전개: " + story_summary + "\n"
    if theme != "":
        story_data_final += " * 스토리 테마: " + theme + "\n"
    story_data_final += " * [NAME]의 결말: " + ending + "\n"
    story_data_final += " * [NAME]의 변화: " + config.objective_hidden + "\n\n"

def story_gen (story, name, name2):
    global story_full
    global job
    global job2
    num = 5
    story_full = []
    story_tmp1 = []
    story_tmp2 = []
    story_tmp3 = []
    story_tmp4 = []

    #for i in range(1,num+1):
    #    story_item.append(["[SENSORY_FOCUS]"+str(i), sensory_get[i-1]])
    #    story_item.append(["[POSE]"+str(i), pose_get[i-1]])

    #final_ending = final_ending[0] + "\n" + final_ending[1] 

    #story_item.append(["[FINAL_FORM]", final_ending])
    #story_item.append(["[BODY_UPDATE]", body_update])
    #story_item.append(["[EPISODE_UPDATE]", episode_update])
    #story_item.append(["[POSSESSION_MARK1]", possession_mark[0]])
    #story_item.append(["[POSSESSION_MARK2]", possession_mark[1]])
    #story_item.append(["[POSSESSION_MARK3]", possession_mark[2]])
    #story_item.append(["[POSSESSION_MARK4]", possession_mark[3]])
    #story_item.append(["[TEMPLATE_SUB]", template_sub])
    #story_item.append(["[BODY_CHANGE1]", body_change[0]])
    #story_item.append(["[BODY_CHANGE2]", body_change[1]])
    #story_item.append(["[BODY_CHANGE3]", body_change[2]])
    #story_item.append(["[BODY_CHANGE4]", body_change[3]])
    #story_item.append(["[BODY_CHANGE5]", body_change[4]])
    #story_item.append(["[COMMON_CHANGE1]", common_change[0]])
    #story_item.append(["[COMMON_CHANGE2]", common_change[1]])
    #story_item.append(["[COMMON_CHANGE3]", common_change[2]])
    #story_item.append(["[COMMON_CHANGE4]", common_change[3]])
    #story_item.append(["[COMMON_CHANGE5]", common_change[4]])
    #story_item.append(["[COMMON_CHANGE6]", common_change[5]])
    #story_item.append(["[STORY_PROGRESS1]", story_progress[0]])
    #story_item.append(["[STORY_PROGRESS2]", story_progress[1]])
    #story_item.append(["[STORY_PROGRESS3]", story_progress[2]])
    #story_item.append(["[STORY_PROGRESS4]", story_progress[3]])
    #story_item.append(["[STORY_PROGRESS5]", story_progress[4]])
    story_item.append(["[TITLE]", title])
    story_item.append(["[BACKGROUND]", city_chg])
    story_item.append(["[SITUATION]", story_summary])
    story_item.append(["[THEME]", theme])
    story_item.append(["[OBJECTIVE]", config.objective])
    story_item.append(["[ENDING]", ending])
    story_item.append(["[RAG_DIAG]", rag_diag])
    story_item.append(["[EPISODE_NUM]", str(config.json_episode_num) ])
    story_item.append(["[STORY_GUIDE]", story_guide])

    for i in range(len(story_full)):
        story_full[i] = name_chg(story_full[i], name, name2).strip()

    return story_full

def story_update(line):
    for tag in story_item:
        # CLOTH setup
        if line.count(tag[0]) == 1 and tag[0].find("CLOTH") > -1:
            config.clothes = tag[1]
            if tag[1].find("#") > -1:
                tag[1] = tag[1][:tag[1].find("#")]
        try:                
            line = line.replace(tag[0], tag[1])
        except:
            print("ERROR at TAG:")
            print(line, tag[0], tag[1])
            exit()            

    return line        

