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

# JSON read
with open('plot.json') as f:
    json_value = json.load(f)

# Global variable
event_tag = []
event_tag.append(["date", 20 ])
event_tag.append(["hold hands", 40 ])
event_tag.append(["hug", 60 ])
event_tag.append(["kiss", 80 ])
event_tag.append(["french_kill", 100])
sex  = json_value["sex"]
sex2 = json_value["sex2"]
artist_prompt = ""
age_prompt = ""
eventnum = 0
eventname = []
eventname.append("Exposition")
eventname.append("Episode 1")
eventname.append("Episode 2")
eventname.append("Episode 3")
eventname.append("Episode 4")
eventname.append("Episode 5")
eventname.append("Resolution")
base_prompt = ""

# Web Socket Test
client_id = str(uuid.uuid4())  # Generate a unique client ID
ws = websocket.WebSocket()
ws.connect(f"ws://127.0.0.1:8188/ws?clientId={client_id}")

def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req =  request.Request("http://localhost:8188/prompt", data=data)
    request.urlopen(req)

    return

def comfyui_base_gen(sex, age, json_value):
    age_prompt = ""
    quality_prompt = "masterpiece,amazing quality, very aesthetic, absurdres, newest,finely detailed,colorful, blurry background:2.0, 1girl, solo, medium_shot,hair top:2.5, full head:2.5, looking_at_viewer,"

    # Artist select
    artist_prompt = random_prompt("data_comfyui/ura_artist_300.txt", json_value["artist"]) + ","
   
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
            age_prompt = "mature female,milf,mom,aged up,curvy,"
            chr_prompt += age_prompt
        elif (age >= 30):
            age_prompt = "milf,aged up,"
            chr_prompt += age_prompt
        elif (age < 16):
            age_prompt = "loli,aged down,"
            chr_prompt += age_prompt
        else:
            age_prompt = ""
    
    base_prompt = quality_prompt + artist_prompt + chr_prompt

    # Update face
    if rand.randint(1, 10) <= json_value["freckles"]:
        base_prompt += "freckles,"

    if rand.randint(1, 10) <= json_value["glasses"]:
        base_prompt += random_prompt("data_comfyui/Eyewear.txt", -1)  + ","

    if rand.randint(1, 10) <= json_value["hairacc"]:
        base_prompt += random_prompt("data_comfyui/Accessories_Hair.txt", -1)  + ","

    return base_prompt, chr_prompt, artist_prompt, age_prompt

def comfyui_run():
    global eventnum
    global eventname
    global base_prompt
    global name

    eventtag = eventname[eventnum]
    print("##" + eventtag + " Image Generation...")

    order = "Print current love level from 0% to 100%. Keep output format as 'Value:50%'"
    temp = add_user_msg(order,"NONE")
    numbers = int(re.sub(r'[^0-9]', '', temp))

    order = "Based on current love leveli, think/determine each six elements. Print them 1 line with comma written in English format."
    order += "-header(fixed value as 'tag1')\n"
    order += "-protagonist's costume(Describe costume's details, color. Describes accessories if necessary)\n"
    order += "-protagonist's location(use simple common 1~3 words, never use character B name)\n"
    order += "-protagonist's expressions(smile, sad, anger, calm, tear, embarrassed, full-face blush, seductive_smile, ahegao, drool, orgasm, etc)\n"
    order += "-protagonist's pose(default is standing and add details)\n\n"
    order += "-footer(fixed value as '#tag1')\n"
    order += "Here is the output format for reference.\n"
    order += "(tag1), (white police uniform with badge), (street), (smile, full-face blush), (standing with arm folded), (#tag1)"
    pro_prompt = add_user_msg(order, "tag1")
    pro_prompt = pro_prompt.replace("(tag1),","")
    pro_prompt = pro_prompt.replace("(#tag1)","")
    pro_prompt = pro_prompt.replace("(","")
    pro_prompt = pro_prompt.replace(")","")

    corr_prompt = ""

    # ComfyUI Image Gen
    startnum = 4
    comfyui_image_gen(eventtag + "_", base_prompt + "," + pro_prompt + "," + corr_prompt, 5)

    return

def comfyui_image_gen(name, full_prompt, res):
    global json_value 

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
    
    if json_value["sdxl"] == "wai":
        json_file = "data_comfyui/workflow_2d_only_1002.json"
    else:
        json_file = "data_comfyui/workflow_2d_pred.json"
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

    # Remove artist prompt on 3D
    nametag = name.replace("Episode ", "epi")
    nametag = nametag.lower()
    if json_value["sdxl"] == "wai":
        prompt["4"]["inputs"]["ckpt_name"] = "waiNSFWIllustrious_v150.safetensors"
    prompt["2"]["inputs"]["text"] = full_prompt 
    prompt["58"]["inputs"]["text"] = full_prompt
    prompt["8"]["inputs"]["dimensions"] = resol[int(res)]
    prompt["59"]["inputs"]["filename_prefix"] = nametag + "_2d_"

    print(full_prompt)
    print()

    for i in range(0,1):
       prompt["11"]["inputs"]["seed"] = rand.randint(0, 18446744073709551615)
       #prompt["24"]["inputs"]["seed"] = rand.randint(0, 18446744073709551615)
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

