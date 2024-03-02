import json
dict_p = dict()
dict_p["person"] = 3
dict_p["bicycle"] = 1
dict_p["motorbike"] = 2
file_name = "data.json"
with open(file_name, 'w') as file:
    json.dump(dict_p, file)