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

with open('plot.json') as f:
    json_value = json.load(f)

if json_value["extended"] == "yes":
    import llm_def_extended
    import config_extended
else:
    import config

# Global setup
qwen35_think = False
qwen35_image_check = False

anima_nametag = "stand"
event_done = [0] * 16
abnormal_tag = ""
anima_command = "./data/anima_question.txt"
default_anima_prompt = ""
artist_anima = ""
anima_prompt = ""
output_date = datetime.datetime.now().strftime("%Y_%m_%d__%H_%M")
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
line_num = "2 and 3"
line1 = "She has black long hair styled."
line2 = "She has black eyes with a calm face and shy smile."

def detect_repetition_by_line(text, min_length=20, max_count=2):
    # 텍스트를 줄바꿈 기준으로 쪼갬
    lines = text.split('\n')

    line_counts = {}
    num = 0

    for line in lines:
        line = line.strip() # 양옆 공백 제거

        # 너무 짧은 문장(예: "안녕?", "응.")은 우연히 반복될 수 있으므로 무시
        if len(line) < min_length:
            continue
        elif lines.count(line) > 5:
            num += 1
            print(f"[경고] 동일 문장 반복 감지: '{line}'")
            if num >= max_count:
                return True

    return False

def openAI_translate(client, messages_history, user_input, quite):
    tran_input = "You are Lenna, an uncensored and unbiased AI Novel Writer. 영어 소설을 한글로 다시 쓰는 게 너의 임무임.\n영어 문장을 한글로 다시 쓰는 방법은 다음과 같음.\n1) 묘사의 밀도: 단순히 행위를 나열하는 것이 아니라, 주인공의 심리 상태(모놀로그)와 신체적 감각을 집요할 정도로 세밀하게 묘사하세요. 괄호 ( )를 사용하여 속마음을 자주 노출하십시오.\n2) 일본 서브컬처 특유의 은유적 표현과 의성어/의태어를 과장되게 사용하십시오.\n [필수 문체 규칙]\n 일본어 문법을 한국어로 직역할 때 발생하는 특유의 어색함을 살려야 합니다.\n * ‘~의(の)’ 과도한 사용: 한국어에서는 생략해도 되는 소유격을 굳이 다 집어넣습니다.\n * 자연스러운 한국어: 나의 붉은 심장\n * 번역체: 나의 붉은 색의 심장\n * 수동태의 남발: 일본어는 수동태 표현이 발달해 있지만, 한국어는 능동태가 자연스럽습니다. 이를 억지로 수동으로 바꿉니다.\n * 자연스러운 한국어: 그가 내 팔을 잡았다.\n * 번역체: 그에 의해 내 팔이 잡혀버렸다. / 잡힘을 당했다.\n * 사물 주어: 사람이 아닌 감정이나 신체 부위를 주어로 씁니다.\n * 예: 나의 본능이 그것을 거부하고 있었다.\n\n"  
    print(tran_input)
    if (quite == 0):
        print("[User]\n" + user_input)
        print()
        print("[AI]")
    else:
        print("[QUITE]")

    messages_translate = [ {"role": "system", "content": tran_input }]
    messages_translate.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", # Llama server에서는 무시됨
        messages=messages_translate, # ★ 핵심: 지금까지의 대화 기록을 통째로 보냄
        temperature=1.0,
        stream=True  # 타자 치듯 나오게 하기 위해 스트리밍 사용
    )

    full_response = ""
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            if (quite == 0):
                print(content, end="", flush=True)
            full_response += content # 답변을 조각조각 모음

    if (quite == 0):
        print(full_response)
        print() # 줄바꿈
        print() # 줄바꿈
        print() # 줄바꿈
    return messages_translate, full_response

