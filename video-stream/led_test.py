#!/usr/bin/env python3
"""
Manuell test av LED-kobling i fuglekasse

Bruk:
  python3 led_test.py on       – slå på LED (fullt lys)
  python3 led_test.py off      – slå av LED
  python3 led_test.py blink    – blink 5 ganger (bekreft kobling)
  python3 led_test.py dim 50   – sett lysstyrke til 50% (0–100)
  python3 led_test.py status   – vis nåværende tilstand

Ingen ekstra biblioteker nødvendig – lgpio følger med Raspberry Pi OS.
"""

import sys
import time
import lgpio

# ── Konfigurasjon ──────────────────────────────────────────────
GPIO_PIN = 18      # Samme pin som i fuglekasse_lys.py
FREKVENS = 1000    # PWM-frekvens i Hz
# ───────────────────────────────────────────────────────────────

HJELP = """
Bruk: python3 led_test.py <kommando> [verdi]

Kommandoer:
  on            Slå på LED (100% lysstyrke)
  off           Slå av LED
  blink         Blink 5 ganger – bekreft at koblingen virker
  dim <0-100>   Sett lysstyrke i prosent, f.eks: dim 50
  status        Vis GPIO-pinens nåværende tilstand

Eksempler:
  python3 led_test.py on
  python3 led_test.py dim 75
  python3 led_test.py blink
"""

def setup():
    chip = lgpio.gpiochip_open(0)
    lgpio.gpio_claim_output(chip, GPIO_PIN, 0)
    return chip

def sett_pwm(chip, prosent):
    """Sett lysstyrke via PWM. 0 = av, 100 = fullt på."""
    lgpio.tx_pwm(chip, GPIO_PIN, FREKVENS, max(0.0, min(100.0, prosent)))

def stopp(chip):
    """Slå av PWM og frigjør GPIO."""
    sett_pwm(chip, 0)
    lgpio.gpiochip_close(chip)

def kommando_on(chip):
    sett_pwm(chip, 100)
    print(f"LED PÅ – fullt lys (GPIO {GPIO_PIN})")

def kommando_off(chip):
    sett_pwm(chip, 0)
    print(f"LED AV (GPIO {GPIO_PIN})")

def kommando_blink(chip):
    print(f"Blinker 5 ganger på GPIO {GPIO_PIN} ...")
    try:
        for i in range(5):
            sett_pwm(chip, 100)
            print(f"  Blink {i + 1}/5 – PÅ")
            time.sleep(0.5)
            sett_pwm(chip, 0)
            print(f"  Blink {i + 1}/5 – AV")
            time.sleep(0.5)
        print("Ferdig. Hvis LED blinket er koblingen i orden.")
    except KeyboardInterrupt:
        print("\nAvbrutt.")

def kommando_dim(chip, args):
    if len(args) < 3:
        print("Feil: oppgi lysstyrke mellom 0 og 100.")
        print("Eksempel: python3 led_test.py dim 50")
        return
    try:
        styrke = float(args[2])
    except ValueError:
        print(f"Feil: '{args[2]}' er ikke et gyldig tall.")
        return
    if not 0 <= styrke <= 100:
        print("Feil: lysstyrke må være mellom 0 og 100.")
        return
    sett_pwm(chip, styrke)
    print(f"LED satt til {styrke:.0f}% lysstyrke (GPIO {GPIO_PIN})")
    print("Trykk Ctrl+C for å slukke og avslutte.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nSlukker LED.")
        kommando_off(chip)

def kommando_status(chip):
    tilstand = lgpio.gpio_read(chip, GPIO_PIN)
    print(f"GPIO {GPIO_PIN} tilstand: {'HØY (PÅ)' if tilstand else 'LAV (AV)'}")

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(HJELP)
        sys.exit(0)

    kommando = sys.argv[1].lower()
    chip = setup()

    try:
        if kommando == "on":
            kommando_on(chip)
        elif kommando == "off":
            kommando_off(chip)
        elif kommando == "blink":
            kommando_blink(chip)
        elif kommando == "dim":
            kommando_dim(chip, sys.argv)
        elif kommando == "status":
            kommando_status(chip)
        else:
            print(f"Ukjent kommando: '{kommando}'")
            print(HJELP)
    finally:
        pass
#        stopp(chip)

if __name__ == "__main__":
    main()
