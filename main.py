import sys
import os
import shutil
import subprocess
import json5 as json

def prepare_kristal():
    try: shutil.rmtree("build")
    except FileNotFoundError: pass
    try: shutil.rmtree("output")
    except FileNotFoundError: pass
    os.mkdir("build")
    os.mkdir("output")
    shutil.copytree("kristal", "build/kristal")


def main():
    prepare_kristal()
    mod_info = None
    with open("mod/mod.json", "r") as modjson: mod_info = json.load(modjson)
    mod_info['path'] = "build/kristal/mods/" + mod_info["id"]
    shutil.copytree("mod", mod_info["path"])
    try: shutil.rmtree(f"{mod_info['path']}.git")
    except FileNotFoundError: pass

    with open("build/kristal/src/engine/vendcust.lua", "a") as vendcust:
        vendcust.write(f"TARGET_MOD = \"{mod_info['id']}\"\n")
    
    if os.path.exists(f"{mod_info['path']}/patches"):
        old_path = os.getcwd()
        os.chdir(old_path + "/build/kristal")
        for patch_path in os.listdir(f"{old_path}/{mod_info['path']}/patches"):
            print(f"Applying {patch_path}")
            subprocess.run(["git", "apply", "--allow-empty", f"{old_path}/{mod_info['path']}/patches/{patch_path}"])
        os.chdir(old_path)

    if os.path.exists(f"{mod_info['path']}/preview/splash_logo.png"):
        shutil.copyfile(f"{mod_info['path']}/preview/splash_logo.png", "build/kristal/assets/sprites/kristal/title_logo.png")
    if os.path.exists(f"{mod_info['path']}/preview/splash_logo_heart.png"):
        shutil.copyfile(f"{mod_info['path']}/preview/splash_logo_heart.png", "build/kristal/assets/sprites/kristal/title_logo_heart.png")

    print("Removing default mods")
    shutil.rmtree("build/kristal/mods/_testmod")
    shutil.rmtree("build/kristal/mods/example")

    print(f"Creating love file at output/{mod_info['id']}.love")
    shutil.make_archive("output/kristal", "zip", "build/kristal", "")
    shutil.move("output/kristal.zip", f"output/{mod_info['id']}.love")



if __name__ == "__main__": main()