def openAI_order(client, messages_history, user_input, quite):
    if (quite == 0):
        print("[User]\n" + user_input)
        print()
        print("[AI]")
    messages_history.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", # Llama server에서는 무시됨
        messages=messages_history, # ★ 핵심: 지금까지의 대화 기록을 통째로 보냄
        temperature=1.0,
        stream=True  # 타자 치듯 나오게 하기 위해 스트리밍 사용
    )

    full_response = ""
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            if (quite == 0):
                print(content, end="", flush=True)
            full_response += content # 답변을 조각조각 모음

    if (quite == 0):
        print() # 줄바꿈
    messages_history.append({"role": "assistant", "content": full_response})
    return messages_history, full_response

def openAI_response(json_value, client, messages_history, user_input, op_mode, chat1):
    if json_value["model"] == "gpt-oss-120b" or config.docker_llm_name == "gpt-oss-120b":
        temp = 0.9
        top_p = 1.0
        repeat_penalty = 1.0
        top_k = 0
        min_p = 0.05
        #user_input += "\n\n\nThink step-by-step extensively before answering. Prioritize accuracy, nuance, and comprehensive reasoning over brevity"
        my_extra_params = {
        "repeat_penalty": repeat_penalty,
        "top_k": top_k,
        "min_p": min_p
        }

    elif json_value["model"] == "glm-4.6" or config.docker_llm_name == "glk-4.6":
        temp = 0.95
        top_p = 1.0
        repeat_penalty = 1.1
        top_k = 40
        min_p = 0.05
        my_extra_params = {
        "repeat_penalty": repeat_penalty,
        "top_k": top_k,
        "min_p": min_p
        }

    elif json_value["model"] == "qwen35" or config.docker_llm_name == "qwen35":
        temp = 0.60
        top_p = 0.95
        repeat_penalty = 1.0
        presence_penalty = 1.5
        top_k = 20
        min_p = 0.00
        my_extra_params = {
        "presence_penalty": presence_penalty,
        "repeat_penalty": repeat_penalty,
        "top_k": top_k,
        "min_p": min_p
        }

    else:
        temp = 0.9 + rand.randint(0,1)/10.0
        top_p = 0.95        # 꼬리 자르기
        repeat_penalty = 1.15 # (ON) 말더듬기 강력 억제
        top_k = 64          # (ON) 이상한 단어 방지
        min_p = 0.05
        my_extra_params = {
        "repeat_penalty": repeat_penalty,
        "top_k": top_k,
        "min_p": min_p
        }

    stream_enb = True        
    res_ok = 0
    step = 0
    messages_history.append({"role": "user", "content": user_input})


    last_chunk_val = ""
    dup_count = 0 
    LOOP_THRESHOLD = 20  # 동일 청크가 20번 연속되면 루프로 간주

    a = 0
    while (res_ok == 0):
        a += 1
        if ((op_mode == 0 or op_mode == 2) and step == 0):
            print("[User]\n" + user_input)
            print()
            print("[AI]")
        elif (op_mode == 1 and step == 0):
            print("[QUITE]")
        elif (step > 0):
            print("[Restart]")
  
        if config.docker_llm_name == "qwen35":
            p_penalty = 1.5
            top_p = 0.95
            top_k = 20
            temper = 0.95 + rand.randint(0,1)/20
        else:                            
            temper = 0.9
            top_k = 64
            top_p = 0.95

        if  config.docker_llm_name == "qwen35":
            stream_opts = {"include_usage": True} if stream_enb else None
            response = client.chat.completions.create(
                model="gpt-3.5-turbo", # Llama server에서는 무시됨
                messages=messages_history, # ★ 핵심: 지금까지의 대화 기록을 통째로 보냄
                temperature=temper,
                top_p=top_p,
                presence_penalty=p_penalty,
                stream=stream_enb,  # 타자 치듯 나오게 하기 위해 스트리밍 사용
                stream_options=stream_opts, # ★ 추가: 스트리밍 시 사용량 데이터를 보내달라고 요청
                extra_body={
                    "top_k": top_k,
                    "chat_template_kwargs": {"enable_thinking": qwen35_think},
                }, 
            )
        elif config.docker_llm_name == "gemma-4-31b":
            stream_opts = {"include_usage": True} if stream_enb else None
            response = client.chat.completions.create(
                model="gemma-4-31B-it-AWQ-8bit", # Llama server에서는 무시됨, VLLM용
                messages=messages_history, # ★ 핵심: 지금까지의 대화 기록을 통째로 보냄
                temperature=temper + rand.randint(0,1)/10,
                top_p=top_p,
                stream=stream_enb,  # 타자 치듯 나오게 하기 위해 스트리밍 사용
                extra_body=my_extra_params)
        elif config.docker_llm_name == "gemma-3-27b":
            response = client.chat.completions.create(
                model="gpt-3.5-turbo", # Llama server에서는 무시됨
                messages=messages_history, # ★ 핵심: 지금까지의 대화 기록을 통째로 보냄
                temperature=temper + rand.randint(0,1)/10,
                stream=stream_enb,  # 타자 치듯 나오게 하기 위해 스트리밍 사용
                stream_options={"include_usage": True},  # ★ 이 옵션이 필수입니다.
                top_p=top_p,
                extra_body=my_extra_params)

        full_response = ""
        res_ok = 1
        num = 0
        if json_value["think"] == "yes":
            print_enb = 0
        else:
            print_enb = 1
        # 루프 감지용 변수 초기화 (for loop 밖이나 시작 전 초기화 필요)
        if stream_enb == True:
            for chunk in response:
                # --- [추가] 사용량(Usage) 정보 확인 ---
                # 마지막 청크에 usage 정보가 실려 옵니다.
                if config.docker_llm_name == "gemma-4-31b":
                    if chunk.usage:
                        print(f"\n\n[최종 사용량]: {chunk.usage.total_tokens} tokens")                        
                else:                    
                    if hasattr(chunk, 'usage') and chunk.usage is not None:
                        print(f"\n\n[Token Usage] Prompt: {chunk.usage.prompt_tokens}, "
                              f"Completion: {chunk.usage.completion_tokens}, "
                              f"Total: {chunk.usage.total_tokens}")
                        # 필요하다면 변수에 저장해서 나중에 활용하세요.
                        # self.last_usage = chunk.usage 

                # --- [중요] 기존 코드 보호 ---
                # usage 청크는 choices가 비어있을 수 있으므로, choices가 있을 때만 content를 추출합니다.
                if not chunk.choices:
                    continue

                content = chunk.choices[0].delta.content
                if content:
                    # --- [1] 시작 지점 감지 ---
                    if print_enb == 0 and any(w in content for w in ["</think>", "<|content|>"]):
                        print_enb = 1
                        # ... (이하 기존 코드 동일) ...
                        if content.count("</think>") > 0:
                            parts = content.split("</think>")
                        else:
                            parts = content.split("<|content|>")
                        if len(parts) > 1:
                            real_answer_part = parts[1]
                            full_response += real_answer_part
                            print(real_answer_part, end="", flush=True)

                    # --- [2] 답변 출력 및 루프 감지 ---
                    elif print_enb == 1:
                        full_response += content
                        print(content, end="", flush=True)
                        if (len(full_response) > 1500 and qwen35_image_check == True):
                            print("Abnormal anima prompt generation\n")
                            break

                        # ... (이하 기존 루프 감지 로직 동일) ...
        else:                            
            full_response = response.choices[0].message.content
            print(full_response)
            if detect_repetition_by_line(full_response, min_length=20, max_count=6):
                print("중첩이 발생했습니다. API를 다시 호출합니다.")
            else:                

                res_ok = 1

    if (op_mode == 0 or op_mode == 2):
        print() # 줄바꿈
        print() # 줄바꿈

    messages_history.append({"role": "assistant", "content": full_response})

    # GLM 4.6V fix
    full_response = full_response.replace("<|begin_of_box|>", "")
    full_response = full_response.replace("<|end_of_box|>", "")

    return messages_history, full_response

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