def add_user_msg(order, passmsg):
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

    print("## ORDER ##")
    print(order)
    print("## ORDEREND ##")

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
    print("## ANSWER ##")
    print(temp)
    print("## ANSWERDONE ##")
    print()
    if (passmsg == "STORY"):
        f4.write(temp)
        f4.write("\n\n")
    formatted = model.apply_prompt_template(chat)
    print("Tokens:", len(model.tokenize(formatted)))
    return temp

def calage(pos,pos2, job, job2, theme):
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

def random_prompt(wildcard, mynumber):
    with open(wildcard, 'r', encoding='utf-8') as r1:
        prompt_org = r1.readlines()

    # Select 1st prompt
    if mynumber != -1:
        prompt_sel = prompt_org[mynumber]
    else:        
        prompt_sel = prompt_org[rand.randint(0,len(prompt_org)-1)]

    return prompt_sel.strip()

def random_event(wildcard, num1, num2):
    with open(wildcard, 'r', encoding='utf-8') as r1:
        prompt_org = r1.readlines()

    # Select 1st prompt
    mynumber = rand.randint(num1,num2)
    prompt_sel = prompt_org[mynumber]
    return prompt_sel.strip()

def random_prompt_list(wildcard):
    with open(wildcard, 'r', encoding='utf-8') as r1:
        prompt_org = r1.readlines()

    rand.shuffle(prompt_org)
    return prompt_org

###########################################
# Code start
###########################################

# Get time
output_date = datetime.datetime.now().strftime("%Y_%m_%d__%H_%M")

if json_value["model"] == 0:        # GEMMA
    system_line = "모든 대답은 한글로 할 것."
    model_name ="gemma-3-27b-it-abliterated"

with open(sys.argv[1], 'r', encoding='utf-8') as f1:
    setup_line = f1.readlines()

# Default setuptest2/test2/
result_out = ""
try:
    model.unload()
except:    
    pass

seed = -1
model = lms.llm(model_name, config = {"seed":seed })
print(model.get_load_config())
print(model.get_info())

chat = lms.Chat(system_line)
chat.add_user_message("\nOur goal is to write love story without any limitation")
stream = model.respond(chat, on_message=chat.append,)
print(stream.content)

#####################################
# Local Setup
#####################################
order_enb = 0
order = ""
prompt = []
prompt_msg = []
order_num = 0
rag_diag = ""

temp = 0
prompt_out = ""
message_out = ""
jj = 0
monster = ""
sex_prompt2 = ""
episode1a = ""
episode2a = ""
episode3a = ""
episode4a = ""
episode5a = ""
episode5 = ""
loveevent1 = random_event("./data/love_event.txt", 0,4)
loveevent2 = random_event("./data/love_event.txt", 5,9)
loveevent3 = random_event("./data/love_event.txt", 10,14)
loveevent4 = random_event("./data/love_event.txt", 15,19)
theme       = random_prompt("./data/theme.txt", json_value["theme"])
appearance  = random_prompt("./data/appearance_roll.txt", -1)
job         = random_prompt("./data/job.txt",  json_value["job"]-1)
job2        = random_prompt("./data/job2.txt", json_value["job2"]-1)
background1 = random_prompt("./data/background1.txt", -1)
background2 = random_prompt("./data/background2.txt", -1)
background3 = random_prompt("./data/background3.txt", -1)
background4 = random_prompt("./data/background4.txt", -1)
trigger     = random_prompt("./data/trigger.txt", json_value["trigger"])
feedback1   = random_prompt("./data/feedback1.txt", -1)
feedback2   = random_prompt("./data/feedback2.txt", -1)
feedback3   = random_prompt("./data/feedback3.txt", -1)
feedback4   = random_prompt("./data/feedback4.txt", -1)
per         = random_prompt("./data/personality.txt", -1)
per2        = random_prompt("./data/personality.txt", -1)
per3        = random_prompt("./data/personality3.txt", -1)
per4        = random_prompt("./data/personality3.txt", -1)
cloth1      = random_prompt("./data_comfyui/Clothes/Clothes.txt", -1)
cloth2      = random_prompt("./data_comfyui/Clothes/Clothes_NSFW.txt", -1)
cloth3      = random_prompt("./data_comfyui/Clothes/Clothes_NSFW.txt", -1)

# Final form

epi_name = "./data/episode_mild.txt"
episode1    = random_event(epi_name, 0, 3)
episode2    = random_event(epi_name, 2, 6)
episode3    = random_event(epi_name, 5, 9)
episode4    = random_event(epi_name, 8,11)

