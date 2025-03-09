import sys
import os
import shutil
import subprocess
import json5 as json

from pe_tools import parse_pe, IMAGE_DIRECTORY_ENTRY_RESOURCE
from pe_tools.rsrc import parse_pe_resources, pe_resources_prepack, parse_prelink_resources, KnownResourceTypes
from pe_tools.version_info import parse_version_info, VersionInfo

# Contains code from https://github.com/KristalTeam/Kristal/blob/main/build.py

RT_VERSION = KnownResourceTypes.RT_VERSION

resources = None

class _IdentityReplace:
    def __init__(self, val):
        self._val = val

    def __call__(self, s):
        return self._val

class Version:
    def __init__(self, s):
        s = s.strip("-beta")
        s = s.strip("-alpha")
        s = s.strip("-dev")
        parts = s.split(',')
        if len(parts) == 1:
            parts = parts[0].split('.')
        self._parts = [int(part.strip()) for part in parts]
        if not self._parts or len(self._parts) > 4 or any(part < 0 or part >= 2**16 for part in self._parts):
            raise ValueError('invalid version')

        while len(self._parts) < 4:
            self._parts.append(0)

    def get_ms_ls(self):
        ms = (self._parts[0] << 16) + self._parts[1]
        ls = (self._parts[2] << 16) + self._parts[3]
        return ms, ls

    def format(self):
        return ', '.join(str(part) for part in self._parts)

def setInfo(key, value):
    ver_data = None
    for name in resources.get(RT_VERSION, ()):
        for lang in resources[RT_VERSION][name]:
            if ver_data is not None:
                print('error: multiple manifest resources found', file=sys.stderr)
                return 4
            ver_data = resources[RT_VERSION][name][lang]
            ver_name = name
            ver_lang = lang
    
    if ver_data is None:
        ver_data = VersionInfo()
    
    params = {}
    params[key] = _IdentityReplace(value)
    
    vi = parse_version_info(ver_data)
    
    fvi = vi.get_fixed_info()
    if 'FileVersion' in params:
        ver = Version(params['FileVersion'](None))
        fvi.dwFileVersionMS, fvi.dwFileVersionLS = ver.get_ms_ls()
    if 'ProductVersion' in params:
        ver = Version(params['ProductVersion'](None))
        fvi.dwProductVersionMS, fvi.dwProductVersionLS = ver.get_ms_ls()
    vi.set_fixed_info(fvi)
    
    sfi = vi.string_file_info()
    for _, strings in sfi.items():
        for k, fn in params.items():
            val = fn(strings.get(k, ''))
            if val:
                strings[k] = val
            elif k in strings:
                del strings[k]
    vi.set_string_file_info(sfi)
    resources[RT_VERSION][ver_name][ver_lang] = vi.pack()

def prepare_kristal():
    try: shutil.rmtree("build")
    except FileNotFoundError: pass
    try: shutil.rmtree("output")
    except FileNotFoundError: pass
    os.mkdir("build")
    os.mkdir("output")
    shutil.copytree("kristal", "build/kristal")

mod_info = None
def patch_icon():
    print("(Not yet implemented)")
    shutil.copy("build/kristal_noicon.exe", "build/mod-win/"+mod_info['id']+".exe")

def main():
    prepare_kristal()
    global mod_info
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

    print(f"Copying mod to output/{mod_info['id']}-kristal.zip")
    shutil.make_archive(f"output/{mod_info['id']}-kristal", "zip", "mod", "")
    
    print(f"Creating windows build at build/kristal_noicon.exe")
    shutil.copytree("love-11.5-win64", "build/mod-win")
    with open(os.path.join("build","mod-win","love.exe"), "rb") as file1, open(os.path.join("output", f"{mod_info['id']}.love"), "rb") as file2, open(os.path.join("build", "kristal_noicon.exe"), "wb") as output:
        output.write(file1.read())
        output.write(file2.read())
    os.remove("build/mod-win/love.exe")
    os.remove("build/mod-win/lovec.exe")

    print("Patching in icon")
    patch_icon()

    print(f"Creating output/{mod_info['id']}-win.zip")
    shutil.make_archive(f"output/{mod_info['id']}-win", "zip", "build/mod-win", "")

    print("All done!")



if __name__ == "__main__": main()