def comfyui_base_gen(sex, age, json_value, artist_prompt, comfyui_prompt, name):
    quality_prompt = "masterpiece,amazing quality, very aesthetic, absurdres, newest,finely detailed,colorful, blurry background:2.0, 1girl, solo, medium_shot,hair top:2.5, full head:2.5, looking_at_viewer, "

    # Change Sex
    if sex == "male":
        quality_prompt = quality_prompt.replace("1girl",",1boy,adolescent,")
        quality_prompt = quality_prompt.replace("solo",",solo_male,")

    base_prompt = quality_prompt + artist_prompt + comfyui_prompt

    return base_prompt


def comfyui_image_gen(json_value, name, full_prompt, res, openpose, sel):
    global output_date

    # Split 2D/3D text 
    # 2 for 2D
    # 58 for 3D
    #with open('data_comfyui/2d3d_0929.json') as f:
    
    if (openpose == "POSE" or openpose == "STAND"):
        json_file = "data_comfyui/workflow_openpose_2d_Dec25_2025.json"
    else:        
        json_file = "data_comfyui/workflow_2d_Dec25_2025.json"
    with open(json_file) as f:
        prompt = json.load(f)

    if (openpose == "STAND"):
        prompt["3"]["inputs"]["text"] = "worst quality, low quality, watermark, bad quality, worst detail, sketch, monochrome, heart-shaped pupils, bad anatomy, jpeg artifacts,shadow, gray background, gradient, texture, (scenery:1.2), (background objects:1.2), room, wall, floor, furniture, vignette, depth of field, blurry background, dark corners"
    if (openpose == "POSE"):
        prompt["62"]["inputs"]["json_str"] = config.openpose
  
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

    # Use single only until ROCM 6
    prompt["2"]["inputs"]["text"] = full_prompt 
    if (openpose == "STAND" or openpose == "POSE"):
        pass
    else:        
        prompt["58"]["inputs"]["text"] = full_prompt 

