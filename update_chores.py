
#!/usr/bin/python
# -*- coding:utf-8 -*-
import os
import re
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
import math
import time
import traceback

import requests
from PIL import Image, ImageDraw, ImageFont

import secrets_api_etc
from chore_formatting import is_very_overdue
from secrets_api_etc import (  # Local settings and API key are stored here.
    DISPLAY_DRIVER,
    enable_working_range,
    wg,
    wg_name,
    wg_offset,
    working_range_upper_bound,
    x_api_key,
)

enable_very_overdue_format = getattr(
    secrets_api_etc, "enable_very_overdue_format", True
)
very_overdue_threshold_percent = getattr(
    secrets_api_etc, "very_overdue_threshold_percent", 50
)
very_overdue_one_time_days = getattr(
    secrets_api_etc, "very_overdue_one_time_days", 10
)

if DISPLAY_DRIVER == "epd7in5bc":
    from waveshare_epd import epd7in5bc as epd_driver
elif DISPLAY_DRIVER == "epd7in5b_V2":
    from waveshare_epd import epd7in5b_V2 as epd_driver
else:
    raise ValueError(f"Unsupported display driver: {DISPLAY_DRIVER}")

logging.basicConfig(level=logging.DEBUG)

fontsize = 20
string_length = 30


url_chores = "https://api.flatastic-app.com/index.php/api/chores"
url_wg = "https://api.flatastic-app.com/index.php/api/wg"
url_points = "https://api.flatastic-app.com/index.php/api/chores/statistics" #new

headers = {"x-api-key": x_api_key}


def getTime(chore):

    till = math.floor(chore["timeLeftNext"] / 86400)

    if till > 0:
        temp = "in " + str(till) + " Tagen"
    elif till == 0:

        temp = "heute"
    elif till < 0:

        temp = str(till * -1) + " Tage Verzug"
    else:

        temp = "Fehler"

    return temp


def get_timeLeft(chores):
    return chores.get("timeLeftNext")


# testing out requests

