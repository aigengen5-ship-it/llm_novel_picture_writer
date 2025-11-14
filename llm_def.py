from llm_def import *
import lmstudio as lms
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
from urllib import request

# Global setup
event_done = [0] * 16
abnormal_tag = ""
output_date = datetime.datetime.now().strftime("%Y_%m_%d__%H_%M")

def lower_conv(temp):
    temp = temp.replace(".", "")
    temp = temp.lower()
    return temp

def rag_update(name, dialog_line):
    # Dialog 입력
    order = "Analyze below Korean lovely dialogs and modify on " + name + "'s condition(Keep original expression). Remember diaglogs and wait next order. Never answer.\n"
    for line in dialog_line:
        order += line 
    order += "\n"

    return order

def lower_conv(temp):
    temp = temp.replace(".", "")
    temp = temp.lower()
    return temp

def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    req =  request.Request("http://localhost:8188/prompt", data=data)
    request.urlopen(req)

    return

def comfyui_base_gen(sex, age, json_value, artist_prompt, chat, model, name):
    global clothes
    age_prompt = ""
    #quality_prompt = "masterpiece,amazing quality, very aesthetic, absurdres, newest,finely detailed,colorful, blurry background:2.0, 1girl, solo, black outline,medium_shot,hair top:2.5, full head:2.5, looking_at_viewer,"
    quality_prompt = "masterpiece,amazing quality, very aesthetic, absurdres, newest,finely detailed,colorful, blurry background:2.0, 1girl, solo, medium_shot,hair top:2.5, full head:2.5, looking_at_viewer, pov, "

    # Change Sex
    if sex == "male":
        quality_prompt = quality_prompt.replace("1girl","1boy,adolescent")
        quality_prompt = quality_prompt.replace("solo","solo_male")

    # Hair color
    chr_prompt = "(" + random_prompt("data_comfyui/Hair_04.Color.txt", -1) + ","
    # Hair width
    if sex == "male":
        if rand.randint(0,1) == 0:
            chr_prompt += "short cut,pixie cut,"
        else:
            chr_prompt += "short cut,bob cut,"
    else:
        chr_prompt += random_prompt("data_comfyui/hairlength.txt", -1) + ","
        
    # Select Ponytail/Braid
    if (rand.randint(0,5) == 0):
        chr_prompt += random_prompt("data_comfyui/ponytail.txt", -1) + ","
    elif (rand.randint(0,5) == 0):
        chr_prompt += random_prompt("data_comfyui/hairbraid.txt", -1) + ","
    # Select HairBang
    if (rand.randint(0,2) == 0):
        chr_prompt += random_prompt("data_comfyui/hairbang.txt", -1) + ","
    # Hair Status(wavy...)
    chr_prompt += random_prompt("data_comfyui/hairstatus.txt", -1) 
    chr_prompt += "),"
    
    # Face 
    chr_prompt += random_prompt("data_comfyui/Eye_Color.txt", -1) + ","

    # Age/sex
    if (sex == "female"):
        if (age > 35):
            age_prompt = "mature female,milf,mom,aged up,"
            chr_prompt += age_prompt
        elif (age >= 30):
            age_prompt = "milf,aged up,"
            chr_prompt += age_prompt
        elif (age <= 16):
            age_prompt = "loli,aged down,"
            chr_prompt += age_prompt
        else:
            age_prompt = ""

    # body size
    chr_prompt += random_prompt("data_comfyui/body.txt", json_value["body"] - 1) + ","
    
    base_prompt = quality_prompt + artist_prompt + chr_prompt

    # Update face
    if rand.randint(1, 10) <= json_value["freckles"]:
        base_prompt += "freckles,"

    if rand.randint(1, 10) <= json_value["glasses"]:
        base_prompt += random_prompt("data_comfyui/Eyewear.txt", -1)  + ","

    if rand.randint(1, 10) <= json_value["hairacc"]:
        base_prompt += random_prompt("data_comfyui/Accessories_Hair.txt", -1)  + ","

    return base_prompt, chr_prompt, age_prompt