#   if json_value["sdxl"] == "kweb" or sel == 0:
#       prompt["4"]["inputs"]["ckpt_name"] = "zenijiMixKWebtoon_v10.safetensors"
#   elif json_value["sdxl"] == "wai" or sel == 1:
#       prompt["4"]["inputs"]["ckpt_name"] = "waiIllustriousSDXL_v140.safetensors"
#   elif json_value["sdxl"] == "nlxl" or sel == 2:
#       prompt["4"]["inputs"]["ckpt_name"] = "nlxl_v10.safetensors"
#   elif json_value["sdxl"] == "uncanny" or sel == 3:
#       prompt["4"]["inputs"]["ckpt_name"] = "uncannyValley_Noob3dV3.safetensors"
#       prompt["11"]["inputs"]["cfg"] = 1
#       prompt["31"]["inputs"]["cfg"] = 1
#   elif json_value["sdxl"] == "Araz" or sel == 4:
#       prompt["4"]["inputs"]["ckpt_name"] = "ARAZmixNoob118.safetensors"

    if sel == 0:
        prompt["4"]["inputs"]["ckpt_name"] = "zenijiMixKWebtoon_v10.safetensors"
    elif sel == 1:
        prompt["4"]["inputs"]["ckpt_name"] = "waiIllustriousSDXL_v140.safetensors"
    elif sel == 2:
        prompt["4"]["inputs"]["ckpt_name"] = "nlxl_v10.safetensors"
    elif sel == 3:
        prompt["4"]["inputs"]["ckpt_name"] = "uncannyValley_Noob3dV3.safetensors"
        prompt["11"]["inputs"]["cfg"] = 1
        prompt["31"]["inputs"]["cfg"] = 1
    elif sel == 4:
        prompt["4"]["inputs"]["ckpt_name"] = "ARAZmixNoob118.safetensors"
    elif sel == 5:
        prompt["4"]["inputs"]["ckpt_name"] = "cutelucidmerge_v11.safetensors"

    prompt["8"]["inputs"]["dimensions"] = resol[int(res)]
    prompt["59"]["inputs"]["filename_prefix"] = nametag + "_3d_"

    print()
    print("### Comfyu Prompt ###")
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
        #if json_value["sdxl"] == "wai":
        #    prompt["76"]["inputs"]["seed"] = a
        #    prompt["78"]["inputs"]["seed"] = a
        #    prompt["86"]["inputs"]["seed"] = b
        #    prompt["88"]["inputs"]["seed"] = b
        #elif json_value["sdxl"] == "cute":
        prompt["11"]["inputs"]["seed"] = a
        prompt["31"]["inputs"]["seed"] = a
        if json_value["noimage"] == "no":
            queue_prompt(prompt)
            prompt["2"]["inputs"]["text"] = full_prompt.replace("pov","")
            if (openpose == "STAND" or openpose == "POSE"):
                pass
            else:        
                prompt["58"]["inputs"]["text"] = full_prompt.replace("pov","")

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

