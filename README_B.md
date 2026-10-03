# waveshark-flatastic

Display Flatastic chores and chore statistics on a Waveshare e-Paper display connected to a Raspberry Pi.

This README documents a **known-working clean installation** starting from an empty microSD card. It also explains how to identify/test the Waveshare panel before running this repository.

## Known-working hardware

This setup has been tested with:

- Raspberry Pi Zero W v1.1 (`armv6l`)
- Waveshare e-Paper Driver HAT Rev 2.2
- Waveshare 7.5" black/white/red displays
  - older 640x384 panel using `epd7in5bc`
  - 7.5" (B) V3, 800x480, using `epd7in5b_V2`

> **Important:** `Driver HAT Rev 2.2` identifies the driver board, **not the attached display panel**. Check the label/revision of the actual e-Paper panel before choosing a driver.

---

## 1. Flash Raspberry Pi OS

Install **Raspberry Pi Imager** on your computer and insert the Raspberry Pi microSD card.

For an original Raspberry Pi Zero / Zero W, select:

- **Device:** Raspberry Pi Zero
- **OS:** Raspberry Pi OS (Legacy, 32-bit) Lite
- **Base:** Debian Bookworm
- **Desktop:** none

The Pi Zero W is an old ARMv6 device, so use the **32-bit** image.

### Raspberry Pi Imager customisation

Configure the OS before writing it to the SD card.

Recommended values:

```text
Hostname: flatpi-yourname
Username: job
Password: choose a strong password
Wi-Fi: your 2.4 GHz Wi-Fi
Wi-Fi country: your country, e.g. CH
Timezone: your timezone, e.g. Europe/Zurich
SSH: enabled
SSH authentication: password authentication
```

The current scripts assume the Linux username is `job`, especially for the font paths under `/home/job/`.

If you choose another username, update the paths in `update_chores.py` and `run.sh`.

Write the image, eject the SD card, insert it into the Pi and boot it.

---

## 2. Connect over SSH

After giving the Pi about 1–3 minutes to boot:

```bash
ping flatpi-yourname.local
```

Then connect:

```bash
ssh job@flatpi-yourname.local
```

If `.local` does not resolve, determine the IP address from your router/network and use:

```bash
ssh job@10.0.0.X
```

---

## 3. Enable SPI

The Waveshare HAT communicates with the Pi over SPI.

Enable it:

```bash
sudo raspi-config nonint do_spi 0
sudo reboot
```

Reconnect and verify:

```bash
ls -l /dev/spidev*
```

Expected:

```text
/dev/spidev0.0
/dev/spidev0.1
```

---

## 4. Install required packages

```bash
sudo apt update

sudo apt install -y \
  git \
  python3-pil \
  python3-requests \
  python3-spidev \
  python3-rpi.gpio \
  python3-pip
```

---

## 5. Install the Waveshare e-Paper library

The setup documented here uses the same Waveshare revision as a known-working installation.

```bash
cd ~

git clone https://github.com/waveshare/e-Paper.git

cd ~/e-Paper

git checkout d56d7b2d4f03c2e978fa1cbd1d1f412b89d60b28
```

Verify:

```bash
git rev-parse HEAD
```

Expected:

```text
d56d7b2d4f03c2e978fa1cbd1d1f412b89d60b28
```

A detached HEAD is expected because the Waveshare repository is deliberately pinned to this known-working revision.

---

## 6. Raspberry Pi Zero / Bookworm Waveshare fix

With the pinned Waveshare revision, a Pi Zero running Bookworm may be incorrectly detected as a Jetson Nano.

A typical symptom is:

```text
OSError: .../sysfs_software_spi.so: wrong ELF class: ELFCLASS64
```

Back up the configuration file and change the fallback platform to Raspberry Pi:

```bash
cd ~/e-Paper/RaspberryPi_JetsonNano/python/lib/waveshare_epd

cp epdconfig.py epdconfig.py.bak

sed -i \
  's/    implementation = JetsonNano()/    implementation = RaspberryPi()/' \
  epdconfig.py
```

Check the result:

```bash
tail -n 15 epdconfig.py
```

The final platform selection should fall back to:

```python
implementation = RaspberryPi()
```

This patch is appropriate for a dedicated Raspberry Pi installation.

---

## 7. Identify the actual e-Paper panel

Do **not** choose the display driver only from the HAT revision.

Inspect the label on the actual panel and determine:

- physical size
- resolution
- black/white or black/white/red
- panel revision, e.g. V2, V3, HD
- model number if available

You can list the available 7.5" Waveshare examples with:

```bash
cd ~/e-Paper/RaspberryPi_JetsonNano/python/examples

ls | grep -i 7in5
```

Useful known configurations for this project:

| Panel | Resolution | Colours | Python driver | Waveshare test |
|---|---:|---|---|---|
| older 7.5" BC | 640x384 | black/white/red | `epd7in5bc` | `epd_7in5bc_test.py` |
| 7.5" B V2/V3 | 800x480 | black/white/red | `epd7in5b_V2` | `epd_7in5b_V2_test.py` |
| 7.5" V2 | 800x480 | black/white | `epd7in5_V2` | `epd_7in5_V2_test.py` |

For the **7.5" B V3 black/white/red 800x480 panel**, test:

```bash
cd ~/e-Paper/RaspberryPi_JetsonNano/python/examples

python3 epd_7in5b_V2_test.py
```

Only continue once the official Waveshare test works correctly.

This isolates hardware/SPI/driver problems from application problems.

---

## 8. Clone waveshark-flatastic

```bash
cd ~

git clone https://github.com/Mjolnirius/waveshark-flatastic.git

cd ~/waveshark-flatastic
```

If the adaptive display version is currently on the `adaptive-display` branch:

```bash
git fetch origin
git switch adaptive-display
git pull
```

If that work has already been merged into the repository's default branch, this step is not necessary.

Check that the adaptive code is present:

```bash
grep -nE "DISPLAY_DRIVER|epd_driver|scale_x" update_chores.py
```

---

## 9. Choose the display driver

The repository supports multiple display versions from the same codebase.

The display driver is configured together with the local Flatastic settings in `secrets_api_etc.py`. Create that file as described in the next section, then edit it:

```bash
nano secrets_api_etc.py
```

### 7.5" B V3 — 800x480 black/white/red

```python
DISPLAY_DRIVER = "epd7in5b_V2"
```

### Older 7.5" BC — 640x384 black/white/red

```python
DISPLAY_DRIVER = "epd7in5bc"
```

The layout scales horizontally from its original 640-pixel reference layout, so the same application code can run on both 640x384 and 800x480 displays.

---

## 10. Configure Flatastic secrets

Create the local secrets file:

```bash
cd ~/waveshark-flatastic

cp secrets_api_etc_mock.py secrets_api_etc.py
```

Edit it:

```bash
nano secrets_api_etc.py
```

Fill in the values required by the mock file, including the display driver, your Flatastic API key, flatmate mapping and WG settings.

The application currently imports:

```python
DISPLAY_DRIVER
enable_very_overdue_format
enable_working_range
very_overdue_one_time_days
very_overdue_threshold_percent
wg
wg_name
wg_offset
working_range_upper_bound
x_api_key
```

### Very overdue task formatting

Very overdue tasks can be shown as white text on a red background
with a six-pixel black frame around the existing row bounds. The feature is on
by default:

```python
enable_very_overdue_format = True
very_overdue_threshold_percent = 50
very_overdue_one_time_days = 10
```

The threshold is a percentage of the task frequency. With a 14-day frequency
and a 50% threshold, the special format starts once the task is 7 days overdue.
Set `enable_very_overdue_format` to `False` to retain the normal white-on-red
format for every overdue task. One-time tasks have no recurring frequency, so
they use the special format only after they are more than
`very_overdue_one_time_days` overdue. Tasks configured as "only when necessary"
remain excluded from the display.

### Obtaining the Flatastic API key

Use the Flatastic web application in your browser and inspect its network requests in the browser developer tools.

Look for requests to the Flatastic API and copy the value of the:

```text
x-api-key
```

request header.

Treat this key like a password.

Make sure `.gitignore` contains:

```gitignore
secrets_api_etc.py
```

Never commit the real secrets file.

---

## 11. Install the required fonts

The current layout expects these files:

```text
/home/job/.fonts/CousineNerdFont-Bold.ttf
/home/job/.fonts/CousineNerdFont-BoldItalic.ttf
```

Create the directory:

```bash
mkdir -p ~/.fonts
```

Copy/install the two Cousine Nerd Font files there.

Verify:

```bash
ls -lah ~/.fonts
```

Expected filenames:

```text
CousineNerdFont-Bold.ttf
CousineNerdFont-BoldItalic.ttf
```

---

## 12. Test the repository manually

The Waveshare Python package lives outside this repository, so add its `lib` directory to `PYTHONPATH` when running the application:

```bash
cd ~/waveshark-flatastic

PYTHONPATH=/home/job/e-Paper/RaspberryPi_JetsonNano/python/lib \
python3 update_chores.py
```

If everything is configured correctly, the display should refresh and show the Flatastic chore screen.

Do this manually before configuring cron.

---

## 13. Create a launcher

Create `run.sh`:

```bash
cd ~/waveshark-flatastic

cat > run.sh <<'EOF'
#!/bin/bash
export PYTHONPATH=/home/job/e-Paper/RaspberryPi_JetsonNano/python/lib
exec /usr/bin/python3 /home/job/waveshark-flatastic/update_chores.py
EOF

chmod +x run.sh
```

Test it:

```bash
./run.sh
```

---

## 14. Run automatically with cron

Edit the user's crontab:

```bash
crontab -e
```

Example: update every 15 minutes between 08:00 and 22:59:

```cron
*/15 8-22 * * * /home/job/waveshark-flatastic/run.sh >> /home/job/flatastic.log 2>&1
```

Verify:

```bash
crontab -l
```

Inspect logs:

```bash
tail -50 ~/flatastic.log
```

Once the setup is stable, you may redirect output to `/dev/null` instead.

---

## 15. Updating the application

Because the application now runs directly from the Git repository, updating is simple:

```bash
cd ~/waveshark-flatastic

git pull

./run.sh
```

`secrets_api_etc.py` remains local and is not overwritten by normal Git updates.

---

## Optional: Tailscale

Tailscale can be useful for remote administration of a headless Pi.

The original Raspberry Pi Zero W is an ARMv6 machine, so test the currently available Tailscale build/features on your device rather than assuming every newer feature is supported.

Tailscale is independent of the e-Paper application and is not required to run this repository.

---

# Development workflow

## Raspberry Pi Zero W and VS Code Remote SSH

The original Pi Zero W is `armv6l`.

Modern VS Code Server / Remote SSH does not support this platform well, so a practical workflow is:

1. edit the repository locally on your computer using VS Code/Codex
2. commit and push changes
3. `git pull` on the Pi
4. run `./run.sh`

For quick testing you can also copy a file from Windows:

```powershell
scp .\update_chores.py job@flatpi-yourname.local:/home/job/waveshark-flatastic/update_chores.py
```

Then execute remotely:

```powershell
ssh job@flatpi-yourname.local "cd /home/job/waveshark-flatastic && ./run.sh"
```

---

# Troubleshooting

## `ModuleNotFoundError: No module named 'waveshare_epd'`

The application is being run directly from this repository, while the Waveshare package lives in:

```text
/home/job/e-Paper/RaspberryPi_JetsonNano/python/lib
```

Run with:

```bash
PYTHONPATH=/home/job/e-Paper/RaspberryPi_JetsonNano/python/lib \
python3 update_chores.py
```

or use `run.sh`.

---

## `wrong ELF class: ELFCLASS64`

Example:

```text
OSError: .../sysfs_software_spi.so: wrong ELF class: ELFCLASS64
```

The pinned Waveshare code has misidentified the Raspberry Pi as a Jetson Nano.

Apply the `epdconfig.py` Raspberry Pi fallback patch described in **Step 6**.

---

## Display test works, but application uses only part of the screen

The original application layout was designed for a 640-pixel-wide display.

Use the adaptive display version of the repository. It reads the real:

```python
epd.width
epd.height
```

and scales the original horizontal coordinates relative to a 640-pixel base width.

Check:

```bash
grep -nE "scale_x|x_person|x_time|row_right" update_chores.py
```

For an 800-pixel display, `scale_x` should become:

```text
1.25
```

---

## Wrong colours / corrupted output / display behaves strangely

Stop testing and verify the actual panel model.

Do not infer the panel model from:

```text
e-Paper Driver HAT Rev 2.2
```

That is only the controller/HAT revision.

Identify the e-Paper panel itself and run the matching official Waveshare test before using this application.

---

## SPI devices do not exist

Check:

```bash
ls /dev/spidev*
```

If nothing is returned:

```bash
sudo raspi-config nonint do_spi 0
sudo reboot
```

---

## Hostname does not resolve

If:

```bash
ssh job@flatpi-yourname.local
```

does not work, determine the Pi's IP address from the router/network and connect directly:

```bash
ssh job@10.0.0.X
```

The Pi Zero W supports **2.4 GHz Wi-Fi**, not 5 GHz-only Wi-Fi.

---

# Security notes

Do not commit:

```text
secrets_api_etc.py
```

At minimum, `.gitignore` should contain:

```gitignore
secrets_api_etc.py
__pycache__/
*.pyc
*.save
.vscode/
```

The Flatastic `x-api-key` should be treated as a secret.

---

# Known-working software stack

The installation described above has been tested with a setup based on:

```text
Raspberry Pi Zero W v1.1
Raspberry Pi OS Lite 32-bit
Debian Bookworm
SPI enabled
Python 3
Waveshare e-Paper repository
Waveshare commit:
d56d7b2d4f03c2e978fa1cbd1d1f412b89d60b28
```

A previous working installation used Raspberry Pi OS Bullseye / Python 3.9. The Bookworm setup documented here has also been tested successfully after applying the Waveshare Raspberry Pi platform-detection fix.

---

# Quick checklist

Before blaming the application, verify in this order:

1. Raspberry Pi boots and SSH works.
2. `/dev/spidev0.0` and `/dev/spidev0.1` exist.
3. The actual e-Paper panel model/revision is known.
4. The matching official Waveshare example works.
5. `secrets_api_etc.py` selects the correct driver and contains valid local settings.
6. Both required fonts exist under `/home/job/.fonts/`.
7. `update_chores.py` works manually with `PYTHONPATH`.
8. `run.sh` works.
9. Only then enable the cron job.
