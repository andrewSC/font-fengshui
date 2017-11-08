import fnmatch
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

def generate_font_dict(fonts):
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

if __name__ == "__main__":
    # cmd = ['pkgfile', '-u']  # requires su, maybe leave that to the user?

    cmd = ['pkgfile', '-rv', '/usr/share/fonts/.*\.']
    result = exec_cmd(cmd)
    font_dict = generate_font_dict(result.split('\n'))
    google_font_dict = fetch_google_fonts()

    for google_font_name, path in google_font_dict.items():
        if google_font_name in font_dict:
            print(f"Collision: [{google_font_dict[google_font_name]}] is provided by package [{font_dict[google_font_name]}]")