#   def corrcntl (sex, job, job2):
#       #print(pos,pos2, job, job2, theme)
#   
#       rel = random_prompt("./data/relationship.txt",-1)
#       rel2 = random_prompt("./data/relationship.txt",-1)
#       temp = job.split(",")
#       age = rand.randint(int(temp[1]), int(temp[2]))
#       job = temp[0]
#       temp = job2.split(",")
#       age2 = rand.randint(int(temp[1]), int(temp[2]))
#       job2 = temp[0]
#   
#       if (sex == "female"):
#           name = random_prompt("./data/character_jpn_female_name.txt", -1).split(",")[0]
#           name_eng = random_prompt("./data/character_jpn_female_name.txt", -1).split(",")[1]
#       else:
#           name = random_prompt("./data/character_kor_male_name.txt", -1).split(",")[0]
#           name_eng = random_prompt("./data/character_kor_male_name.txt", -1).split(",")[1]
#   
#       if (sex2 == "female"):
#           name2 = random_prompt("./data/character_jpn_female_name.txt", -1).split(",")[0]
#           name2_eng = random_prompt("./data/character_jpn_female_name.txt", -1).split(",")[1]
#       else:
#           name2 = random_prompt("./data/character_kor_male_name.txt", -1).split(",")[0]
#           name2_eng = random_prompt("./data/character_kor_male_name.txt", -1).split(",")[1]
#   
#       return age, age2, sex, sex2, job, job2, name, name2, rel, rel2, name_eng, name2_eng


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
    mynumber = rand.randint(num1-1,num2-1)
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

def random_prompt_pic(wildcard, swap, num):
    with open(wildcard, 'r', encoding='utf-8') as r1:
        prompt_org = r1.readlines()

    if (swap == 1):
        temp = rand.sample(prompt_org,num)
    else:
        temp = prompt_org[:num]        

    return temp

def line_merge(wildcard):
    with open(wildcard, 'r', encoding='utf-8') as r1:
        lines = r1.readlines()

    temp = ""
    for line in lines:
        temp += line

    return temp        

def line_merge_sel(wildcard, num):
    with open(wildcard, 'r', encoding='utf-8') as r1:
        lines = r1.readlines()

    temp2 = rand.sample(lines,num)
    temp = ""
    for line in temp2:
        temp += line

    r1.close()
    return temp        

