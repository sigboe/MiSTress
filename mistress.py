#!/usr/bin/env python3
import feedparser, sys, os, argparse, locale, ssl, textwrap, time
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
# Settup pillow for drawing
image = Image.open('/media/fat/wallpaper.png').convert('RGB')
draw = ImageDraw.Draw(image)
font = ImageFont.truetype('./Roboto-Regular.ttf', 23)
color = "black"
shadowcolor = "white"
(x, y) = (24, 200)
#Text wrap settings
wrapper = textwrap.TextWrapper(width=50, subsequent_indent=' ')
# init system
inittab = '/etc/inittab'
initline = '::sysinit:/media/fat/Scripts/rss -u'

if args.updaterss:
    for i in range(5):
        date = time.strftime("%b %d", rss.entries[i].published_parsed)
        xmllint = run(['xmllint', '--html', '--xpath', '//text()', '-'], input = rss.entries[i].summary, stdout=PIPE, universal_newlines=True)
        summary = wrapper.fill(text=xmllint.stdout)
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