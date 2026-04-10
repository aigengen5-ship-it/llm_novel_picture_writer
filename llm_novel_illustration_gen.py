#Create a JSON file from the following text. The tags are separated by # characters. Each tag should be a key in the JSON object. The value for each key should be an object containing start_line and end_line numbers. Only include start and end lines; do not include the text itself as data.

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
import llm_def
#import llm_novel_revise
import copy
import rp
import story_gen
from urllib import request
import httpx  # OpenAI 라이브러리는 내부적으로 httpx를 씁니다
from openai import APIConnectionError, APITimeoutError, InternalServerError

# Save variable
import pickle

config.current_level = 0

# JSON read
with open('plot.json') as f:
    json_value = json.load(f)

if json_value["extended"] == "yes":
    import llm_def_extended
    import config
    import config_extended
else:
    import config

if json_value["dockermode"] == "yes":
    import docker_control

###########################################
# DEF(like function)
###########################################
def next_order_gen():
    order = "라이트 노벨 작성을 위해 아래 2가지 항목을 기억할 것. 절대 에피소드를 작성하지 말고 다음 명령을 대기할 것." + "\n\n" 
    order += "1) 등장인물의 캐릭터 시트." + "\n\n" + character_sheet + "\n\n"
    #order += "2) 에피소드 요약:\n" + episodekeep + "\n\n"
    order += "2) 배경 요약:\n" + background_story
    return order

def check_server_is_alive(base_url):
    """
    서버가 살아있는지 가벼운 요청을 보내 확인합니다.
    """
    # '/v1/models'는 보통 가장 가벼운 엔드포인트입니다.
    health_url = f"{base_url}/models"
    
    try:
        # 짧은 타임아웃(예: 3초)으로 찔러봅니다.
        response = httpx.get(health_url, timeout=3.0)
        
        if response.status_code == 200:
            return True, "정상"
        else:
            return False, f"서버 에러 (Status: {response.status_code})"
            
    except httpx.ConnectError:
        # 물리적으로 연결할 수 없음 (서버 꺼짐, 포트 닫힘)
        return False, "서버 다운됨 (연결 거부)"
        
    except httpx.ReadTimeout:
        # 서버가 너무 바쁘거나 멈춤
        return False, "서버 응답 없음 (타임아웃)"
        
    except Exception as e:
        return False, f"기타 에러: {e}"

def run_with_retry(func, *args, **kwargs):
    max_retries = 5
    last_exception = None

    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except (APIConnectionError, APITimeoutError, InternalServerError) as e:
            print (f"Reload model again.....")
            docker_control.switch_model(config.docker_llm_name)
            time.sleep(30) # 1초 숨 고르기
            return func(*args, **kwargs)
            # 여기서 클라이언트를 재생성하는 로직을 추가해도 좋습니다.
        except Exception as e:
            # 문법 에러 등 재시도해도 소용없는 에러는 바로 던짐
            raise e
    
###########################################
# Code start
###########################################

# Global variable
episodekeep = ""
background_story = ""
full_response = ""
artist_prompt = ""
base_prompt = ""   # only used for non-Anima mode
title = ""
chgword = ""
story = ""
episode_single = [] 
ragdata = ""
val1 = ""
val2 = ""
val3 = ""
val4 = ""
moral = 5
# RPDATA is single
rpdata = []
rpact = []
# RPTAG 
rptags = []

# Setup special
if len(sys.argv) == 5:
    config.json_episode_num = int(sys.argv[4])
else:
    config.json_episode_num = json_value["episode_num"]

# Docker LLM Name setup
#config.docker_llm_name = "gemma-3-27b"
config.docker_llm_name = "gemma-4-31b"
#config.docker_llm_name = "gpt-oss-120b"

# Web Socket Test
client_id = str(uuid.uuid4())  # Generate a unique client ID
ws = websocket.WebSocket()

# Artist select, not used on Anima
artist_prompt = random_prompt("data_comfyui/ura_artist_300.txt", json_value["artist"]-1) + ","

