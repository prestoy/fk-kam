# fk-kam – Bevegelsesdeteksjon med Motion og Raspberry Pi

Oppsett for bevegelsesdeteksjon via RTSP-strøm fra en Raspberry Pi 3B til en Ubuntu 24.04-PC ved hjelp av [Motion 4.6](https://motion-project.github.io/).

---

## Innhold

```
fk-kam/
├── motion_fk-kam.conf       # Motion-konfigurasjon
├── rtsp-server.py           # RTSP-strømserver (kjøres på Raspberry Pi)
├── motion-watchdog.sh       # Watchdog-skript mot hengte prosesser
└── clips/                   # Lagrede videosekvenser (ikke inkludert i repo)
```

---

## Krav

### Raspberry Pi (kilde)
- Raspberry Pi 3B med kamera
- GStreamer med `libcamerasrc` og `x264enc`
- Python 3 med `python3-gi` og GStreamer-bindinger

### Ubuntu PC (mottaker)
- Ubuntu 24.04
- Motion 4.6.0 (`sudo apt install motion`)
- FFmpeg (for RTSP-dekoding)
- ffprobe (del av `ffmpeg`-pakken, brukes av watchdog)

---

## Installasjon

### 1. Klon repoet

```bash
git clone <repo-url> ~/fk-kam
cd ~/fk-kam
```

### 2. Opprett nødvendige mapper

```bash
mkdir -p ~/fk-kam/clips
sudo mkdir -p /mnt/fk-kam/clips   # Juster til din lagringsdisk
```

### 3. Start RTSP-server på Raspberry Pi

Kopier `rtsp-server.py` til Pi-en og kjør:

```bash
python3 rtsp-server.py
```

Strømmen er tilgjengelig på `rtsp://<PI_IP>:8554/stream`.

### 4. Tilpass konfigurasjonsfilen

Rediger `motion_fk-kam.conf` og juster:

```
netcam_url rtsp://<PI_IP>:8554/stream   # IP-adressen til Pi-en
target_dir /mnt/fk-kam/clips            # Ønsket lagringsmappe
log_file /home/<bruker>/fk-kam/motion.log
pid_file /home/<bruker>/fk-kam/motion.pid
```

### 5. Start Motion manuelt (for testing)

```bash
motion -c ~/fk-kam/motion_fk-kam.conf
tail -f ~/fk-kam/motion.log
```

---

## Automatisk oppstart med systemd

### Motion-tjeneste

Opprett `/etc/systemd/system/motion-fk-kam.service`:

```ini
[Unit]
Description=Motion bevegelsesdeteksjon - fk-kam
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=stale
ExecStart=/usr/bin/motion -c /home/stale/fk-kam/motion_fk-kam.conf
Restart=on-failure
RestartSec=15s
StartLimitIntervalSec=300
StartLimitBurst=5
TimeoutStopSec=10s
KillMode=process

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now motion-fk-kam.service
sudo systemctl status motion-fk-kam.service
```

### Watchdog-timer

Watchdog-skriptet sjekker om strømmen er tilgjengelig og restarter Motion hvis den har vært nede i over 60 sekunder.

Opprett `/etc/systemd/system/motion-watchdog.service`:

```ini
[Unit]
Description=Motion watchdog

[Service]
Type=oneshot
User=root
ExecStart=/home/stale/fk-kam/motion-watchdog.sh
```

Opprett `/etc/systemd/system/motion-watchdog.timer`:

```ini
[Unit]
Description=Motion watchdog timer

[Timer]
OnBootSec=60s
OnUnitActiveSec=15s

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now motion-watchdog.timer
```

---

## Robusthet

### Tilkoblingstimeout

Konfigen er satt opp med eksplisitte timeouts for å forhindre at Motion henger stille ved tap av RTSP-strøm:

```
netcam_params keepalive=on,reconnect=on
netcam_connect_timeout 15
netcam_read_timeout 15
```

### Loggrotasjon

Opprett `/etc/logrotate.d/motion-fk-kam` for å forhindre at loggfilen vokser ubegrenset:

```
/home/stale/fk-kam/motion.log {
    daily
    rotate 14
    compress
    missingok
    notifempty
    copytruncate
}
```

### Automatisk sletting av gamle klipp

Legg til i crontab (`crontab -e`) for å slette klipp eldre enn 30 dager:

```cron
0 3 * * * find /mnt/fk-kam/clips -name "*.mp4" -mtime +30 -delete
```

### Pause og gjenoppta deteksjon

Bruk Motions webcontrol-API til å pause deteksjon i et gitt tidsrom, f.eks. om natten:

```cron
0 23 * * * curl -s "http://localhost:8080/0/detection/pause"
0  6 * * * curl -s "http://localhost:8080/0/detection/start"
```

Sjekk status:

```bash
curl http://localhost:8080/0/detection/status
```

---

## Feilsøking

| Problem | Løsning |
|--------|---------|
| `Permission denied` på loggfil | Sjekk at `log_file` peker til en mappe du eier |
| Motion starter ikke etter reboot | Sjekk at lagringsdisken er montert før tjenesten starter |
| Doble instanser av Motion | `pid_file` i konfigen forhindrer dette |
| Strømmen fryser uten at Motion krasjer | Watchdog-timeren håndterer dette |
| Disk full | Sett opp cron-jobb for automatisk sletting av gamle klipp |

---

## Lisens

MIT
