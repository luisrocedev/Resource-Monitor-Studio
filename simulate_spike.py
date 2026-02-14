from __future__ import annotations

import math
import time


def cpu_spike(seconds: int = 12) -> None:
    end = time.time() + seconds
    x = 0.00001
    while time.time() < end:
        x = math.sin(x) * math.cos(x) * 1.000001


def main() -> None:
    print("Generando pico de CPU para pruebas...")
    cpu_spike(12)
    print("Pico finalizado.")


if __name__ == "__main__":
    main()
