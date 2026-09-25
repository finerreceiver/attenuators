import subprocess
import argparse


PIN1 = [22, 27, 17, 26, 3, 2]
PIN2 = [13, 6, 5, 11, 9, 10]
PIN3 = [14, 15, 18, 23, 24, 25]
PIN4 = [8, 7, 12, 16, 20, 21]

PIN_GROUPS = [PIN1, PIN2, PIN3, PIN4]

WEIGHTS = [0.5, 1, 2, 4, 8, 16]


def run_command(cmd):
    """
    ??????????Python?????????
    ?:
        pinctrl -e set 8 op dh
    """
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def set_pin_level(pin, level):
    """
    1??GPIO?HIGH???LOW????

    level = 1 -> HIGH
    level = 0 -> LOW
    """

    drive = "dh" if level == 1 else "dl"

    cmd = ["pinctrl", "-e", "set", str(pin), "op", drive]

    run_command(cmd)


def set_pins_level(pins, level):
    """
    ???GPIO?????HIGH???LOW????

    level = 1 -> HIGH
    level = 0 -> LOW

    ?:
        pins = [17, 3]
        level = 1

        ?????????:
        pinctrl -e set 17,3 op dh
    """

    if len(pins) == 0:
        return

    drive = "dh" if level == 1 else "dl"

    gpio_list = ",".join(str(pin) for pin in pins)

    cmd = ["pinctrl", "-e", "set", gpio_list, "op", drive]

    run_command(cmd)


def get_pin_state(pin):
    """
    1??GPIO?????????
    """
    cmd = ["pinctrl", "get", str(pin)]
    return run_command(cmd)


def attenuation_to_bits(val):
    """
    ???[dB]?6???????????

    ??:
        bit0 -> 0.5 dB
        bit1 -> 1.0 dB
        bit2 -> 2.0 dB
        bit3 -> 4.0 dB
        bit4 -> 8.0 dB
        bit5 -> 16.0 dB

    ?:
        10 dB = 2 + 8
        bits = [0, 0, 1, 0, 1, 0]
    """

    x = int(round(val * 2))

    bits = [(x >> i) & 1 for i in range(6)]

    return bits


def check_arguments(attid, val):
    """
    ?????????????
    """

    if attid not in [1, 2, 3, 4]:
        raise ValueError("attid must be 1, 2, 3, or 4")

    if val < 0 or val > 31.5:
        raise ValueError("val must be between 0.0 and 31.5 dB")

    if abs(val * 2 - round(val * 2)) > 1e-9:
        raise ValueError("val must be a multiple of 0.5 dB")


def set_att(attid, val):
    """
    ????????????????????
    """

    check_arguments(attid, val)

    pin_group = PIN_GROUPS[attid - 1]
    bits = attenuation_to_bits(val)

    print(f"attenuator id = {attid}")
    print(f"attenuation val = {val} dB")
    print(f"GPIO pins = {pin_group}")
    print(f"bits = {bits}")

    high_pins = []
    low_pins = []

    for pin, bit in zip(pin_group, bits):
        if bit == 1:
            high_pins.append(pin)
        else:
            low_pins.append(pin)

    print(f"HIGH pins = {high_pins}")
    print(f"LOW pins  = {low_pins}")

    # HIGH = ??ON ????
    # ??HIGH?????????????????????????????
    set_pins_level(high_pins, 1)

    # ?????????LOW???????????LOW????
    set_pins_level(low_pins, 0)

    for pin, bit, weight in zip(pin_group, bits, WEIGHTS):
        state = "HIGH" if bit == 1 else "LOW"
        print(f"GPIO{pin}: {state}  ({weight} dB bit)")

    print("\nCurrent pin states:")

    for pin in pin_group:
        print(get_pin_state(pin))


def main():
    parser = argparse.ArgumentParser(
        description="Set attenuator value using pinctrl."
    )

    parser.add_argument(
        "--attid",
        type=int,
        required=True,
        help="attenuator id: 1, 2, 3, or 4",
    )

    parser.add_argument(
        "--val",
        type=float,
        required=True,
        help="attenuation value in dB: 0.0 to 31.5, step 0.5",
    )

    args = parser.parse_args()

    set_att(args.attid, args.val)


if __name__ == "__main__":
    main()