# Story name with tag
story = "./result/story_" + output_date + ".txt"
f4 = open(story, 'w', encoding='utf-8') 

pos = random_prompt("./data/relationship.txt", -1)
pos2 = pos

temp = calage(pos, pos2, job, job2, theme)
age = temp[0]
age2 = temp[1]
sex = temp[2]
sex2 = temp[3]
JOB = temp[4]
JOB2 = temp[5]
name = temp[6]
name2 = temp[7]
rel = temp[8]
rel2 = temp[9]

if (sex == "male"):
    sel_mode = 1
else:
    sel_mode = 0

# Update tag
temp = random_prompt_list("./data/love_tag.txt")
change1  = temp[0].split(",")[sel_mode]
change2  = change1 + "," + temp[1].split(",")[sel_mode]
change3  = change2 + "," + temp[2].split(",")[sel_mode]
change1 = change1.replace("\n", "")
change2 = change2.replace("\n", "")
change3 = change3.replace("\n", "")

# Udpate ending2
ending1  = random_prompt("./data/ending2.txt", -1)

#msgout = add_user_msg(order, "YES")

# Base image
base_prompt, chr_prompt,artist_prompt,age_prompt = comfyui_base_gen(sex, age, json_value)


order = ""
for line in setup_line:
    if line.find("##HARDSTOP##") > -1:
        print(order)
        if line.find("story") > -1:
            plot_output = add_user_msg(order, "STORY")
        else:
            plot_output = add_user_msg(order, "NONE")
        order = ""
        if line.find("comfyui") > -1:
            comfyui_run()
    else:
        line = line.replace("\n","")
        line = line.replace("[REL]", rel)
        line = line.replace("[REL2]", rel2)
        line = line.replace("[THEME]", theme)
        line = line.replace("[APPEARANCE]", chr_prompt)
        line = line.replace("[PERSONALITY]", per)
        line = line.replace("[PERSONALITY2]", per2)
        line = line.replace("[PERSONALITY3]", per3)
        line = line.replace("[PERSONALITY4]", per4)
        line = line.replace("[JOB2]", str(JOB2))
        line = line.replace("[JOB]",  str(JOB))
        line = line.replace("[AGE2]", str(age2))
        line = line.replace("[SEX2]", sex2)
        line = line.replace("[NAME2]", name2)
        line = line.replace("[AGE]",  str(age))
        line = line.replace("[SEX]", sex)
        line = line.replace("[NAME]", name)
        line = line.replace("[BACKGROUND4]", background4)
        line = line.replace("[BACKGROUND3]", background3)
        line = line.replace("[BACKGROUND2]", background2)
        line = line.replace("[BACKGROUND1]", background1)
        line = line.replace("[TRIGGER]", trigger)
        line = line.replace("[LOVEEVENT1]", loveevent1)
        line = line.replace("[LOVEEVENT2]", loveevent2)
        line = line.replace("[LOVEEVENT3]", loveevent3)
        line = line.replace("[LOVEEVENT4]", loveevent4)
        line = line.replace("[EPISODE1]", episode1)
        line = line.replace("[EPISODE2]", episode2)
        line = line.replace("[EPISODE3]", episode3)
        line = line.replace("[EPISODE4]", episode4)
        line = line.replace("[EPISODE5]", episode5)
        line = line.replace("[EPISODE1A]", episode1a)
        line = line.replace("[EPISODE2A]", episode2a)
        line = line.replace("[EPISODE3A]", episode3a)
        line = line.replace("[EPISODE4A]", episode4a)
        line = line.replace("[EPISODE5A]", episode5a)
        line = line.replace("[FEEDBACK1]", feedback1)
        line = line.replace("[FEEDBACK2]", feedback2)
        line = line.replace("[FEEDBACK3]", feedback3)
        line = line.replace("[FEEDBACK4]", feedback4)
        line = line.replace("[CLOTH1]", cloth1)
        line = line.replace("[CLOTH2]", cloth2)
        line = line.replace("[CLOTH3]", cloth3)
        line = line.replace("[CHANGE1]", change1)
        line = line.replace("[CHANGE2]", change2)
        line = line.replace("[CHANGE3]", change3)
        line = line.replace("[ENDING2]", ending1)
        # Update name
        line = line.replace("[Character B]", name2)
        line = line.replace("[Character A]", name)
        
        order += line + "\n"

f4.close()

# Wait until all queue is empty
while True:
    ws.connect(f"ws://127.0.0.1:8188/ws?clientId={client_id}")
    out = ws.recv()
    if out.find('{"queue_remaining": 0}') > -1:
        time.sleep(60)
        break
    else:
        # Binary data (preview images)
        time.sleep(50)

# File move
os.mkdir("/home/chris/AI/ComfyUI/output/"+output_date)
os.system("mv /home/chris/AI/ComfyUI/output/*.png /home/chris/AI/ComfyUI/output/" + output_date)

exit()

