## update this file with your own values and rename it to secrets_api.py


## device configuration:
# Waveshare 640x384 black/white/red display:
DISPLAY_DRIVER = "epd7in5bc"

# Waveshare 7.5" B V3, 800x480 black/white/red display:
# DISPLAY_DRIVER = "epd7in5b_V2"


## Working range configuration:
# Keeps the leaderboard relative: the top scorer is set to the upper bound
# (for example, 15 points), while all other scores retain the same differences to the top scorer.
enable_working_range = True
working_range_upper_bound = 15


## Flatmate Configuration:
# Check on https://www.flatastic-app.com/webapp/ to get your WG ID and the corresponding offsets for each member.
wg = {
    100: "Anna",
    101: "Betty",
    102: "Charlie",
    103: "Dennis",
}

wg_offset = {
    100: 10,
    101: 5,
    102: 3,
    103: 0,
}

wg_name = "My cool flat"

x_api_key = "abcdefghlkmnopqrstuvwxyz"
