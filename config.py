import random as rand
import re
import llm_def
import rp

# Character A
anima_think = True
default_anima_prompt = ""
episode_num = 0
face_tag = []
bodystyle_tag = []
minion_tag = []
makeup_tag = []
marks_tag = []
exposure_tag = []
p_exposure_tag = []
background_tag = []
body_tag = []
json_episode_num  = 0

clothes_arr = []
action_arr = []
location_arr = []
status_arr = []
rptag = ""
episode_list = []
current_level = 0
sex = ""
body_value = [0] * 4
body_dic = {}
hip_size = -1
muscle_enb = False
body_size = 0
breasts_size = -1
hair_style = ""
eye_color = ""
face_style = ""
personality = ""
personality_real = ""
personality_eng = ""
personality_diag = ""
personality_prom = ""
personality_text = ""
personality_verbal_tic = ""
personality_consist = ""
objective = ""
objective_hidden = ""
relationship = ""
job = ""
job_raw = ""
age = 0
name = ""
keyword_job = ""
clothes = ""
mindset = []
curr_face = ""
job_attribute = ""

# Character B
sex2 = ""
job2_raw = ""
age2 = 0
name2 = ""

nationality = ""
nationality2 = ""
bodytag = []
animabodytag = ""
pose = ""

# Setup
dialog_style_simple = []
dialog_dict = {}
prompt_dict = {}
love_value = 0
love_table = []
submission_level = ""
openpose = ""
openpose_prom = ""
openpose_width = 0
openpose_height = 0
openpose_sel = 0
rag_diag = ""
plump_enb = False
fem_enb = False
minion_enb = True

breasts_special = 0
makeup = 0
heart = 0
piercing = 0
openpose = '{"people":[{"pose_keypoints_2d":[338.09436485715537,412.9026739174106,1,421.6162716874224,660.2560133762779,1,199.96198048402164,652.2250607964445,1,168.5134648764611,1013.2133077512699,1,126.20604275892947,1188.9935744647817,1,643.2705628908232,668.2869659561113,1,551.7177034807228,1032.892213080546,1,521.2000836773561,583.1588686098778,1,312.90932683667745,1145.529244847649,1,0,0,0,0,0,0,477.58960900600607,1149.4838896588544,1,0,0,0,0,0,0,281.87769679832195,369.53552998631045,1,387.88627085212215,342.2302912148769,1,246.5415054470551,401.65934030564387,1,501.925797485756,345.44267224681045,1],"hand_left_keypoints_2d":[519.5938931613894,571.9155349981111,1,534.0496078050894,530.1545815829775,1,558.1424655445894,483.57505661994406,1,561.3548465765227,446.6326747527108,1,548.5053224487895,411.2964834014438,1,587.0538948319895,446.6326747527108,1,583.8415138000562,398.44695927371055,1,564.5672276084563,374.35410153421054,1,537.2619888370227,359.8983868905105,1,579.0229422521563,443.42029372077724,1,574.2043707042562,388.8098161779106,1,545.2929414168561,366.32314895437713,1,514.7753216134893,356.68600585857695,1,561.3548465765227,445.026484236744,1,554.9300845126561,396.8407687577438,1,526.018655225256,377.56648256614386,1,498.7134164538227,371.141720502277,1,538.8681793529895,449.8450557846441,1,527.6248457412228,417.7212454653107,1,506.7443690336561,403.26553082161064,1,489.0762733580225,400.0531497896771,1]}],"animals":[],"canvas_width":768,"canvas_height":1152}' 

docker_llm_name = "gemma-3-27b"

a = rand.randint(1,5)

if a == 1:
    skin_color = "갈색"
elif a == 2:
    skin_color = "밝은 살색"
else:    
    skin_color = "하얀 살색(백인 느낌)"

if rand.randint(1,5) == 1:
    eye_shape = "긴 눈"
elif rand.randint(1,5) == 2:
    eye_shape = "큰 눈"
elif rand.randint(1,5) == 2:
    eye_shape = "처진 눈"
else:
    eye_shape = "평범한 눈"

