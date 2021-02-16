#!/usr/bin/env python3
import feedparser, sys, os, argparse, locale, ssl, textwrap, time, random
from subprocess import run, PIPE
from PIL import Image, ImageFont, ImageDraw
from dialog import Dialog
# feedparser, PIL and dialog are dependencies not met on MiSTer
# these are baked in with PyInstaller. 
# PyInstaller needs to be patched to include libxcb, 
# as it is designed to explicitly ignore that, but MiSTer needs it.

# Disable ssl enforcement if platform doesn't support it
# This is needed by MiSTer. If not, feedparser will error.
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

# This is currently needed to use the included baked in font file
os.chdir(sys._MEIPASS)

# Dialog
locale.setlocale(locale.LC_ALL, '')
d = Dialog(dialog="dialog", autowidgetsize=True)
d.set_background_title("RSS Wallpaper v0.1")
# Parse command line options (ie. -u)
parser = argparse.ArgumentParser(description='enable/disable daemon that writes an rss feed to the wallpaper.')
parser.add_argument('--updaterss', '-u', help='update wallpaper with latest rss', action='store_true')
args = parser.parse_args()
# Setup the rss feed
rss = feedparser.parse('https://misterfpga.org/feed.php?t=147')
feed = ''
# Pick image random png from /media/fat/wallpapers if present, if not pick /media/fat/wallpaper.png
if os.path.isdir('/media/fat/wallpapers'):
    wallpapers = [os.path.join('/media/fat/wallpapers', _) for _ in os.listdir('/media/fat/wallpapers') if _.endswith(r".png")]
    image = Image.open(random.choice(wallpapers)).convert('RGB')
else:
    image = Image.open('/media/fat/wallpaper.png').convert('RGB')
# Settup pillow for drawing
draw = ImageDraw.Draw(image)
font = ImageFont.truetype('./Roboto-Regular.ttf', 23)
color = "black"
shadowcolor = "white"
(x, y) = (24, 200)
# init system
inittab = '/etc/inittab'
initline = '::sysinit:/media/fat/Scripts/mistress -u'
# mister api
mistercmd = '/dev/MiSTer_cmd'
corename = '/tmp/CORENAME'

if args.updaterss:
    for i in range(4):
        date = time.strftime("%b %d", rss.entries[i].published_parsed)
        #print(rss.entries[i].summary)
        xmllint = run(['xmllint', '--html', '--xpath', '//text()', '-'], input = rss.entries[i].summary.replace('<br>', '\n'), stdout=PIPE, universal_newlines=True)
        #print(xmllint.stdout)
        summary = '\n'.join(['\n'.join(textwrap.wrap(line, 50, break_long_words=False, replace_whitespace=False, subsequent_indent=' ')) for line in xmllint.stdout.splitlines() if line.strip() != ''])
        #print(summary)
        feed += rss.entries[i].author + ' @ ' + date + '\n' + summary + '\n\n'
    
    print(feed, end =" ")

    # draw text outline first
    draw.text((x-1, y-1), feed, font=font, fill=shadowcolor)
    draw.text((x+1, y-1), feed, font=font, fill=shadowcolor)
    draw.text((x-1, y+1), feed, font=font, fill=shadowcolor)
    draw.text((x+1, y+1), feed, font=font, fill=shadowcolor)

    # then draw text over it
    draw.text((x, y), feed, fill=color, font=font)
    image.save('/media/fat/menu.png')
    
    # restart the menu if you are still there
    if 'MENU' in open(corename).read():
        api=open(mistercmd, 'w')
        api.write("load_core /media/fat/menu.rbf" + "\n")

    # Exit
    sys.exit()

#enabling this will make it run via init system
# https://buildroot.org/downloads/manual/manual.html#_init_system

with open(inittab) as origin:
    for line in origin:
        if not initline in line:
            serviceenabled = False
            continue
        try:
            serviceenabled = True
            break
        except IndexError:
            print

if serviceenabled:
    if d.yesno("RSS service is installed and enabled, remove service?") == d.OK:
        with open(inittab,"r+") as f:
            new_f=f.readlines()
            f.seek(0)
            for line in new_f:
                if initline not in line:
                    f.write(line)
            f.truncate()
else:
    if d.yesno("RSS service is not installed, install service?") == d.OK:
        f=open(inittab, "a+")
        f.write(initline + "\n" )
