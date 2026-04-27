#!/usr/bin/env python3
"""
Lysstyring for fuglekasse basert på soloppgang/solnedgang
Lokasjon: Trondheim (63.4305° N, 10.3951° Ø)
Buffer: 30 minutter (lyset slås på 30 min før solnedgang,
        og slås av 30 min etter soloppgang)

Installer avhengigheter:
  pip install astral --break-system-packages

lgpio følger med Raspberry Pi OS og trenger ikke installeres.
"""

import time
import logging
from datetime import datetime, date
import lgpio
from astral import LocationInfo
from astral.sun import sun
from datetime import datetime, date, timedelta

# ── Konfigurasjon ──────────────────────────────────────────────
GPIO_PIN   = 18      # PWM-pin til transistorens base
FREKVENS   = 1000    # PWM-frekvens i Hz
LYSSTYRKE  = 100     # Prosent (0–100) når lyset er på
LYSSTYRKE  = 100     # Prosent (0–100) når lyset er på
BUFFER_MIN = 30      # Minutter etter soloppgang og før solnedgang

LOKASJON = LocationInfo(
    name      = "Trondheim",
    region    = "Norway",
    timezone  = "Europe/Oslo",
    latitude  = 63.4305,
    longitude = 10.3951,
)

LOGGFIL = "fuglekasse_lys.log"
# ───────────────────────────────────────────────────────────────

logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(LOGGFIL),
        logging.StreamHandler(),
    ]
)
log = logging.getLogger(__name__)


def sett_pwm(chip, prosent):
    """Sett lysstyrke via PWM. 0 = av, 100 = fullt på."""
    lgpio.tx_pwm(chip, GPIO_PIN, FREKVENS, max(0.0, min(100.0, prosent)))


def hent_tider(dato: date) -> tuple[datetime, datetime]:
    """Returner (lys_på, lys_av) for en gitt dato.
    Lyset slås på ved soloppgang + buffer og av ved solnedgang - buffer.
    """
    s = sun(LOKASJON.observer, date=dato, tzinfo=LOKASJON.timezone)
    lys_paa = s["sunrise"] + timedelta(minutes=BUFFER_MIN)
    lys_av  = s["sunset"]  - timedelta(minutes=BUFFER_MIN)
    return lys_paa, lys_av


def skal_lyse(lys_paa: datetime, lys_av: datetime) -> bool:
    """
    Avgjør om lyset skal være på nå.
    Lyset er på mellom soloppgang (+ buffer) og solnedgang (- buffer),
    dvs. om dagen. Dette tidsvinduet krysser aldri midnatt.
    """
    naa = datetime.now(tz=lys_paa.tzinfo)
    return lys_paa <= naa <= lys_av


def main():
    chip = lgpio.gpiochip_open(0)
    lgpio.gpio_claim_output(chip, GPIO_PIN, 0)

    lys_er_paa = False

    log.info("=" * 55)
    log.info("Lysstyring fuglekasse startet")
    log.info(f"Lokasjon : {LOKASJON.name} ({LOKASJON.latitude}°N)")
    log.info(f"GPIO-pin : {GPIO_PIN}")
    log.info("=" * 55)

    try:
        while True:
            i_dag = date.today()
            lys_paa, lys_av = hent_tider(i_dag)
            paa_naa = skal_lyse(lys_paa, lys_av)

            if paa_naa and not lys_er_paa:
                sett_pwm(chip, LYSSTYRKE)
                lys_er_paa = True
                log.info(f"LYS PÅ  – soloppgang kl. {lys_paa.strftime('%H:%M')}")

            elif not paa_naa and lys_er_paa:
                sett_pwm(chip, 0)
                lys_er_paa = False
                log.info(f"LYS AV  – solnedgang kl. {lys_av.strftime('%H:%M')}")

            time.sleep(60)  # Sjekk hvert minutt

    except KeyboardInterrupt:
        log.info("Avsluttet av bruker.")
    finally:
        sett_pwm(chip, 0)
        lgpio.gpiochip_close(chip)
        log.info("GPIO ryddet opp.")


if __name__ == "__main__":
    main()
