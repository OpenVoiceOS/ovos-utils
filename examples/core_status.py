from ovos_utils.skills import skills_loaded
from time import sleep

loaded = False
while not loaded:
    loaded = skills_loaded()
    sleep(0.5)

print("Skills all loaded!")