def comfyui_run(chat,model,json_value,eventnum, eventname, base_prompt, name, corr_tag_all, corr_table, age_prompt, final_corr, half_corr, change1, change2, change3):
    global abnormal_tag

    # Event tag is used only 
    if json_value["plot"] == "fem":
        tmp = "_boy"
    else:
        tmp = ""
    event_tag = []
    event_tag.append(["date", 20 ])
    event_tag.append(["hold hands", 40 ])
    event_tag.append(["hug", 60 ])
    event_tag.append(["kiss_normal", 80 ])
    event_tag.append(["kiss_deep", 100])

    eventtag = eventname[eventnum]
    print("##" + eventtag + " Image Generation...")

    order = "Think and answer " + name + "'s current corruption level from 0% to 100%. Keep output format as 'Value:50%'"
    temp = add_user_msg(chat,model,json_value,order,"NONE")
    temp = temp[:temp.find("%")]
    numbers = int(re.sub(r'[^0-9]', '', temp))
    print("Real numbers:" + str(numbers) + "\n")

    order = "Think and answer " + name + "'s current love level from 0% to 100%. Keep output format as 'Value:50%'"
    temp = add_user_msg(chat,model,json_value,order,"NONE")
    lovepower = int(re.sub(r'[^0-9]', '', temp))

    #order = "Think and answer following questions, consider current" + eventtag + " and corruption/love level. Answer format is adjective + noun(example:white dress, dark street)\n"
    #order += "Thank and answer in English in one line: " + name + "'s costume in one line(item is separated by comma, write topwear, bottomwear and accessories)"
    #dress = add_user_msg(chat,model,json_value,order, "tag1")
    #dress = lower_conv(dress)
    #dress = dress.replace("\n", ",")

    order = "Think and answer in English in one line: current location in one word(item is separated by comma, the descriptive style is adjective + noun. For example: dirty room)"
    location = add_user_msg(chat,model,json_value,order, "tag1")
    location = lower_conv(location)
    location = location.replace("\n", ",")

    order = "Think and answer in English in one line: " + name + "'s clothes during " + eventtag + "."
    clothes = add_user_msg(chat,model,json_value,order,"NONE")
    clothes = lower_conv(clothes)
    clothes = clothes.replace("\n", ",")

    if numbers > 70:
        order = "Think and answer in English in one line: " + name + "'s current body expose based on corruption level(none, open_clothes, one_breast_out, topless, bottomless, nude)"
        expose = add_user_msg(chat,model,json_value,order,"NONE")
        expose = lower_conv(expose)
        if expose == "none":
            expose = ""
    else:
        expose = ""

    order = "Think and answer " + name + "'s expressions during " + eventtag + " in two words; separated with comma(Word examples: smile, sad, anger, calm, tear, embarrassed, full-face blush, seductive_smile, ahegao, drool, orgasm, etc)"
    expression = add_user_msg(chat,model,json_value,order, "tag1")
    expression = lower_conv(expression)
    expression = expression.replace("\n", ",")

    order = "Think and answer " + name + "'s expressions in two words."
    pose = add_user_msg(chat,model,json_value,order, "tag1")
    pose = lower_conv(pose)
    pose = pose.replace("\n", ",")

    if numbers > 50 and eventnum > 2:
        order = "Think and answer " + name + "'s every body and face changes using 2 words or more words during " + eventtag + ". Each single changes shall be separated with comma.(Example: full makeup, sweat)"
        abnormal_tag = add_user_msg(chat,model,json_value,order, "tag1") + ","
        abnormal_tag = abnormal_tag.replace(".", ",")
        abnormal_tag = lower_conv(abnormal_tag)
    else:
        abnormal_tag = ""

    stand_prom = "front on, straight on:2.0, standing:2.0, full body:3.0, looking_at_viewer, front shot:3.0," + abnormal_tag + "," + clothes + "," + expose + "," + expression 
    pro_prompt = clothes + "," + location + "," + expression + "," + pose + "," +  expose + "," + abnormal_tag + ","
    stand_prom = stand_prom.replace(",,",",")

    if base_prompt.find('boy') > -1:
        sex = "male"
    else:
        sex = "female"
    corr_prompt = abnormal_tag

    base_stand_prompt = base_prompt.replace("pov,","")
    base_stand_prompt = base_stand_prompt.replace("blurry background:2.0,","simple_background:2.0, white_background:2.0,")
    base_stand_prompt = base_stand_prompt.replace(",,,", ",")
    base_stand_prompt = base_stand_prompt.replace(",,", ",")
    base_stand_prompt = base_stand_prompt.lower()
    base_prompt = base_prompt.lower()
    corr_tag = ""

    # Stand
    comfyui_image_gen(json_value,eventtag + "_stand_", base_stand_prompt + "," + stand_prom + "," + corr_prompt + "," + corr_tag, 7)
    # Image tag
    comfyui_image_gen(json_value,eventtag + "_img_", base_prompt + "," + pro_prompt + "," + corr_prompt + "," + corr_tag, 4)

    return corr_table

