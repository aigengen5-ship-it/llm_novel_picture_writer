import random as rand
import re

# Fate
body_value = [0] * 4
body_dic = {}
hip_size = 0
body_size = 0
breasts_size = 0
hair_style = ""
eye_color = ""
face_style = ""
personality = ""
personality_eng = ""
personality_diag = ""
personality_prom = ""
personality_text = ""
personality_verbal_tic = ""
personality_consist = ""
relationship = ""

dialog_dict = {}
prompt_dict = {}
love_value = 0
love_table = []
submission_level = ""
clothes_level = "fully_clothed, adjusting_clothes, clothes_intact"
openpose = ""
openpose_prom = ""
openpose_width = 0
openpose_height = 0
openpose_sel = 0

breasts_special = 0
makeup = 0
heart = 0
piercing = 0
openpose = '{"people":[{"pose_keypoints_2d":[338.09436485715537,412.9026739174106,1,421.6162716874224,660.2560133762779,1,199.96198048402164,652.2250607964445,1,168.5134648764611,1013.2133077512699,1,126.20604275892947,1188.9935744647817,1,643.2705628908232,668.2869659561113,1,551.7177034807228,1032.892213080546,1,521.2000836773561,583.1588686098778,1,312.90932683667745,1145.529244847649,1,0,0,0,0,0,0,477.58960900600607,1149.4838896588544,1,0,0,0,0,0,0,281.87769679832195,369.53552998631045,1,387.88627085212215,342.2302912148769,1,246.5415054470551,401.65934030564387,1,501.925797485756,345.44267224681045,1],"hand_left_keypoints_2d":[519.5938931613894,571.9155349981111,1,534.0496078050894,530.1545815829775,1,558.1424655445894,483.57505661994406,1,561.3548465765227,446.6326747527108,1,548.5053224487895,411.2964834014438,1,587.0538948319895,446.6326747527108,1,583.8415138000562,398.44695927371055,1,564.5672276084563,374.35410153421054,1,537.2619888370227,359.8983868905105,1,579.0229422521563,443.42029372077724,1,574.2043707042562,388.8098161779106,1,545.2929414168561,366.32314895437713,1,514.7753216134893,356.68600585857695,1,561.3548465765227,445.026484236744,1,554.9300845126561,396.8407687577438,1,526.018655225256,377.56648256614386,1,498.7134164538227,371.141720502277,1,538.8681793529895,449.8450557846441,1,527.6248457412228,417.7212454653107,1,506.7443690336561,403.26553082161064,1,489.0762733580225,400.0531497896771,1]}],"animals":[],"canvas_width":768,"canvas_height":1152}' 

def body_init(sex, json_value):
    global body_dic
    global breasts_size
    global hip_size
    global body_size
    global hair_color
    global hair_style
    global eye_color
    global face_style

    body_dic = {}
    start = 0
    with open("./data/body_tag.txt", 'r', encoding='utf-8') as f1:
        temp = f1.readlines() 
        for line in temp: 
            if line[0] == "#":
                if (start == 1):
                    body_dic[dict_tag] = dict_list
                dict_tag = line[1:].strip()
                dict_list = []
                start = 1
            else:
                dict_list.append(line.strip())
    breasts_size = rand.randint(0, len(body_dic["breasts_size"])-1)
    hip_size =  rand.randint(0, len(body_dic["hip_size"])-1)
    body_size = rand.randint(0, len(body_dic["body_size"])-1)
    hair_color = random_prompt("data_comfyui/Hair_04.Color.txt", -1) 
    if sex == "male":
        if rand.randint(0,1) == 0:
            hair_style = "short cut,pixie cut,"
        else:
            hair_style = "short cut,bob cut,"
    else:
        hair_style = random_prompt("data_comfyui/hairlength.txt", -1) + ","

    # Select Ponytail/Braid
    if (rand.randint(0,5) == 0):
        hair_style += random_prompt("data_comfyui/ponytail.txt", -1) + ","
    elif (rand.randint(0,5) == 0):
        hair_style += random_prompt("data_comfyui/hairbraid.txt", -1) + ","
    # Select HairBang
    if (rand.randint(0,2) == 0):
        hair_style += random_prompt("data_comfyui/hairbang.txt", -1) + ","
    # Hair Status(wavy...)
    hair_style += random_prompt("data_comfyui/hairstatus.txt", -1) + ","
    
    # Face 
    eye_color = random_prompt("data_comfyui/Eye_Color.txt", -1) + ","

    # Update face
    face_style = ""
    if rand.randint(1, 10) <= json_value["freckles"]:
        face_style += "freckles,"

    if rand.randint(1, 10) <= json_value["glasses"]:
        face_style += random_prompt("data_comfyui/Eyewear.txt", -1)  + ","

    if rand.randint(1, 10) <= json_value["hairacc"]:
        face_style += random_prompt("data_comfyui/Accessories_Hair.txt", -1)  + ","

    return                

