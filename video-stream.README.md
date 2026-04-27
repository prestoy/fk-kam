# Fuglekassekamera – Sjentemarka, Trondheim

Raspberry Pi-basert fuglekassekamera med automatisk lysstyring og RTSP-videostrøm.

## Maskinvare

| Komponent | Spesifikasjon |
|---|---|
| Datamaskin | Raspberry Pi 3B |
| Kamera | Raspberry Pi Camera Module (uten IR-filter) |
| Lyssensor | Ingen – lysstyring basert på soloppgang/solnedgang |
| LED | 2 × varmhvit LED, 2700–3300K, 5800 mcd, innebygd motstand |
| Transistor | PN2222 (TO-92) |
| Motstand | 1 kΩ (base-motstand) |
| Strøm til LED | 5V fra Pi via transistor på GPIO 18 |

### Transistor-kobling (PN2222, flat side mot deg, ben ned)

```
[ flatt ]
  | | |
  E B C
```

- **Venstre (E)** → GND
- **Midtre (B)** → 1 kΩ → GPIO 18 (pin 12)
- **Høyre (C)** → LED-katoder (korte ben)

LED-anoder (lange ben) kobles til 5V (pin 2).

---

## Programvare

### Avhengigheter

```bash
sudo apt update && sudo apt upgrade -y

# GStreamer og RTSP
sudo apt install -y \
    python3-gi \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-rtsp \
    libgstrtspserver-1.0-dev \
    python3-gst-1.0 \
    gir1.2-gst-rtsp-server-1.0 \
    libcamera-apps \
    gstreamer1.0-libcamera \
    ffmpeg

# Python-biblioteker
pip install astral --break-system-packages
```

---

## Skripter

### fk-lys.py – Lysstyring

Styrer LED-lyset i fuglekassen via PWM på GPIO 18. Lyset slås på ved soloppgang og av ved solnedgang, beregnet for Trondheim (63.4305°N, 10.3951°Ø).

Bruker `lgpio` direkte (følger med Raspberry Pi OS).

**Konfigurasjon i toppen av skriptet:**

| Parameter | Standard | Beskrivelse |
|---|---|---|
| `GPIO_PIN` | 18 | PWM-pin til transistorens base |
| `FREKVENS` | 1000 Hz | PWM-frekvens |
| `LYSSTYRKE` | 100 % | Lysstyrke når lyset er på |
| `LOKASJON` | Trondheim | Koordinater for solberegning |

**Kjør manuelt:**
```bash
python3 fk-lys.py
```

---

### rtsp-server.py – Videostrøm

Starter en RTSP-server på port 8554 og strømmer video fra kameraet via GStreamer.

**Strøminnstillinger:**

| Parameter | Verdi | Beskrivelse |
|---|---|---|
| Oppløsning | 960×720 | |
| Framerate | 15 fps | |
| Eksponeringstid | 40 000 µs | Manuell, fast |
| Analog forsterkning | 15.0 | Manuell, fast |
| Hvitbalanse | awb-mode=1 | Incandescent – passer til varmhvit LED |
| Bitrate | 1000 kbps | H.264 |
| Transportprotokoll | TCP | Anbefalt for stabilitet |

**Se strømmen:**
```bash
# Linux
mpv rtsp://<PI_IP>:8554/stream

# Verifiser uten å se bilde
ffprobe rtsp://<PI_IP>:8554/stream
```

---

## Systemd-tjenester

### fk-lys.service

```ini
[Unit]
Description=Fuglekasse lysstyring
After=network.target

[Service]
Type=simple
User=stale
WorkingDirectory=/home/stale/fk-kam
ExecStart=/usr/bin/python3 /home/stale/fk-kam/fk-lys.py
Restart=on-failure
RestartSec=30
StandardOutput=null
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Installer tjenester

```bash
sudo cp fk-lys.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable fk-lys
sudo systemctl start fk-lys
```

### Nyttige kommandoer

```bash
# Status
sudo systemctl status fk-lys

# Logg
tail -f /var/log/fuglekasse_lys.log

# CPU-temperatur
vcgencmd measure_temp

# CPU-belastning
htop
```

---

## Strømsparing

Følgende er deaktivert for å redusere strømforbruk:

```bash
# Bluetooth
echo "dtoverlay=disable-bt" | sudo tee -a /boot/config.txt

# HDMI
vcgencmd display_power 0

# Unødvendige tjenester
sudo systemctl disable avahi-daemon
sudo systemctl disable triggerhappy
sudo systemctl disable ModemManager
```

---

## Mappestruktur

```
/home/stale/fk-kam/
├── fk-lys.py           # Lysstyring
├── rtsp-server.py      # RTSP-videostrøm
├── fk-youtube.py       # Daglig opplasting til YouTube
├── klipp/              # Bevegelsesutløste klipp
└── arkiv/              # Arkiverte klipp etter opplasting
```