try:
    logging.info("Initialising EPD...")

    epd = epd_driver.EPD()
    width = epd.width
    height = epd.height

    # Layout was originally designed for 640 px width
    base_width = 640
    scale_x = width / base_width

    x_title = round(10 * scale_x)
    x_person = round(380 * scale_x)
    x_time = round(470 * scale_x)
    row_right = width - 1

    title_chars = round(string_length * scale_x)

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
        "/home/job/.fonts/CousineNerdFont-Bold.ttf", fontsize
    )
    fontbig = ImageFont.truetype(
        "/home/job/.fonts/CousineNerdFont-BoldItalic.ttf", fontsize
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
    points_data = json.loads(requests.get(url_points, headers=headers).text) #new

    chores = sorted(json.loads(choresdata), key=get_timeLeft)

    change_detected = True
    while (
        change_detected
    ):  # Loop until no change is detected. If -1 was directly behind another -1, it would be skipped if not looping
        change_detected = False
        for idx, obj in enumerate(
            chores
        ):  # Remove chores that are not done at specific times.
            if obj["rotationTime"] == -1:
                chores.pop(idx)
                change_detected = True

    logging.info("Flatastic requests get, cycling over chores...")

    very_overdue_count = 0
    for i in range(0, len(chores)):

        ch = chores[i]["title"]
        person = wg[chores[i]["currentUser"]]
        time_left = getTime(chores[i])
        start = 10 + i * (fontsize + 10)
        if start >= last_line - 2 * (fontsize + 10):
            break
        if chores[i]["rotationTime"] != -1:
            till = chores[i]["timeLeftNext"]
            till = till / 86400
            if is_very_overdue(
                chores[i],
                enable_very_overdue_format,
                very_overdue_threshold_percent,
                very_overdue_one_time_days,
            ):
                very_overdue_count += 1
                row_bottom = fontsize + start + 5

                # Keep the existing row size. The outer two pixels become a
                # black frame and the remaining interior stays red.
                draw_black.rectangle(
                    (0, start, row_right, row_bottom), outline=0
                )
                draw_black.rectangle(
                    (1, start + 1, row_right - 1, row_bottom - 1), outline=0
                )
                draw_red.rectangle(
                    (2, start + 2, row_right - 2, row_bottom - 2), fill=0
                )

                # Clear red beneath each glyph, then draw the glyph in black.
                draw_red.text(
                    (x_title, start), ch[:title_chars], font=font, fill=255
                )
                draw_red.text((x_person, start), person, font=font, fill=255)
                draw_red.text((x_time, start), time_left, font=font, fill=255)
                draw_black.text(
                    (x_title, start), ch[:title_chars], font=font, fill=0
                )
                draw_black.text((x_person, start), person, font=font, fill=0)
                draw_black.text((x_time, start), time_left, font=font, fill=0)
            elif till < 0:
                #draw_red.rectangle((0, start, row_right, fontsize + start + 5), fill=0)
                #draw_red.text((, start), ch[:string_length], font=font, fill=255)
                #draw_red.text((380, start), person, font=font, fill=255)
                #draw_red.text((470, start), time_left, font=font, fill=255)
                draw_red.rectangle((0, start, row_right, fontsize + start + 5), fill=0)
                draw_red.text((x_title, start), ch[:title_chars], font=font, fill=255)
                draw_red.text((x_person, start), person, font=font, fill=255)
                draw_red.text((x_time, start), time_left, font=font, fill=255)
            elif till < 1:
                #draw_black.rectangle((0, start, 640, fontsize + start + 5), fill=0)
                #draw_black.text((10, start), ch[:string_length], font=font, fill=255)
                #draw_black.text((380, start), person, font=font, fill=255)
                #draw_black.text((470, start), time_left, font=font, fill=255)
                draw_black.rectangle((0, start, row_right, fontsize + start + 5), fill=0)
                draw_black.text((x_title, start), ch[:title_chars], font=font, fill=255)
                draw_black.text((x_person, start), person, font=font, fill=255)
                draw_black.text((x_time, start), time_left, font=font, fill=255)
            else:
                #draw_black.text((10, start), ch[:string_length], font=font, fill=0)
                #draw_black.text((380, start), person, font=font, fill=0)
                #draw_black.text((470, start), time_left, font=font, fill=0)
                draw_black.text((x_title, start), ch[:title_chars], font=font, fill=0)
                draw_black.text((x_person, start), person, font=font, fill=0)
                draw_black.text((x_time, start), time_left, font=font, fill=0)
        else:
            # draw_black.text((10, start), ch[:string_length], font=font, fill=0)
            # draw_black.text((380, start), person, font=font, fill=0)
            # draw_black.text((470, start), time_left, font=font, fill=0)
            draw_black.text((x_title, start), ch[:title_chars], font=font, fill=0)
            draw_black.text((x_person, start), person, font=font, fill=0)
            draw_black.text((x_time, start), time_left, font=font, fill=0)

    logging.info("Rendered %s very overdue task(s)", very_overdue_count)
    logging.info("Aktualisiert...")
    
    # Find the minimum chore points of all flatmates
    min_chore_points = 100000
    for i in range(len(wg)):
        name = int(wg_data["flatmates"][i]["id"])
        #points = int(wg_data["flatmates"][i]["chorePoints"]) - int(wg_offset[name])
        points = int(points_data.get("chore", {}).get(str(name), 0)) #new
        if points < min_chore_points:
            min_chore_points = points


    # Find the ACTUAL maximum chore points of all flatmates
    max_chore_points = -100000
    for i in range(len(wg)):
        name = int(wg_data["flatmates"][i]["id"])
        #points_val = int(wg_data["flatmates"][i]["chorePoints"]) - wg_offset[name] - min_chore_points
        points_val = int(points_data.get("chore", {}).get(str(name), 0)) - min_chore_points #new
        if points_val > max_chore_points:
            max_chore_points = points_val

    if enable_working_range:
        working_range_to_max = max_chore_points - working_range_upper_bound
    else:
        working_range_to_max = 0


    # cycle over all flatmates and print their chore points
    for i in range(len(wg)):

        name = int(wg_data["flatmates"][i]["id"])

        # Somehow the chores data doesn't get reset on the backend. Thus I do it here manualy.
        #points_val = int(wg_data["flatmates"][i]["chorePoints"]) - wg_offset[name] - min_chore_points - working_range_to_max
        points_val = int(points_data.get("chore", {}).get(str(name), 0)) - min_chore_points - working_range_to_max #new
        points = str(points_val)

        if points_val < 0 and enable_working_range:
            # points = wg_data["flatmates"][i]["chorePoints"]
            draw_red.text(
                (10 + i * width / 4, height - 2 * fontsize - 27),
                wg[name] + ": " + points,
                font=fontbig,
                fill=0,
            )
        else:
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
    draw_black.text(
        (width / 4 * 3, height - fontsize - 27), wg_name, font=fontbig, fill=0
    )

    epd.display(epd.getbuffer(image_black), epd.getbuffer(image_red))

    logging.info("Goto Sleep...")
    epd.sleep()

except IOError as e:
    logging.info(e)

except KeyboardInterrupt:
    logging.info("ctrl + c:")
    epd_driver.epdconfig.module_exit()
    exit()