# Get time
output_date = "image_"+datetime.datetime.now().strftime("%Y_%m_%d__%H_%M")

# Set OpenAI local, Client for Main
client_rp = OpenAI(
    base_url="http://localhost:" + json_value["port_main"] + "/v1",
    api_key="llama"
)

# Client for support
client_control = OpenAI(
    base_url="http://localhost:" + json_value["port_support"] + "/v1",
    api_key="llama"
)

# System Prompt
system_line_rp = "You are a Japanese style light novel writing assistant for youngs. Answer in Korean."

# Sedtup RAG dialog, use whole dialog
if (json_value["rag_diag"] == "yes" and sys.argv[1] != "NONE"):
    story_gen.rag_diag = line_merge(sys.argv[1])

# Generate 1st message setup
messages_history_org     = [ {"role": "system", "content": system_line_rp} ]
messages_history_rp      = copy.deepcopy(messages_history_org)

#####################################
# Local Setup
#####################################
order = ""
temp = 0
story_summary = ""      # Summary
special_order = ""      # Special Order
userinput = ""          # User Input File(argv[3]), important!
clothes_1stdone = 0
rpvalue_1stdone = 0

# Prologue data setup, can be used later
prologue_skin = random_prompt("./data/prologue_skin.txt", -1)
prologue_hair = random_prompt("./data/prologue_hair.txt", -1)
prologue_eyes = random_prompt("./data/prologue_eye.txt", -1)
prologue_body = random_prompt("./data/prologue_body.txt", -1)
prologue_inner = random_prompt("./data/prologue_inner.txt", -1)

# Story theme
theme = ""

###########################################################################
# Plot read
###########################################################################
with open(sys.argv[2], 'r', encoding='utf-8') as f1:
    setup_line_org = f1.readlines()

###########################################################################
# Episode writing style read
###########################################################################
with open('./story/COMMON/episode_write.txt', 'r', encoding='utf-8') as f2:
    episode_line = f2.readlines()

setup_line = []
for line in setup_line_org:    
    flag = 0
    for i in range(1,30):
        if line.find(f"[EPISODE_GEN:{i}]") > -1:
            flag = 1
            for line2 in episode_line:
                setup_line.append(line2.replace("[NUM]", str(i)))
    if flag == 0:                
        setup_line.append(line)            

###########################################################################
# Character initialization
###########################################################################
###########################################################################
# user input split
###########################################################################
# If possible, override it
userinput = line_merge(sys.argv[3])
# Update sex based on override
temp = userinput.split("###SPLIT###")
char_override = temp[0]    
story_gen.story_guide = temp[1]
story_override2 = temp[2]
background_story = temp[3]
story_gen.city_chg = temp[3]

# Override
story_gen.char_override(char_override)
story_gen.story_headline(char_override)
story_gen.story_override(story_override2)

# Remove unnecessary 
char_override = re.sub(r'.*\[NAME\]의 가슴크기.*\n?', '', char_override)
story_gen.char_override(re.sub(r'.*\[NAME\]의 가슴크기.*\n?', '', char_override))

config.character_init(config.sex, json_value)
config.personality_init(json_value)


# setup special diaglog
episode_2nd_update = ""
if (json_value["extended"] == "yes"):
    dialog_special = ""
    temp = random_prompt_pic("./data_extended/rag_dialog.txt", 0, 20)
    for line in temp:
        dialog_special += line

    #episode_2nd_update = config_extended.episode_action


# Setup default value
temp = config.calage(theme, json_value)
story_gen.story_data = story_gen.name_chg(story_gen.story_data, config.name, config.name2)

# Age mapping
age = config.age
age2 = config.age2

# Setup dialog
#dialog = config_extended.dialog_init(config.personality)
#dialog_addon = "추가 대화 톤 설정은 아래와 같음\n" + config.dialog_addon()

ordernum = 0

config.character_update(config.current_level)
character_sheet, comfyui_prompt = config.character_sheet(config.current_level)

character_sheet = character_sheet.replace("[NAME]", config.name)
character_sheet = character_sheet.replace("[NAME2]", config.name2)