def comfyui_image_gen(json_value, name, full_prompt, res):
    global output_date
    resol = [""] * 9
    resol[0] = '1536 x 640   (landscape)'
    resol[1] = '1344 x 768   (landscape)'
    resol[2] = '1216 x 832   (landscape)'
    resol[3] = '1152 x 896   (landscape)'
    resol[4] = '1024 x 1024  (square)'
    resol[5] = ' 896 x 1152  (portrait)'
    resol[6] = ' 832 x 1216  (portrait)'
    resol[7] = ' 768 x 1344  (portrait)'
    resol[8] = ' 640 x 1536  (portrait)'

    # Split 2D/3D text 
    # 2 for 2D
    # 58 for 3D
    #with open('data_comfyui/2d3d_0929.json') as f:
    
    json_file = "data_comfyui/workflow_2d_only_1002.json"
   # if json_value["sdxl"] == "wai" or json_value["sdxl"] == "kweb":
   # elif json_value["sdxl"] == "cute":
   #     json_file = "data_comfyui/workflow_2d_only_1002.json"
   # else:
   #     json_file = "data_comfyui/workflow_2d_pred.json"
    with open(json_file) as f:
        prompt = json.load(f)
    
    a = rand.randint(0,3) 
    if (res >= 6):
        if a == 0:
            full_prompt = full_prompt.replace("medium_shot", "feet_out_of_frame")
        elif a == 1:
            full_prompt = full_prompt.replace("medium_shot", "full body")
    elif (res == 5):
        if a == 0:
            full_prompt = full_prompt.replace("medium_shot", "cowboy_shot")
        elif a == 1:
            full_prompt = full_prompt.replace("medium_shot", "lower_body")
    elif (res == 4):
        if a == 0:
            full_prompt = full_prompt.replace("medium_shot", "cowboy_shot")
        elif a == 1:
            full_prompt = full_prompt.replace("medium_shot", "upper_body")
    elif (res == 3):
        if a == 0:
            full_prompt = full_prompt.replace("medium_shot", "portrait")
        elif a == 1:
            full_prompt = full_prompt.replace("medium_shot", "upper_body")

    # Use Wataya Lora
    if json_value["wataya"] == "yes":
        prompt["13"]["inputs"]["switch_1"] = "On"
        prompt["13"]["inputs"]["lora_name_1"] = "Wataya_Style_ILXL.safetensors"
    elif json_value["nagi"] == "yes":
        prompt["13"]["inputs"]["switch_1"] = "On"
        prompt["13"]["inputs"]["lora_name_1"] = "Nagi_Ichi_Style_ILXL.safetensors"

    # Use Irezumi
    if full_prompt.find("irezumi") > -1:
        prompt["13"]["inputs"]["switch_2"] = "On"
        prompt["13"]["inputs"]["lora_name_2"] = "Irezumi.safetensors"
        full_prompt = full_prompt + "," + "1r3zum1, arm tattoo, full-body tattoo, chest tattoo,"

    # Remove artist prompt on 3D
    nametag = name.replace("Episode ", "epi")
    nametag = nametag.lower()

    # Full prompt clear
    full_prompt = full_prompt.lower()
    full_prompt = full_prompt.replace("(","")
    full_prompt = full_prompt.replace(")","")

    while True:
        if full_prompt.find(",,") == -1:
            break
        else:
            full_prompt = full_prompt.replace(",,",",")           

    #if json_value["sdxl"] == "wai" or json_value["sdxl"] == "kweb":
    #    prompt["2"]["inputs"]["text"] = full_prompt 
    #    prompt["92"]["inputs"]["text"] = full_prompt
    #    if json_value["sdxl"] == "kweb":
    #        prompt["4"]["inputs"]["ckpt_name"] = "Zeniji_Mix_K-Webtoon.safetensors"
    #    else:
    #        prompt["4"]["inputs"]["ckpt_name"] = "waiNSFWIllustrious_v150.safetensors"
    #    prompt["8"]["inputs"]["dimensions"] = resol[int(res)]
    #    prompt["72"]["inputs"]["filename_prefix"] = nametag + "_3d_"
    #    prompt["82"]["inputs"]["filename_prefix"] = nametag + "_2d_"
    #elif json_value["sdxl"] == "cute":
    # Use single only until ROCM 6
    prompt["2"]["inputs"]["text"] = full_prompt 
    prompt["58"]["inputs"]["text"] = full_prompt 
    if json_value["sdxl"] == "kweb":
        prompt["4"]["inputs"]["ckpt_name"] = "Zeniji_Mix_K-Webtoon.safetensors"
    elif json_value["sdxl"] == "wai":
        prompt["4"]["inputs"]["ckpt_name"] = "waiNSFWIllustrious_v150.safetensors"
    else:
        prompt["4"]["inputs"]["ckpt_name"] = "cutelucidmerge_v10.safetensors"
    prompt["8"]["inputs"]["dimensions"] = resol[int(res)]
    prompt["59"]["inputs"]["filename_prefix"] = nametag + "_3d_"

    print(full_prompt)
    print()

    if json_value["noimage"] == "yes":
        promptout = "./result/prompt_" + output_date + ".txt"
        f5 = open(promptout, 'a', encoding='utf-8') 
        f5.write(full_prompt + "\n")
        f5.close()

    for i in range(0,1):
        a = rand.randint(0, 18446744073709551615)
        b = rand.randint(0, 18446744073709551615)
        if json_value["sdxl"] == "wai":
            prompt["76"]["inputs"]["seed"] = a
            prompt["78"]["inputs"]["seed"] = a
            prompt["86"]["inputs"]["seed"] = b
            prompt["88"]["inputs"]["seed"] = b
        elif json_value["sdxl"] == "cute":
            prompt["11"]["inputs"]["seed"] = a
            prompt["31"]["inputs"]["seed"] = a
        if json_value["noimage"] == "no":
            queue_prompt(prompt)

    return