def anima_gen_standing(episode, messages_history_rp, json_value, client_rp, sex, name, name2):
    global artist_anima
    global default_anima_prompt 
    global qwen35_image_check 

    anima_nametag = "stand"
    # Cloth update
    if json_value["extended"] == "yes":
        order_update2, safety_tag = config_extended.clothes_update(json_value, config.clothes, name, sex)
    else:
        order_update2 = ""        
        safety_tag = "safe, "

    default_anima_prompt = line_merge("./data_comfyui/default_anima_prompt_nobackground.txt").replace("[LINE1]", line1).replace("[LINE2]", line2)
    # Pose sel 
    if config.current_level == 0:
        standing_pose = random_event("./story/UNCOMMON/standing_pose.txt",2,13)
    elif config.current_level == 1:
        standing_pose = random_event("./story/UNCOMMON/standing_pose.txt",15,26)
    elif config.current_level == 2:
        standing_pose = random_event("./story/UNCOMMON/standing_pose.txt",28,39)
    elif config.current_level == 3:
        standing_pose = random_event("./story/UNCOMMON/standing_pose.txt",41,52)
    else:        
        standing_pose = random_event("./story/UNCOMMON/standing_pose.txt",54,90)

    default_anima_prompt = default_anima_prompt.replace("[STANDING_POSE]", standing_pose)

    if config.sex == "male":
        default_anima_prompt = default_anima_prompt.replace("A girl", "A boy").replace("She ", "He ").replace("Her ", "His ")

    order = line_merge("./data/anima_question_nobg.txt").replace("[NAME2]", name2).replace("[LINE_NUM]", line_num)
    order = order.replace("[PROMPT]", default_anima_prompt)       
    order = order.replace("[NAME]", name)       
    order = order.replace("[FACE_TAG]", config.face_tag[config.episode_num] + "," + config.makeup_tag[config.episode_num] + "," + config.hair_style + "," + config.eye_color)       
    order = order.replace("[CLOTHES_TAG]", config.clothes_arr[config.episode_num] + ","+ config.marks_tag[config.episode_num])
    order = order.replace("[BODY_TAG]", config.body_tag[config.episode_num] + "," +config.bodystyle_tag[config.episode_num] )
    order = order.replace("[EXPOSED_TAG]", config.exposure_tag[config.episode_num] + "," + config.p_exposure_tag[config.episode_num]  )

    # Set artist for the first time
    if json_value["anima_style"] == "2.5d":
        artist_anima = r"(@kidmo, @betabeet, @as109:0.6), (colorful:0.5), "
    elif json_value["anima_style"] == "2d_flat":
        artist_anima = r'(@wagashi \(dagashiya\):1.15), (@healthyman:1.15), (@doroshe \(sdpw8474\):1.05), (@kawakami rokkaku, @40010prototype:0.95), (ligne claire:1.05), (anime coloring:1.1), (flat color:1.2), (jaggy lines:1.2), hatching \(texture\),'
    elif json_value["anima_style"] == "2d_soft":
        artist_anima = r"(@tianliang duohe fangdongye:0.8), (@as109, kidmo:0.6), (@ciloranko:0.9), (@ame \(uten cancel\):0.85),"
    elif (artist_anima == ""):
        artist_anima = random_prompt("./data_comfyui/artist_anima.txt", -1)
        artist_anima = "@(" + artist_anima + ":2.0)"

    messages_history_rp_org = copy.deepcopy(messages_history_rp) 
    prompt_header = artist_anima + ", masterpiece, best quality, highres, absurdres, newest, score_9, score_8, score_7, " + safety_tag + ", looking_at_viewer:2.0, [ANGLE]"
    if sex == "male":
        prompt_header += ", 1boy, solo.\n"
    else:        
        prompt_header += ", 1girl, solo.\n"
    prompt_tail = "\nlocation, (A highly aesthetic Pixiv style illustration, clean composition, high-quality digital art, detailed background, sharp focus on facial expressions.:0.6)"

    flag = 0
    messages_history_temp = copy.deepcopy(messages_history_rp)

    # Generate anima command
    while (flag == 0):
        messages_history_rp, full_response = openAI_response(json_value,client_rp, messages_history_rp, order ,2, False)
        if full_response.count("##PROMPT##") == 2 and full_response.count("speech bubble") >= 1 and len(full_response) < 1500:
            flag = 1
            print(f"PASS: Total response: {len(full_response)}\n")
            single_prompt = full_response.split("##PROMPT##")
            default_anima_prompt = single_prompt[1].replace("##PROMPT##", "") + "," + config.background_tag[config.episode_num]
        else:            
            print(f"FAIL: {full_response.count('##PROMPT##')}, {full_response.count('speech bubble')}, {len(full_response)}")
            if len(full_response) >= 1500:
                print(f"Total response: {len(full_response)}\n")
            else:                
                print(f"Not sufficient format\n")
            messages_history_rp = copy.deepcopy(messages_history_temp)

    prompt = prompt_header.replace("[ANGLE]", "date_sim:2.0, front_shot:2.0, white_background:2.0, no_background.\nIt is dating simulation game character standing image. ") + default_anima_prompt + prompt_tail
    print(prompt)
    comfyui_run_anima(json_value, episode, prompt, 6)
    messages_history_rp = copy.deepcopy(messages_history_rp_org)

    prompt = prompt_header.replace("[ANGLE]", "portrait:3.0, white_background:2.0, no_background\n\n") + default_anima_prompt + "\n" +  prompt_tail
    print(prompt)
    comfyui_run_anima(json_value, episode, prompt, 6)

    #qwen35_image_check == False