# New episode generation
full_episode = story_gen.story_gen(json_value["story"], config.name, config.name2)
char_override = story_gen.name_chg(char_override, config.name, config.name2)
story_gen.story_guide = story_gen.name_chg(story_gen.story_guide, config.name, config.name2)

#######################################################################
# Extended
#######################################################################
if json_value["extended"] == "yes":
    config_extended.body_final()
    final_desc = config_extended.description
    rel = config_extended.rel


#######################################################################
# Extended Done
#######################################################################

# Base image
#base_prompt = comfyui_base_gen(sex, age, json_value, artist_prompt, comfyui_prompt, name)
#comfyui_run_normal(json_value, "level1", base_prompt, job_clothes + "," + prompt1_1)

if json_value["dockermode"] == "yes":
    docker_control.switch_model(config.docker_llm_name)

# Character setup
order = "Review below 2 character's sheet and write it in Korean.\n"  
order += " * Your review result shall keep the same character sheet format.\n"
order += " * Think and update 2nd character sheet information.\n"
order += " * You shall write ## REVIEW DONE ## tag at the start/end of reviewed character sheet.\n"
order += "# 1st character sheet\n\n" + character_sheet
order += "\n\n# 2nd character sheet\n\n"
order += " * Name: " + config.name2 + "\n"
order += " * Sex: male\n"
order += " * Job: " + config.keyword_job + "\n * Age: " + str(age2) + "\n * Personality: Not defined\n"
order += special_order.replace("[NAME]", config.name)

messages_history_rp, full_response = openAI_response(json_value,client_rp, messages_history_rp, order ,2, False)
# Character sheet update
flag = 0
while (flag == 0):
    if full_response.count("REVIEW DONE") >= 1:
        character_sheet = full_response.split("## REVIEW DONE ##",1)[1]
        flag = 1
    else:        
        messages_history_rp, full_response = openAI_response(json_value,client_rp, messages_history_rp, order ,2, False)

order = """
캐릭터 시트에 아래 추가사항을 업데이트한 후 변경된 최종 캐릭터 시트를 출력할 것(절대 변경 이유/변경 전 내용 출력하지 말 것!!).\n 
 * 직업과 성격에 따라 캐릭터 수치(도덕성, 호감도등) 를 꼭 업데이트 할 것.
 * You shall write ## REVIEW DONE ## tag at the start/end of reviewed character sheet.
"""

order += story_gen.story_data  + "\n"
order += char_override

if config.sex == "male" and json_value["chr"] > -1:
    llm_def.line_num = "3"
    character = random_prompt("./data_comfyui/default_anime_male_chr.txt", json_value["chr"]-1)
    llm_def.line1 = character.split("#")[0]
    llm_def.line2 = character.split("#")[1].strip()
    order += "Update " + config.name + "'s character sheet appearance(" + llm_def.line1.replace(" is ", " looks like ") + ")"

messages_history_temp = copy.deepcopy(messages_history_rp)
messages_history_rp, full_response = openAI_response(json_value,client_rp, messages_history_rp, order ,2, False)
flag = 0

while flag == 0:
    if (full_response.count("REVIEW DONE") >= 1):
        character_sheet = full_response.replace("## REVIEW DONE ##","")
        character_sheet = full_response.replace("# REVIEW DONE #","")
        character_sheet = full_response.replace("##REVIEW DONE##","")
        character_sheet = full_response.replace("#REVIEW DONE#","")
        flag = 1
    else:        
        messages_history_rp = copy.deepcopy(messages_history_temp)
        messages_history_rp, full_response = openAI_response(json_value,client_rp, messages_history_rp, order ,2, False)

all_story = ""
all_story += "\n\n %%CHAR \n\n"
all_story += character_sheet
all_story += "\n\n %%CHARDONE \n\n"

# Writing style update
story_gen.writing_style = story_gen.name_chg(story_gen.writing_style, config.name, config.name2)

# Real start
order = ""
corr_tag_all = ""
titlefind = 0

# mapping
name = config.name
name2 = config.name2