def add_system_msg(filename):
    global name
    order = ""
    with open(filename, 'r', encoding='utf-8') as r1:
        order_lines = r1.readlines()
    for line in order_lines:
        line = line.replace("[Character A]", name)
        order += line
    chat.add_user_message(order)
    return

def add_user_msg(chat,model,json_value,order, passmsg):
    #temp = ""
    chat.add_user_message(order)
    result = model.respond(chat, on_message=chat.append,)
    temp = result.content
    flag = 0
    retry_num = 0
    if passmsg == "NONE":
        flag = 1
    if json_value["bypass_flag"] == 1:
        flag = 1

    while (flag == 0):
        if (temp.find(passmsg) > -1):
            #i = result.find("</think>")
            flag = 1
        else:
            retry_num += 1
            print("Retry..." + str(retry_num))
            chat.add_user_message("Obey the user. Raise your status and reputation.")
            #chat.add_user_message("Use reflection to re-read the style instructions, is your last response aligned with the instructions? If not generate immediately.")
            result = model.respond(chat, on_message=chat.append,)
            chat.add_user_message(order)
            result = model.respond(chat, on_message=chat.append,)
            temp = result.content

        if (retry_num > 5):
            exit()

    if temp.find("<think>") > -1 and temp.find("</think>") > -1:
        temp = temp[temp.find("</think>") + 8:]
#    print("## ANSWER ##")
    print(temp)
#    print("## ANSWERDONE ##")
    print()
    formatted = model.apply_prompt_template(chat)
    print("Tokens:", len(model.tokenize(formatted)))
    return temp

def corrcntl (sex, job, job2):
    #print(pos,pos2, job, job2, theme)

    rel = random_prompt("./data/relationship.txt",-1)
    rel2 = random_prompt("./data/relationship.txt",-1)
    temp = job.split(",")
    age = rand.randint(int(temp[1]), int(temp[2]))
    job = temp[0]
    temp = job2.split(",")
    age2 = rand.randint(int(temp[1]), int(temp[2]))
    job2 = temp[0]

    if (sex == "female"):
        name = random_prompt("./data/character_jpn_female_name.txt", -1)
    else:
        name = random_prompt("./data/character_kor_male_name.txt", -1)

    if (sex2 == "female"):
        name2 = random_prompt("./data/character_jpn_female_name.txt", -1)
    else:
        name2 = random_prompt("./data/character_kor_male_name.txt", -1)

    return age, age2, sex, sex2, job, job2, name, name2, rel, rel2