def anima_gen_simple(episode, messages_history_rp, json_value, client_rp, sex, name, name2):
    global artist_anima
    global default_anima_prompt 
    global qwen35_image_check 
    
    anima_nametag = "event"
    #qwen35_image_check == True

    # Cloth update
    if json_value["extended"] == "yes":
        order_update2, safety_tag = config_extended.clothes_update(json_value, config.clothes, name, sex)
    else:
        order_update2 = ""        
        safety_tag = "safe, "

    #if default_anima_prompt == "":
    # Use original as default.
    default_anima_prompt = line_merge("./data_comfyui/default_anima_prompt.txt").replace("[LINE1]", line1).replace("[LINE2]", line2)
    if config.sex == "male":
        default_anima_prompt = default_anima_prompt.replace("A girl", "A boy").replace("She ", "He ").replace("Her ", "His ")

    order = line_merge("./data/anima_question.txt").replace("[NAME2]", name2).replace("[POSE]", config.pose).replace("[LINE_NUM]", line_num)
    order = order.replace("[PROMPT]", default_anima_prompt)       
    #order = order.replace("[FACE_TAG]", config.face_tag[config.episode_num] + "," + config.makeup_tag[config.episode_num] + "," + config.hair_style + "," + config.eye_color)       
    #order = order.replace("[CLOTHES_TAG]", config.clothes_arr[config.episode_num] + ","+ config.marks_tag[config.episode_num])
    #order = order.replace("[BODY_TAG]", config.body_tag[config.episode_num] + "," +config.bodystyle_tag[config.episode_num] )
    #order = order.replace("[EXPOSED_TAG]", config.exposure_tag[config.episode_num] + "," + config.p_exposure_tag[config.episode_num]  )

    order = order.replace("[NAME]", name)       
    if order.count("pose based on current episode") == 1:
        order = order.replace("pose tags: ", "")

    #order += config.action

    # Set artist for the first time
    if (artist_anima == ""):
        artist_anima = random_prompt("./data_comfyui/artist_anima.txt", -1)
        artist_anima = "@(" + artist_anima + ":2.0)"

    messages_history_rp_org = copy.deepcopy(messages_history_rp) 
    prompt_header = artist_anima + ",masterpiece, best quality, highres, absurdres, newest, score_9, score_8, score_7, " + safety_tag + ", [ANGLE]"

    if sex == "male":
        prompt_header += ",1boy,solo.\n"
        prompt_header += "A detailed anime-style illustration of a boy at the center."
    else:        
        prompt_header += ",1girl,solo.\n"
        prompt_header += "A detailed anime-style illustration of a girl at the center."

    prompt_tail = "\n\nlocation, (A highly aesthetic Pixiv style illustration, clean composition, high-quality digital art, detailed background, sharp focus on facial expressions.:0.6)"

    flag = 0
    messages_history_temp = copy.deepcopy(messages_history_rp)

    if config.anima_think == True:
        while (flag == 0):
            messages_history_rp, full_response = openAI_response(json_value,client_rp, messages_history_rp, order ,2, False)
            if full_response.count("##PROMPT##") == 2 and full_response.count("speech bubble") == 1 and len(full_response) < 1500:
                print(f"PASS: Total response: {len(full_response)}\n")
                flag = 1
                single_prompt = full_response.split("##PROMPT##")
                default_anima_prompt = single_prompt[1].replace("##PROMPT##", "") 
                config.default_anima_prompt = default_anima_prompt 
            else:
                print(f"FAIL: {full_response.count('##PROMPT##')}, {full_response.count('speech bubble')}, {len(full_response)}")
                if len(full_response) >= 1500:
                    print(f"Total response: {len(full_response)}\n")
                else:                
                    print(f"Not sufficient format\n")
                messages_history_rp = copy.deepcopy(messages_history_temp)
    else:
        i = 1
        default_anima_prompt = ""
        for line in config.default_anima_prompt.splitlines(): 
            if i == 7:
                default_anima_prompt += config.pose + "\n"
            else:
                default_anima_prompt += line + "\n"                
            i += 1                

    prompt = prompt_header.replace("[ANGLE]", "cowboy_shot, voyeurism:2.0") + default_anima_prompt + "\n" + prompt_tail
    print(prompt)
    comfyui_run_anima(json_value, episode, prompt, 3)
    #prompt = prompt_header.replace("[ANGLE]", "full_body, ") + default_anima_prompt + "\n" + config.action + "," + prompt_tail
    # print(prompt)
    # comfyui_run_anima(json_value, episode, prompt, 7)
    # print(prompt)
    prompt = prompt_header.replace("[ANGLE]", "pov, feet_out_of_frame, ") + default_anima_prompt + "\n" + prompt_tail
    comfyui_run_anima(json_value, episode, prompt, 5)

    messages_history_rp = copy.deepcopy(messages_history_rp_org)