def character_init(sex, json_value):
    global body_dic
    global breasts_size
    global hip_size
    global body_size
    global hair_color
    global hair_style
    global eye_color
    global face_style
    global job
    global job2

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
    if (sex == "male"):                
        breasts_size = 0
        hip_size = 0
    else:        
        if breasts_size == -1:
            breasts_size = rand.randint(0, len(body_dic["breasts_size"])//2)
        if hip_size == -1:
            hip_size =  rand.randint(0, len(body_dic["hip_size"])//2)

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
    if (rand.randint(0,2) == 0):
        hair_style += random_prompt("data_comfyui/ponytail.txt", -1) + ","
    elif (rand.randint(0,5) == 0):
        hair_style += random_prompt("data_comfyui/hairbraid.txt", -1) + ","
    # Select HairBang
    if (rand.randint(0,2) == 0):
        hair_style += random_prompt("data_comfyui/hairbang.txt", -1) + ","
    # Hair Status(wavy...)
    hair_style += random_prompt("data_comfyui/hairstatus.txt", -1) + ","

    # Clean hair for man
    if sex == "male":
        if rand.randint(0,1) == 0:
            hair_style = "short cut,pixie cut,"
        else:
            hair_style = "short cut,bob cut,"
    
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

def personality_init(json_value):
    global personality
    global personality_real
    global personality_eng
    global personality_prom
    global personality_diag
    global personality_verbal_tic
    global personality_text
    global personality_consist
    global love_table
    global love_value
    global dialog_dict
    global prompt_dict
    global dialog_style_simple

    # Speaking Style
    temp = random_prompt("story/COMMON/dialog_style_simple.txt", -1)
    dialog_style_simple = temp.split("#")

    # Old
    personality = random_prompt("data/personality_tag.txt", json_value["personality"] - 1)

    # New
    if personality_real != "":
        personality_real = random_prompt("story/COMMON/personality_tag.txt", json_value["personality"] - 1)
        if sex == "male":
            personality_real = personality_real.split("#")[1].strip()
        else:        
            personality_real = personality_real.split("#")[0]
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
            personality_text += line
            break 
    
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
                #love_table.append(love_meter.strip())
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
    personality_text = ""
    personality_diag = rand.sample(dialog_dict[0], 1)

def character_sheet(love_value):
    global body_dic
    global personality
    global personality_prom
    global dialog_dict
    global hair_color
    global hair_style
    global eye_color
    global face_style
    global love_table
    global relationship
    global clothes
    global job_attribute


    acc = random_prompt("data_comfyui/accessory.txt", -1)

    if job_attribute == "":
        job_attribute = rand.choice([ "긍지", "의무", "평범", "불만"])

    temp = love_value
    character_sheet = "## Character Sheet ##\n"
    character_sheet += "이름: " + name + "\n"
    character_sheet += "나이: " + str(age) + "\n"
    character_sheet += "성별: " + sex + "\n"
    character_sheet += "성격/말투: " + personality_real + "\n"
    character_sheet += "직업: " + job + "\n"
    character_sheet += "직업에 대한 평가(긍지/의무/평범/불만): " + job_attribute + "\n"
    character_sheet += "인생 목표: " + objective + "\n"
    character_sheet += "현재 느끼는 행복도: " + str(rand.randint(0,100)) + "%\n"
    character_sheet += "도덕성(0~5): " + str(rand.randint(4,5)) + "\n"
    character_sheet += "애정도(0~5): " + str(rand.randint(0,6)//5) + "\n"
    character_sheet += "호감도(0~5): " + str(rand.randint(0,4)) + "\n"
    character_sheet += "복종도(0~5): " + str(rand.randint(0,3)) + "\n"
    character_sheet += "지성(0~5): "   + str(rand.randint(2,5)) + "\n"
    character_sheet += "수치심(0~5): " + str(rand.randint(3,5)) + "\n"
    character_sheet += "주도권(0~5): " + str(rand.randint(0,5)) + "\n"
    character_sheet += "머리색: " + hair_color + "\n"
    character_sheet += "헤어스타일: " + hair_style + "\n"
    character_sheet += "눈 색깔: " + eye_color + "\n"
    character_sheet += "눈 모양: " + eye_shape + "\n"
    character_sheet += "피부 색깔: " + skin_color + "\n"
    character_sheet += "얼굴 스타일: " + face_style + "\n"
    character_sheet += "액서서리: " + acc + "\n"
    character_sheet_add = "가슴크기: " +body_dic["breasts_size"][breasts_size] + "\n"
    character_sheet_add = character_sheet_add.replace("NONE", "평범")
    character_sheet += character_sheet_add
    character_sheet_add = "엉덩이 크기: " +body_dic["hip_size"][hip_size] + "\n"
    character_sheet_add = character_sheet_add.replace("NONE", "평범")
    character_sheet += character_sheet_add
    character_sheet_add = "몸매: " +body_dic["body_size"][body_size] + "\n"
    character_sheet_add = character_sheet_add.replace("NONE", "평범")
    character_sheet += character_sheet_add

    if (sex == "female"):
        if (age < 20):
            clothes = random_prompt("./story/COMMON/clothes_student.txt", -1)
        else:        
            clothes = random_prompt("./story/COMMON/clothes_adult.txt", -1)
    else:
        clothes = "평범한 남자 옷"            
    character_sheet_add = "복장: " + clothes + "\n"
    character_sheet += character_sheet_add

    if (relationship != ""):
        character_sheet += "\n혈연관계:" + relationship + "\n"

    character_sheet += "\n기타 특징\n\n" + personality_text + "\n"


    comfyui_prompt = ""

    return character_sheet, comfyui_prompt

# Update Character body
def character_update(love_value):
    global personality_diag
    global personality_prom

    # Personality_prom        
    if love_value in dialog_dict.keys():
        personality_diag = rand.sample(dialog_dict[love_value], 1)[0].strip()
        #print(personality_diag)
        personality_prom = ",".join(rand.sample(prompt_dict[love_value], 1))

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
        openpose = r1.readlines()

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

def dialog_addon():
    i = rand.randint(0,10)
    style = llm_def.line_merge("./story/COMMON/dialog_style.txt")
 
    a = style.find("#### **Type " + str(i))
    b = style.find("#### **Type " + str(i+1))
    style = style[a:b]
    return style

def calage(theme, json_value):
    global age
    global age2
    global name
    global name2
    global nationality
    global nationality2

    temp = job_raw.split(",")
    if age == 0:
        age = rand.randint(int(temp[2]), int(temp[3]))
    temp = job2_raw.split(",")
    if age2 == 0:
        age2 = rand.randint(int(temp[2]), int(temp[3]))

    nationality_tag = ["korean", "japanese", "western", "fantasy", "others"]

    if nationality == "":
        #nationality = rand.choice(nationality_tag)
        nationality = nationality_tag[1]
    if nationality2 == "":
        nationality2 = nationality_tag[1]

        name_tag = "./story/COMMON/" + sex + "_" + nationality + ".txt"
        name_tag2 = "./story/COMMON/" + sex2 + "_" + nationality2 + ".txt"
        name = random_prompt(name_tag, -1).strip()
        name_eng = ""
        name2 = random_prompt(name_tag2, -1).strip()
        name2_eng = ""

