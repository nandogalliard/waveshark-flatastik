#!/usr/bin/python
# -*- coding:utf-8 -*-
import os
import sys

picdir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "pic"
)
libdir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "lib"
)
if os.path.exists(libdir):
    sys.path.append(libdir)

import datetime
import json
import logging
import time
import traceback

import requests
from PIL import Image, ImageDraw, ImageFont
from waveshare_epd import epd7in5bc

from secrets_api_etc import (  # Local API KEY and flatemate names are stored in secrets_api_etc.py
    wg,
    wg_name,
    wg_offset,
    x_api_key,
)

logging.basicConfig(level=logging.DEBUG)

fontsize = 20
string_length = 30


url_chores = "https://api.flatastic-app.com/index.php/api/chores"
url_wg = "https://api.flatastic-app.com/index.php/api/wg"

headers = {"x-api-key": x_api_key}


def getTime(chore):

    if chore["rotationTime"] != -1:

        till = round(chore["timeLeftNext"] / 86400)

        if till > 0:
            return "in " + str(till) + " Tagen"
        elif till == 0:

            return "heute"
        elif till < 0:

            return str(till * -1) + " Tage Verzug"
        else:

            return "Fehler"
    else:

        return "nach Bedarf"


def get_timeLeft(chores):
    return chores.get("timeLeftNext")


# testing out requests

try:
    logging.info("Initialising EPD...")

    epd = epd7in5bc.EPD()
    width = epd.width
    height = epd.height

    last_line = height - fontsize - 20
    epd.init()
    # epd.Clear()

    logging.info("Initialised, width: %s, height: %s", width, height)

    image_black = Image.new("1", (width, height), 255)  # 298*126
    image_red = Image.new(
        "1", (width, height), 255
    )  # 298*126  ryimage: red or yellow image
    draw_black = ImageDraw.Draw(image_black)
    draw_red = ImageDraw.Draw(image_red)

    logging.info("Image loaded, Loading Font...")

    font = ImageFont.truetype(
        "/home/pi/.fonts/Cousine Bold Nerd Font Complete.ttf", fontsize
    )
    fontbig = ImageFont.truetype(
        "/home/pi/.fonts/Cousine Bold Italic Nerd Font Complete.ttf", fontsize
    )
    # font = ImageFont.truetype(os.path.join(picdir, "Font.ttc"), fontsize)
    # fontbig = ImageFont.truetype(os.path.join(picdir, "Font.ttc"), fontsize, index=1)
    # font = ImageFont.truetype("ubuntu-font-family-0.83/Ubuntu-B.ttf", fontsize)

    logging.info("Font loaded...")

    choresdata = requests.get(url_chores, headers=headers).text

    wg_data = json.loads(
        requests.get(
            "https://api.flatastic-app.com/index.php/api/wg", headers=headers
        ).text
    )

    chores = sorted(json.loads(choresdata), key=get_timeLeft)

    logging.info("Flatastic requests get, cycling over chores...")

    for i in range(0, len(chores)):

        ch = chores[i]["title"]
        person = wg[chores[i]["currentUser"]]
        time = getTime(chores[i])
        start = 10 + i * (fontsize + 10)
        if start >= last_line - 2 * (fontsize + 10):
            break
        if chores[i]["rotationTime"] != -1:
            till = chores[i]["timeLeftNext"]
            till = till / 86400
            if till < 0:
                draw_red.rectangle((0, start, 640, fontsize + start + 5), fill=0)
                draw_red.text((10, start), ch[:string_length], font=font, fill=255)
                draw_red.text((380, start), person, font=font, fill=255)
                draw_red.text((470, start), time, font=font, fill=255)
            elif till < 1:
                draw_black.rectangle((0, start, 640, fontsize + start + 5), fill=0)
                draw_black.text((10, start), ch[:string_length], font=font, fill=255)
                draw_black.text((380, start), person, font=font, fill=255)
                draw_black.text((470, start), time, font=font, fill=255)
            else:
                draw_black.text((10, start), ch[:string_length], font=font, fill=0)
                draw_black.text((380, start), person, font=font, fill=0)
                draw_black.text((470, start), time, font=font, fill=0)
        else:
            draw_black.text((10, start), ch[:string_length], font=font, fill=0)
            draw_black.text((380, start), person, font=font, fill=0)
            draw_black.text((470, start), time, font=font, fill=0)

    logging.info("Aktualisiert...")

    for i in range(len(wg)):

        name = int(wg_data["flatmates"][i]["id"])

        # Somehow the chores data doesn't get reset on the backend. Thus I do it here manualy.
        points = str(int(wg_data["flatmates"][i]["chorePoints"]) - wg_offset[name])

        # points = wg_data["flatmates"][i]["chorePoints"]
        draw_black.text(
            (10 + i * width / 4, height - 2 * fontsize - 27),
            wg[name] + ": " + points,
            font=fontbig,
            fill=0,
        )

    now = datetime.datetime.now().strftime("%H:%M %d.%m.%y")
    draw_black.text(
        (10, height - fontsize - 27), "Aktualisiert: " + now, font=fontbig, fill=0
    )
    draw_red.text(
        (width / 4 * 3, height - fontsize - 27), wg_name, font=fontbig, fill=0
    )

    epd.display(epd.getbuffer(image_black), epd.getbuffer(image_red))

    logging.info("Goto Sleep...")
    epd.sleep()

except IOError as e:
    logging.info(e)

except KeyboardInterrupt:
    logging.info("ctrl + c:")
    epd7in5bc.epdconfig.module_exit()
    exit()
