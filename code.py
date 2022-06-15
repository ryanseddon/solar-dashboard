import time
import alarm
import json
import rtc
import adafruit_imageload
from adafruit_datetime import datetime, date, timedelta
from adafruit_magtag.magtag import MagTag
import terminalio
import displayio
from adafruit_display_text import label
import re

try:
    from secrets import secrets
except ImportError:
    print("Credentials and tokens are kept in secrets.py, please add them there!!")
    raise

# ----------------------------
# Define various assets
# ----------------------------
ICONS_SMALL_FILE = "/bmps/Battery-icons.bmp"
BACKGROUND_BMP = "/bmps/solar_bg.bmp"
OVERSUPPLY_BMP = "/bmps/oversupply.bmp"
MATCHING_BMP = "/bmps/matching.bmp"
PARTIAL_BMP = "/bmps/partial.bmp"
IMPORTING_BMP = "/bmps/importing.bmp"

# MagTag sometimes fails to find wifi network this let's us recover from that error
# doesn't seem to work though I still get black screen panics where I need to
# click the reset button, any ideas?
try:
    magtag = MagTag()
    magtag.network.connect()
except (ConnectionError, ValueError, RuntimeError) as e:
    print("*** MagTag(), Some error occured, retrying! -", e)
    # Exit program and restart in 1 seconds.
    magtag.exit_and_deep_sleep(1)

r = rtc.RTC()

# print(adafruit_datetime)

# ----------------------------
# Backgrounnd bitmap
# ----------------------------
magtag.graphics.set_background(BACKGROUND_BMP)

oversupply_bmp, oversupply_pal = adafruit_imageload.load(OVERSUPPLY_BMP)
matching_bmp, matching_pal = adafruit_imageload.load(MATCHING_BMP)
partial_bmp, partial_pal = adafruit_imageload.load(PARTIAL_BMP)
importing_bmp, importing_pal = adafruit_imageload.load(IMPORTING_BMP)

# ----------------------------
# Battery icons sprite sheet
# ----------------------------
icons_small_bmp, icons_small_pal = adafruit_imageload.load(ICONS_SMALL_FILE)


def solar_generation_window():
    """Gets local time from Adafruit IO and converts to RFC3339 timestamp."""
    # Get local time from Adafruit IO
    magtag.get_local_time(secrets["timezone"])
    # Format as RFC339 timestamp
    cur_time = r.datetime
    cur_hour = cur_time[3]
    should_update = False

    if cur_hour >= 7 and cur_hour <= 20:  # Window magtag should be awake
        should_update = True

    return should_update


def get_data():
    resp = magtag.network.fetch(secrets["gist"])
    d = resp.json()
    print(d)
    return (
        d["consumed"] / 1000,
        d["generated"] / 1000,
        d["diff"] / 1000,
        d["sunrise"],
        d["sunset"],
        d["total"]["consumed"] / 1000,
        d["total"]["generated"] / 1000,
        d["total"]["exported"] / 1000,
        d["t_stamp"],
    )


def battery_indicator(x=0, y=0):

    voltage = round(magtag.peripherals.battery, 1)
    dt = 0

    print("Battery voltage: {:3.2f}v".format(voltage))

    if voltage > 4:
        dt = 0
    elif voltage >= 3.9:
        dt = 1
    elif voltage >= 3.8:
        dt = 2
    else:
        dt = 3

    icon = displayio.TileGrid(
        icons_small_bmp,
        pixel_shader=icons_small_pal,
        x=0,
        y=0,
        width=1,
        height=1,
        tile_width=24,
        tile_height=24,
        default_tile=dt,
    )

    group = displayio.Group(x=x, y=y)
    group.append(icon)

    return group


# UI
oversupply_icon = displayio.TileGrid(
    oversupply_bmp,
    pixel_shader=oversupply_pal,
    x=45,
    y=43,
    width=1,
    height=1,
    tile_width=56,
    tile_height=42,
)

matching_icon = displayio.TileGrid(
    matching_bmp,
    pixel_shader=matching_pal,
    x=45,
    y=43,
    width=1,
    height=1,
    tile_width=56,
    tile_height=6,
)

partial_icon = displayio.TileGrid(
    partial_bmp,
    pixel_shader=partial_pal,
    x=45,
    y=43,
    width=1,
    height=1,
    tile_width=56,
    tile_height=42,
)

