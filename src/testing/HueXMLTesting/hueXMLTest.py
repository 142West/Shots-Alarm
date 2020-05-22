import json

f = open("../../config/hue.json")
hueLights = json.load(f)
print(hueLights)
print(hueLights["bridgeIp"])
print(hueLights["lights"][0])