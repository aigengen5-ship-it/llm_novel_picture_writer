import random as rand

# Fate
body_value = [0] * 4
body_dic = {}

hip_size = 0
body_size = 0
breasts_size = 0

breasts_special = 0
makeup = 0
heart = 0
piercing = 0

def body_init():
    global body_dic
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
    breasts_size = (rand.choice(body_dic["breasts_size"]))
    hip_size = (rand.choice(body_dic["hip_size"]))
    body_size = (rand.choice(body_dic["body_size"]))

    return                

def body_change(body_value):
    if body_value[0] == 0:
        breasts_size = "flat chest"