importing_icon = displayio.TileGrid(
    importing_bmp,
    pixel_shader=importing_pal,
    x=79,
    y=43,
    width=1,
    height=1,
    tile_width=21,
    tile_height=41,
)

panel_power = label.Label(terminalio.FONT, text="Updating", color=0x000000, scale=1)
panel_power.anchor_point = (0, 0)
panel_power.anchored_position = (17, 74)

house_power = label.Label(terminalio.FONT, text="Updating", color=0x000000)
house_power.anchor_point = (0, 0)
house_power.anchored_position = (142, 36)

grid_power = label.Label(terminalio.FONT, text="Updating", color=0x000000)
grid_power.anchor_point = (0, 0)
grid_power.anchored_position = (142, 74)

today_sunrise = label.Label(terminalio.FONT, text="12:12 PM", color=0x000000)
today_sunrise.anchor_point = (0, 0.5)
today_sunrise.anchored_position = (45, 117)

today_sunset = label.Label(terminalio.FONT, text="12:12 PM", color=0x000000)
today_sunset.anchor_point = (0, 0.5)
today_sunset.anchored_position = (130, 117)

# Stats section
stats_consumed = label.Label(terminalio.FONT, text="Updating", color=0x000000)
stats_consumed.anchor_point = (0, 0.5)
stats_consumed.anchored_position = (229, 37)

stats_generated = label.Label(terminalio.FONT, text="Updating", color=0x000000)
stats_generated.anchor_point = (0, 0.5)
stats_generated.anchored_position = (229, 59)

stats_exported = label.Label(terminalio.FONT, text="Updating", color=0x000000)
stats_exported.anchor_point = (0, 0.5)
stats_exported.anchored_position = (229, 85)

stats_tstamp = label.Label(terminalio.FONT, text="Updating", color=0x000000)
stats_tstamp.anchor_point = (0, 0.5)
stats_tstamp.anchored_position = (212, 117)

try:
    print("Fetching solar data...")
    (
        consumed,
        generated,
        diff,
        sunrise,
        sunset,
        s_consumed,
        s_generated,
        s_exported,
        t_stamp,
    ) = get_data()
    
    regex = re.compile(" ")
    tstamp = regex.split(t_stamp)[1]

    solar_banner = displayio.Group()
    if diff > 0 and generated > 0:
        # Solar is meeting house demand and exporting
        solar_banner.append(oversupply_icon)
    elif diff == 0:
        # Solar and demand match
        solar_banner.append(matching_icon)
    elif diff < 0 and generated > 0:
        # Solar is matching partial demand and pulling from grid
        solar_banner.append(partial_icon)
    else:
        solar_banner.append(importing_icon)

    solar_banner.append(panel_power)
    solar_banner.append(house_power)

    if diff < 0:
        grid_power.anchored_position = (136, 74)

    solar_banner.append(grid_power)
    solar_banner.append(today_sunrise)
    solar_banner.append(today_sunset)
    solar_banner.append(stats_consumed)
    solar_banner.append(stats_generated)
    solar_banner.append(stats_exported)
    solar_banner.append(stats_tstamp)

    magtag.splash.append(solar_banner)
    magtag.splash.append(battery_indicator(x=266, y=0))

    print("Should I update:", solar_generation_window())

    # Update battery
    magtag.splash.append(battery_indicator(x=266, y=0))

    panel_power.text = "{:3.3f}kW".format(generated)
    house_power.text = "{:3.3f}kW".format(consumed)
    grid_power.text = "{:3.3f}kW".format(diff)
    today_sunrise.text = sunrise
    today_sunset.text = sunset

    # Stats
    stats_consumed.text = "{:3.1f}kWh".format(s_consumed)
    stats_generated.text = "{:3.1f}kWh".format(s_generated)
    stats_exported.text = "{:3.1f}kWh".format(s_exported)
    stats_tstamp.text = tstamp

    magtag.set_text(" ")
except Exception as e:
    print(e)

sleep_time = 300 if solar_generation_window() else 46800

# Create an alarm that will trigger 300 seconds (5 mins) from now or 10 hours if after 7pm.
time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + sleep_time)
# Exit the program, and then deep sleep until the alarm wakes us.
alarm.exit_and_deep_sleep_until_alarms(time_alarm)