for line in setup_line:
    if line[0:5] == "#####":
        pass
    # Test code        
    elif line.find("##SETLEVEL##") > -1:
        order = "아래 항목을 " + name + "의 캐릭터 시트에 반영할 것.\n"
        order += config_extended.setlevel(config.sex)
        order = name2 + "의 캐릭터 시트는 그대로 유지할 것\n"
        print("[System] Character Sheet is updated")
        messages_history_rp, full_response = openAI_response(json_value,client_rp, messages_history_rp, order ,2, False)
        if full_response.count("##") >= 1:
            character_sheet = "## " + full_response.split("##",1)[1]
        else:                
            character_sheet = full_response
        order = ""            

    elif line.find("##HARDSTOP##") > -1:
        if line.find("titlegen") > -1:
            llm_def.qwen35_think = True
            cnt = 0
            while (titlefind == 0):
                titlefind = 1
                cnt += 1
                messages_history_rp, full_response = openAI_response(json_value,client_rp, messages_history_rp, order ,2, False)
                pattern = r"[^가-힣ㄱ-ㅎㅏ-ㅣa-zA-Z0-9\s]"
                title = re.sub(pattern, "", full_response)
                title = title.replace("\r", "")
                title = title.replace("\n", "")
                story = title.replace(" ", "_")
                if len(story) > 50:
                    story = story[:50]
                story = "./result/" + story + ".txt"
                f4 = open(story, 'w', encoding='utf-8') 
                f4.write(all_story)
                f4.close()
                f4 = open("./result/anima_prompt.txt", 'w', encoding='utf-8') 
                f4.write(llm_def.anima_prompt)
                f4.close()
            llm_def.qwen35_think = False
        elif line.find("docker") > -1:
            print(f"Docker Change is requested at {line.find('##docker')}")
            config.docker_llm_name = line.replace("##HARDSTOP##docker:","").strip()
            docker_control.switch_model(config.docker_llm_name)
        elif line.find("summary") > -1:
            messages_history_rp, full_response = openAI_response(json_value,client_rp, messages_history_rp, order ,2, False)
            if full_response.count("## SUMMARY ##") == 1:
                story_summary = full_response.split("## SUMMARY ##", 1)[1]
            elif full_response.count("## SUMMARY ##") >= 2:
                story_summary = full_response.split("## SUMMARY ##", 2)[1]
        # Order update
        elif line.find("episodekeep") > -1:
            episode_single = []
            llm_def.qwen35_think = True
            flag = 0
            fail = 0
            messages_history_temp = copy.deepcopy(messages_history_rp)
            while (flag == 0):
                messages_history_rp, full_response = openAI_response(json_value,client_rp, messages_history_rp, order ,2, False)

                episodekeep = full_response

                print("##DEBUG##")
                print(episodekeep)
                print("##DEBUGDONE##")

                # Exclude final one since there is another checker
                for i in range(1,config.json_episode_num):
                    a = episodekeep.find("에피소드 " + str(i))
                    b = episodekeep.find("에피소드 " + str(i+1))
                    if a > -1 and b > -1:
                        # Check clothes on final step
                        if line.find("episodekeepfinal") > -1:
                            clothes_flag = 0
                        else:                            
                            clothes_flag = 1
                        # Episode save    
                        temp = episodekeep[a:b]
                        episode_single.append(temp)
                        # Clothes save
                        lines = temp.split("\n")
                        clothes = ""
                        action = "standing"
                        location = "room"
                        for line in lines:
                            if line.find("행동") == 0:
                                action = line.replace("행동","").replace("#","").replace(":","").strip()
                            if line.find("장소") == 0:
                                location = line.replace("장소","").replace("#","").replace(":","").strip()
                            if line.find("복장") == 0:
                                clothes = line.replace("복장","").replace("#","").replace(":","").replace("blindfold", "hairband").strip()
                                clothes_flag = 1
                                print(f"에피소드{i}: {clothes}")
                                # Update Clothes if it is longer
                        if clothes_1stdone == 0:
                            config.clothes_arr.append(clothes)
                            config.action_arr.append(action)
                            config.location_arr.append(location)
                        else:
                            if len(clothes) > len(config.clothes_arr[i-1]):
                                config.clothes_arr[i-1] = clothes
                            if len(action) > len(config.action_arr[i-1]):
                                config.action_arr[i-1] = action
                            if len(location) > len(config.location_arr[i-1]):
                                config.location_arr[i-1] = location


                        flag = 1                                
                    else:                
                        print(f"Episode is not founded: 에피소드 value: {i}")
                        flag = 0
                        config.clothes_arr = []
                        episode_single = []
                        messages_history_rp = copy.deepcopy(messages_history_temp)
                        break
                    if clothes_flag == 0:
                        print(f"No clothes is found")
                        flag = 0
                        config.clothes_arr = []
                        episode_single = []
                        messages_history_rp = copy.deepcopy(messages_history_temp)
                        break

                # Last episode check
                if (flag == 1):
                    a = episodekeep.find(f"에피소드 {config.json_episode_num}")
                    if a > -1:
                        episode_single.append(episodekeep[a:])
                        temp = episodekeep[a:]
                        lines = temp.split("\n")
                        for line in lines:
                            if line.count("복장") > 0:
                                clothes = line.replace("복장","").replace("#","").replace(":","").replace("blindfold", "hairband").strip()
                            if line.find("행동") == 0:
                                action = line.replace("행동","").replace("#","").replace(":","").strip()
                            if line.find("장소") == 0:
                                location = line.replace("장소","").replace("#","").replace(":","").strip()
                            if line.find("복장") == 0:
                                clothes = line.replace("복장","").replace("#","").replace(":","").strip()
                                clothes_flag = 1
                                #print(f"에피소드{i}: {clothes}")
                        # Update Clothes if it is longer
                        if clothes_1stdone == 0:
                            config.clothes_arr.append(clothes)
                            config.action_arr.append(action)
                            config.location_arr.append(location)
                        else:
                            if len(clothes) > len(config.clothes_arr[i-1]):
                                config.clothes_arr[i-1] = clothes
                            if len(action) > len(config.action_arr[i-1]):
                                config.action_arr[i-1] = action
                            if len(location) > len(config.location_arr[i-1]):
                                config.location_arr[i-1] = location


                        # Update Clothes if it is longer
                        if clothes_1stdone == 0:
                            config.clothes_arr.append(clothes)
                        else:
                            if len(clothes) > len(config.clothes_arr[config.json_episode_num -1]):
                                config.clothes_arr[config.json_episode_num -1] = clothes

                        print(f"에피소드{config.json_episode_num}: {clothes}")
                        config.clothes_arr.append(clothes)
                        flag = 1
                    else:                    
                        print(f"Not founded: 에피소드 value: {a}")
                        flag = 0
                        messages_history_rp = copy.deepcopy(messages_history_temp)

            clothes_1stdone = 1
            llm_def.qwen35_think = False
        #elif line.find("levelup") > -1:
        #    print("##DEBUG:LEVELUP##")
        #    config.current_level += 1
        #    if (line.find("final") > -1 or config.current_level >= 4):
        #        config.current_level = 4
        #    config_extended.levelup(config.current_level)

        elif line.find("specialset") > -1:
            print("##DEBUG:SETto10##")
            config.current_level = 10


        elif line.find("orderupdate") > -1:
            messages_history_rp      = copy.deepcopy(messages_history_org)

            order += next_order_gen() 
            messages_history_rp, full_response = openAI_response(json_value,client_rp, messages_history_rp, order ,2, False)

            order += "\n\n 잘 기억한 후 다음 명령을 대기할 것"
            order = story_gen.name_chg(order, config.name, config.name2)
            messages_history_rp, full_response = openAI_response(json_value,client_rp, messages_history_rp, order ,2, False)

        elif line.find("character_sheet") > -1:
            print("[System] Character Sheet is updated")
            order = "**중요** : Right Arrow Symbol(rightarrow) 절대 사용하지 말 것. 최종 결과만 적을 것!\n" + order
            # plot_output = add_user_msg(chat,model,json_value,order, "STORY")
            messages_history_rp, full_response = openAI_response(json_value,client_rp, messages_history_rp, order ,2, False)
            #messages_history_temp, full_response = openAI_translate(client2, messages_history_temp, full_response, 0)
            if full_response.count("##") >= 1:
                character_sheet = "## " + full_response.split("##",1)[1]
            else:                
                character_sheet = full_response
            all_story += "\n\n %%CHAR \n\n"
            all_story += character_sheet
            all_story += "\n\n %%CHARDONE \n\n"
        elif line.find("##storyreview") > -1:
            llm_def.qwen35_think = True
            messages_history_pre = copy.deepcopy(messages_history_rp)

            # Update writing style
            flag = 0
            while (flag == 0):
                messages_history_rp, full_response = openAI_response(json_value,client_rp, messages_history_rp, order ,2, False)
                if len(full_response) > 20:
                    flag = 1
                else:    
                    messages_history_rp = copy.deepcopy(messages_history_pre)

            if json_value["review"] == "yes":
                order = "방금 작성한 에피소드를 꼼꼼히 다시 리뷰할 것. \n* 중국어, 한자, 영어는 한글로 바꿀 것. 특히 맞춤법과 존대말 꼼꼼히 리뷰하고 같은 포맷으로 다시 출력할 것"
                check = 0
                
                while (check == 0):
                    messages_history_rp, full_response = openAI_response(json_value,client_rp, messages_history_rp, order ,2, False)
                    if len(full_response) > 20:
                        check = 1
                    else:    
                        messages_history_rp = copy.deepcopy(messages_history_pre)

            #messages_history_rp = copy.deepcopy(messages_history_pre)
            all_story += "\n\n %%STORY \n\n"
            all_story += f"EPISODE {config.episode_num}"
            all_story += full_response
            all_story += "\n\n %%STORYDONE \n\n"
            llm_def.qwen35_think = False
            config.episode_num += 1
            if config.episode_num == config.json_episode_num:
                config.episode_num = config.json_episode_num - 1

        elif line.find("##storypre") > -1:
        # Setup information before episode writing
            order =  "*** 아래 정보들은 에피소드를 작성하기 위하여 필요한 guide이므로 잘 읽고 추후 에피소드 작성에 반영할 것. 이해했으면 YES라고 답변할 것\n"
            #order +=  "A) 현재 [NAME]의 상태 \n"
            #order += rpdata[config.episode_num] +"\n"
            order += "A) 에피소드 집필 스타일 \n"
            order += story_gen.writing_style +"\n"
            order += f"B) 에피소드 {config.episode_num+1} 전체 요약: \n"
            order += "참고) #INNER는 속마음이고, #TALK는 [NAME]와 [NAME2]의 대화신임. 이 태그 위치에 자세하게 대화/속마음을 쓸 것.\n\n"
            order += episode_single[config.episode_num] + "\n\n" 
            # 최종 order
            order = story_gen.name_chg(order, name, name2)
            messages_history_rp, full_response = openAI_response(json_value,client_rp, messages_history_rp, order ,2, False)

        elif line.find("##story") > -1:
            messages_history_pre = copy.deepcopy(messages_history_rp)
            order = story_gen.name_chg(order, name, name2)

            check = 0
            while (check == 0):
                messages_history_rp, full_response = openAI_response(json_value,client_rp, messages_history_rp, order ,2, False)
                if len(full_response) > 20:
                    check = 1
                else:    
                    messages_history_rp = copy.deepcopy(messages_history_pre)

            #messages_history_rp = copy.deepcopy(messages_history_pre)
            all_story += "\n\n %%STORY \n\n"
            all_story += full_response
            all_story += "\n\n %%STORYDONE \n\n"

        elif line.find("##episodeup") > -1:
            config.episode_num += 1
            if config.episode_num == config.json_episode_num:
               config.episode_num = config.json_episode_num - 1
            # Use L value as current level               
            #config.current_level = config.status_arr[config.episode_num][1]

        elif line.find("##animastanding") > -1:
            messages_history_pre = copy.deepcopy(messages_history_rp)
            #config.animabodytag = config.body_tag[config.episode_num]
            anima_gen_standing("story", messages_history_rp,json_value,client_rp,config.sex, name, name2)
            messages_history_rp = copy.deepcopy(messages_history_pre)

        elif line.find("##anima") > -1:
            config.anima_think = True
            messages_history_pre = copy.deepcopy(messages_history_rp)
            config.pose = "Describe " + name + "'s pose based on current episode. Choose the 'best' pose which explains current episode best."
            #config.animabodytag = config.body_tag[config.episode_num]
            anima_gen_simple("story", messages_history_rp,json_value,client_rp,config.sex, name, name2)
            messages_history_rp = copy.deepcopy(messages_history_pre)

            config.anima_think = False
            lines = config.action_arr[config.episode_num].split(",")[0]
            a = 1
            for line in lines:
                messages_history_pre = copy.deepcopy(messages_history_rp)
                config.pose = "" # comment out for this version
                config.animabodytag = "" # comment out for this version
                anima_gen_simple("story", messages_history_rp,json_value,client_rp,config.sex, name, name2)
                messages_history_rp = copy.deepcopy(messages_history_pre)
                a += 1
                if a == json_value["imagenum"]:
                    break
                            
        elif line.find("##end") > -1:
            print(character_sheet)
            if (json_value["noimage"] == "no"):
                while True:
                    ws.connect(f"ws://127.0.0.1:8188/ws?clientId={client_id}")
                    out = ws.recv()
                    if out.find('{"queue_remaining": 0}') > -1:
                        time.sleep(60)
                        break
                    else:
                        # Binary data (preview images)
                        time.sleep(50)
                os.mkdir("/home/chrisyeo/AI/ComfyUI/output/"+output_date)
                os.system("mv /home/chrisyeo/AI/ComfyUI/output/*.png /home/chrisyeo/AI/ComfyUI/output/" + output_date)
            exit()
        else:
            messages_history_rp, full_response = openAI_response(json_value,client_rp, messages_history_rp, order ,2, 0)
        order = ""

    else:
        line = line.replace("\n","")
        # 1st change is episode replace.
        line = line.replace("[CHARACTER_SHEET]", character_sheet)
        line = line.replace("[LEVELUP_CHANGE]", config.curr_face)
        line = line.replace("[MOE_BODY]", random_prompt("story/COMMON/moe_body.txt", -1))
        line = line.replace("[NUM]", str(config.json_episode_num))
        line = line.replace("[POV]", story_gen.pov)
        line = line.replace("[EPISODE_2ND_UPDATE]", episode_2nd_update)
        if (rpvalue_1stdone == 1):
            line = line.replace("[BODY_TAG]", config.body_tag[config.episode_num])
        for i in range(0,len(full_episode)):
            line = line.replace("[STORY" + str(i+1) + "]", full_episode[i])
        line = story_gen.story_update(line) 

        # Final fix for name
        line = story_gen.name_chg(line, name, name2)
        order += line + "\n"

# Update image
f4.close()

# Wait until all queue is empty
if (json_value["noimage"] == "no"):
    while True:
        ws.connect(f"ws://127.0.0.1:8188/ws?clientId={client_id}")
        out = ws.recv()
        if out.find('{"queue_remaining": 0}') > -1:
            time.sleep(60)
            break
        else:
            # Binary data (preview images)
            time.sleep(50)
    os.mkdir("/home/chrisyeo/AI/ComfyUI/output/"+output_date)
    os.system("mv /home/chrisyeo/AI/ComfyUI/output/*.png /home/chrisyeo/AI/ComfyUI/output/" + output_date)

#if json_value["review_docker"] == "yes":
#    config.docker_llm_name = "gemma-3-27b"
#    docker_control.switch_model(config.docker_llm_name)
#    llm_novel_revise.revise_execute(story, client_rp)

exit()