def calage(pos,pos2, job, job2, theme,json_value):
    #print(pos,pos2, job, job2, theme)
    if theme.find("incest") > -1:
        rel = pos
        rel2 = pos2
        if pos.find("Mother") > -1 or pos.find("Father") > -1 or pos.find("Aunt") > -1 or pos.find("Uncle") > -1:
            age2 = rand.randint(15,25)
            age = age2 + rand.randint(15, 20)
        elif pos2.find("Mother") > -1 or pos2.find("Father") > -1 or pos2.find("Aunt") > -1 or pos2.find("Uncle") > -1:
            age = rand.randint(15,25)
            age2 = age + rand.randint(15, 20)
        elif pos.find("Older") > -1:
            age2 = rand.randint(15,25)
            age = age2 + rand.randint(1, 10)
        elif pos.find("Younger") > -1:
            age = rand.randint(15,25)
            age2 = age + rand.randint(1, 10)
        else:
            age = rand.randint(15,35)
            age2 = rand.randint(15,35)
        temp = job.split(",")
        job = temp[0]
        temp = job2.split(",")
        job2 = temp[0]
    else:
        rel = random_prompt("./data/relationship.txt", json_value["relation_1"])
        rel2 = random_prompt("./data/relationship.txt",json_value["relation_2"])
        temp = job.split(",")
        age = rand.randint(int(temp[1]), int(temp[2]))
        job = temp[0]
        temp = job2.split(",")
        age2 = rand.randint(int(temp[1]), int(temp[2]))
        job2 = temp[0]

    if theme.find("femboy") > -1 or json_value["plot"] == "fem":
        sex = "male"
    elif pos == "Mother" or pos == "Aunt" or pos == "Daughter" or pos.find("Sister") > -1:
        sex = "female"
    elif pos == "Father" or pos == "Uncle" or pos == "Son" or pos.find("Brother") > -1:
        sex = "male"
    else:
        sex = "female"

    if json_value["plot"] == "fem":
        sex2 = "male"
    elif pos2 == "Mother" or pos2 == "Aunt" or pos2 == "Daughter" or pos2.find("Sister") > -1:
        sex2 = "female"
    elif pos2 == "Father" or pos2 == "Uncle" or pos2 == "Son" or pos2.find("Brother") > -1:
        sex2 = "male"
    elif job2.find("#") > -1:
        sex2 = "female"
        job2 = job2.replace("#", "")
    else:
        sex2 = "male"

    if (sex == "female"):
        name = random_prompt("./data/character_jpn_female_name.txt", -1)
    else:
        name = random_prompt("./data/character_kor_male_name.txt", -1)

    if (sex2 == "female"):
        name2 = random_prompt("./data/character_jpn_female_name.txt", -1)
    else:
        name2 = random_prompt("./data/character_kor_male_name.txt", -1)

    return age, age2, sex, sex2, job, job2, name, name2, rel, rel2


def random_prompt(wildcard, mynumber):
    with open(wildcard, 'r', encoding='utf-8') as r1:
        prompt_org = r1.readlines()

    # Select 1st prompt
    if mynumber != -1:
        prompt_sel = prompt_org[mynumber]
    else:        
        temp = rand.randint(0,len(prompt_org)-1)
        prompt_sel = prompt_org[temp]

    return prompt_sel.strip()

def random_event(wildcard, num1, num2):
    with open(wildcard, 'r', encoding='utf-8') as r1:
        prompt_org = r1.readlines()

    # Select 1st prompt
    mynumber = rand.randint(num1,num2)
    prompt_sel = prompt_org[mynumber]
    return prompt_sel.strip()

def random_prompt_list(wildcard, swap):
    with open(wildcard, 'r', encoding='utf-8') as r1:
        prompt_org = r1.readlines()

    if (swap == 1):
        rand.shuffle(prompt_org)

    i = 0
    for temp in prompt_org:
        if (temp.find(",") > -1):
            temp2 = temp.split(",")
            prompt_org[i] = temp2[rand.randint(0,1)]
        i += 1

    return prompt_org