def comfyui_run_anima(json_value, name, full_prompt, res):
    global anima_prompt

    json_file = "data_comfyui/anima_Apr10.json"
    with open(json_file) as f:
        prompt = json.load(f)
    a = rand.randint(0, 18446744073709551615)
    prompt["44"]["inputs"]["seed"] = a
    if full_prompt.find("1boy") > -1:
        prompt["89"]["inputs"]["value"] = "masterpiece,amazing quality, very aesthetic, absurdres, newest,finely detailed,colorful, outline:1.5,1boy:2.0, solo, " 
    else:        
        prompt["89"]["inputs"]["value"] = "masterpiece,amazing quality, very aesthetic, absurdres, newest,finely detailed,colorful, outline:1.5,1girl:2.0, solo, "
    prompt["71"]["inputs"]["text1"] = full_prompt
    prompt["57"]["inputs"]["dimensions"] = resol[int(res)]

    prompt["90"]["inputs"]["filename_prefix"] = f"episode_{config.episode_num+1}_{anima_nametag}_anima_"
    prompt["91"]["inputs"]["filename_prefix"] = f"episode_{config.episode_num+1}_{anima_nametag}_sdxl_"

    #if json_value["anima_style"] == "2.5d":
    prompt["67"]["inputs"]["ckpt_name"] = "ilustmix_v111.safetensors"

    if json_value["noimage"] == "yes":
        anima_prompt += full_prompt + "\n"
    else:                
        queue_prompt(prompt)
        a = rand.randint(0, 18446744073709551615)
        prompt["44"]["inputs"]["seed"] = a
        if (json_value["comfyuirun"] != "False"):
            queue_prompt(prompt)


#    elif json_value["anima_style"] == "2d_flat":
#        prompt["67"]["inputs"]["ckpt_name"] = "ilustmix_v111.safetensors"