def personality_init():
    global personality
    global personality_eng
    global personality_prom
    global personality_diag
    global personality_verbal_tic
    global personality_text
    global personality_consist
    global love_table
    global dialog_dict
    global prompt_dict

    # Setup personality
    if rand.randint(0,1) == 0:
        personality_consist = "내숭"
    else:        
        personality_consist = "순수함"
    personality = random_prompt("data/personality_tag.txt", -1)
    personality_text = ""

    with open("./data/personality.txt", 'r', encoding='utf-8') as r1:
        lines = r1.readlines()
    
    line_start = 0    
    for line in lines:
        if line[:2] == "##":
            if line_start == 1:
                line_start = 0
            elif line.find(personality) > -1:
                personality_eng  = line.split(",",2)[1]
                personality_prom = line.split(",",2)[2].strip()
                line_start = 1
        elif line_start == 1:
            if (line.find("**자주 쓰는") > -1):
                personality_verbal_tic = line        
            personality_text += line        

    with open("./data/all_char.txt", 'r', encoding='utf-8') as r1:
        lines = r1.readlines()

    writeenb = 0
    writeenb2 = 0
    prevkey = 0
    diag_list = []
    prom_list = []

    love_value = 0
    for line in lines:
        # Find line
        if line.find("***") > -1:
            if (line.find(personality) > -1):
                writeenb = 1
            elif (writeenb == 1):                
                writeenb = 0
                dialog_dict[prevkey] = diag_list
                prompt_dict[prevkey] = prom_list
        elif (line.find("**") > -1 and writeenb == 1):
            if line.find(" " + str(love_value) + "%") > -1:
                #print(line)
                love_meter = line[line.find(str(love_value) + "%"):]
                love_meter = love_meter.replace(str(love_value) + "%", "")
                love_meter = love_meter.replace("]", "")
                love_meter = love_meter.replace(":", "")
                love_table.append(love_meter.strip())
                love_value = love_value + 20
    
            pattern = r'(\d+(?:\.\d+)?)%'
            numbers_only = re.findall(pattern, line)
            if (numbers_only):
                if (writeenb2 == 0):
                    writeenb2 = 1
                    prevkey = int(numbers_only[0])
                else:    
                    dialog_dict[prevkey] = diag_list
                    prompt_dict[prevkey] = prom_list
                    prevkey = int(numbers_only[0])
                    diag_list = []
                    prom_list = []
            else:
                print("Error")
                print(line)
                exit()                    
        elif (writeenb == 1):
            clean_text = re.sub(r'[\s\d\W]', '', line.strip())
            has_korean = bool(re.search('[가-힣]', clean_text))
            if (has_korean):
                diag_list.append(line.strip())
            else:                
                prom_list.append(line.strip()) 

    # 1st setup
    #print(personality)
    personality_diag = rand.sample(dialog_dict[0], 1)

