import fnmatch
import json
import os
import re
import subprocess

"""Fonts that don't need to be considered"""
FONT_BLACKLIST = [
        'xorg-font-util',
        'xorg-fonts-100dpi',
        'xorg-fonts-75dpi',
        'xorg-fonts-encodings',
        'xorg-fonts-alias',
        'xorg-fonts-cyrillic',
        'artwiz-fonts',
        'xorg-fonts-misc',
        'xorg-fonts-type1',
        'wqy-bitmapfont',
        'wqy-microhei']

def exec_cmd(cmd):
    proc_result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    return proc_result.stdout.decode('UTF-8')

def fetch_repo_fonts():
    cmd = ['pkgfile', '-rv', '/usr/share/fonts/.*\.(ttf)']
    fonts = exec_cmd(cmd).split('\n')

    repo_fonts = {}
    for font in fonts:
        if font:
            pkgname, path = font.split('\t')
            pkgname = re.search(r'/(.*)\s', pkgname.strip()).group(1)
            font_file = path.rpartition('/')[-1]
            norm_font_file = re.search(r'([a-zA-Z]*)', font_file.lower()).group(1)

            if pkgname not in FONT_BLACKLIST:
                if norm_font_file not in repo_fonts:
                    repo_fonts[norm_font_file] = pkgname

    return repo_fonts

def fetch_google_fonts():
    cmd = ['git', 'clone', 'https://github.com/google/fonts.git']
    exec_cmd(cmd)

    fonts = {}
    for root, dirs, files in os.walk('fonts'):
        if files:
            for file in files:
                if fnmatch.fnmatch(file, '*.ttf'):
                    fonts[root.rpartition('/')[-1]] = root
                    break
    return fonts

"""
    For the first font in every folder within the google fonts repo, use `fc-query` to get the expected package name
    of the font. Store this name with the google fonts relative path for further processing
"""
def fetch_google_font_names(flagged_google_fonts):
    font_names = {}
    for root, dirs, files in os.walk('fonts'):
        if files:
            for file in files:
                if fnmatch.fnmatch(file, '*.ttf'):
                    cmd = ['fc-query', '-f', '%{family[0]|downcase|translate( ,-)}\n', os.path.abspath(root + '/' + file)]
                    if root not in flagged_google_fonts:
                        font_names[root] = exec_cmd(cmd).split('\n')[1]
                        break

    return font_names


"""
    font_names: key, value pairs representing the relative path in the google fonts repo and the name of the font for each folder.
"""
def fetch_aur_fonts(font_names):
    fonts = {}
    for font_path, name in font_names.items():
        cmd = ['aursearch', '-vr', name]
        result = json.loads(exec_cmd(cmd))
        if not result:
            print('ERROR: Expected response from AUR to contain 0 or more results. Response was empty.')
            print(f"Result: {result}, Font path: {font_path}, Font name: {name}")
            continue
        else:
            result = result[0]  #  We direct index here because the list always has one result which is the json obj itself

        if int(result['resultcount']) == 0:
            fonts[font_path] = name + '-fonts'
        else:
            # NOTE: There are actually search results for the font name, let's list out the packages that came back
            font_packages = []
            potential_matches = False
            for package in result['results']:
                pkg_name = package['Name']

                #  NOTE: Only consider the package if the name of the font is actually part of the package name itself
                if name in pkg_name and any(keyword in pkg_name for keyword in ['ttf', 'font']):
                    font_packages.append(pkg_name)
                    potential_matches = True

            if not potential_matches:
                fonts[font_path] = name + '-fonts'
            else:
                print(f"[{font_path}] potentially satisfied by {font_packages}")

    return fonts


if __name__ == "__main__":
    # cmd = ['pkgfile', '-u']  # requires su, maybe leave that to the user?

    repo_font_dict = fetch_repo_fonts()
    google_font_dict = fetch_google_fonts()

    flagged_google_fonts = set()  #  Contains all the [extra] and [community] packages that provide fonts that google-fonts also provides (but will be removed in the PKGBUILD).

    for google_font_name, path in google_font_dict.items():
        if google_font_name in repo_font_dict:
            # print(f"Collision: [{google_font_dict[google_font_name]}] is provided by package [{repo_font_dict[google_font_name]}]")
            flagged_google_fonts.add(google_font_dict[google_font_name])

    font_names = fetch_google_font_names(flagged_google_fonts)  #  For every font folder in the google fonts repo, 
    autogen_font_names = fetch_aur_fonts(font_names)
    print('-------------------------------------------------------------------')
    for font_path, name in autogen_font_names.items():
        print(f"[{name}] virtually provides [{font_path}]")