def character_sheet(sex, age, title1, title2, name, love_value):
    global body_dic
    global personality
    global personality_prom
    global dialog_dict
    global hair_color
    global hair_style
    global eye_color
    global face_style
    global love_table
    temp = int(love_value / 20)
    character_sheet = "## Character Sheet ##\n"
    character_sheet += "이름: " + name + "\n"
    character_sheet += "나이: " + str(age) + "\n"
    character_sheet += "성별: " + sex + "\n"
    character_sheet += "성격/말투: " + personality + "\n"
    character_sheet += "직업: " + title2[:len(title2)-1] + "\n"
    character_sheet += "호감도: " + love_table[temp] + "\n"
#    character_sheet += "대사: " + personality_diag + "\n"

    character_sheet += "머리색: " + hair_color + "\n"
    character_sheet += "헤어스타일: " + hair_style + "\n"
    character_sheet_add = "가슴크기: " +body_dic["breasts_size"][breasts_size] + "\n"
    character_sheet_add = character_sheet_add.replace("NONE", "평범")
    character_sheet += character_sheet_add
    character_sheet_add = "엉덩이 크기: " +body_dic["hip_size"][hip_size] + "\n"
    character_sheet_add = character_sheet_add.replace("NONE", "평범")
    character_sheet += character_sheet_add
    character_sheet_add = "몸매: " +body_dic["body_size"][body_size] + "\n"
    character_sheet_add = character_sheet_add.replace("NONE", "평범")
    character_sheet += character_sheet_add
    character_sheet += "\n기타 특징\n\n" + personality_text + "\n"

    comfyui_prompt = hair_color + ","
    comfyui_prompt += hair_style + "," + eye_color + ","
    comfyui_prompt += body_dic["breasts_size"][breasts_size].replace("NONE", "") + ","
    #comfyui_prompt += body_dic["hip_size"][hip_size].replace("NONE", "") + ","
    comfyui_prompt += body_dic["body_size"][body_size].replace("NONE", "") + ","

    return character_sheet, comfyui_prompt

# Update Character body
def character_update(love_value):
    global clothes_level
    global personality_diag
    global personality_prom

    # Personality_prom        
    if love_value in dialog_dict.keys():
        personality_diag = rand.sample(dialog_dict[love_value], 1)[0].strip()
        #print(personality_diag)
        personality_prom = ",".join(rand.sample(prompt_dict[love_value], 1))
        
        # Comfyui undress level
        if (love_value == 40):
            clothes_level = "showing_bra,"
        elif (love_value == 60):
            clothes_level = "clothes_down, showing_underwear,"

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

def openpose_set():
    global openpose
    global openpose_prom
    global openpose_height
    global openpose_width
    global openpose_sel
    pos = str(rand.randint(0,1)) + "/" 
    with open("./data_comfyui/openposeSFW" + pos + "json.list", 'r', encoding='utf-8') as r1:
        json_list = r1.readlines()
    json_list2 = rand.sample(json_list, 1)[0].strip()

    with open("./data_comfyui/json_pose.list", 'r', encoding='utf-8') as r1:
        temp = r1.readlines()

    for temp2 in temp:
        if json_list2.find(temp2.strip()) > -1:
            openpose_prom = temp2.replace("_",",").lower().strip()
            print(openpose_prom, json_list2)

    with open("./data_comfyui/openposeSFW" + pos + json_list2 , 'r', encoding='utf-8') as r1:
        openpose = r1.readline()

    temp = openpose.find('"canvas_height":')
    temp2 = openpose.find('"canvas_width":')
    print(temp,temp2, openpose_prom)
    openpose_height = int(openpose[temp+16:len(openpose)-1])
    openpose_width  = int(openpose[temp2+15:temp-1])
  
    if openpose_width > openpose_height:
        openpose_sel = 3
    elif openpose_width < openpose_height:
        openpose_sel = 5
    else:
        openpose_sel = 4        


