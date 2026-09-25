import subprocess
import argparse
import json


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


def set_pins_level(pins, level):
    """
    ???GPIO?????HIGH???LOW????

    level = 1 -> HIGH
    level = 0 -> LOW
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


def parse_json_values(json_text):
    """
    JSON??????????
    {attid: val} ?????????

    ???:
        {"1": "31.5", "2": "10"}

    ???:
        {
            1: 31.5,
            2: 10.0
        }
    """

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")

    if not isinstance(data, dict):
        raise ValueError("JSON must be an object like {'1': '31.5', '2': '10'}")

    if len(data) == 0:
        raise ValueError("JSON must not be empty")

    settings = {}

    for attid_text, val_text in data.items():
        try:
            attid = int(attid_text)
        except ValueError:
            raise ValueError(f"attid must be 1, 2, 3, or 4: {attid_text}")

        try:
            val = float(val_text)
        except ValueError:
            raise ValueError(f"attenuation value must be a number: {val_text}")

        check_arguments(attid, val)

        settings[attid] = val

    return settings
def set_atts(settings):
    """
    ???????????????????

    HIGH = ??ON ?????
    ?????????????HIGH???pin???????
    ???LOW???pin?????
    """

    all_high_pins = []
    all_low_pins = []

    info_list = []

    for attid in sorted(settings.keys()):
        val = settings[attid]

        check_arguments(attid, val)

        pin_group = PIN_GROUPS[attid - 1]
        bits = attenuation_to_bits(val)

        high_pins = []
        low_pins = []

        for pin, bit in zip(pin_group, bits):
            if bit == 1:
                high_pins.append(pin)
                all_high_pins.append(pin)
            else:
                low_pins.append(pin)
                all_low_pins.append(pin)

        info_list.append(
            {
                "attid": attid,
                "val": val,
                "pin_group": pin_group,
                "bits": bits,
                "high_pins": high_pins,
                "low_pins": low_pins,
            }
        )

    print("=" * 40)
    print("Requested settings:")

    for info in info_list:
        print("-" * 40)
        print(f"attenuator id = {info['attid']}")
        print(f"attenuation val = {info['val']:.1f} dB")
        print(f"GPIO pins = {info['pin_group']}")
        print(f"bits = {info['bits']}")
        print(f"HIGH pins = {info['high_pins']}")
        print(f"LOW pins  = {info['low_pins']}")

    print("-" * 40)
    print(f"All HIGH pins = {all_high_pins}")
    print(f"All LOW pins  = {all_low_pins}")

    # ???
    # HIGH = ??ON ????
    # ?????HIGH??????????
    # ????????????????????
    set_pins_level(all_high_pins, 1)

    # ????LOW???????
    set_pins_level(all_low_pins, 0)

    print("\nCurrent pin states:")

    for info in info_list:
        print("-" * 40)
        print(f"attenuator id = {info['attid']}")

        for pin, bit, weight in zip(info["pin_group"], info["bits"], WEIGHTS):
            state = "HIGH" if bit == 1 else "LOW"
            print(f"GPIO{pin}: expected {state}  ({weight} dB bit)")
            print(get_pin_state(pin))

    print("=" * 40)
    print("Done.")


def main():
    parser = argparse.ArgumentParser(
        description="Set attenuator values using JSON and pinctrl."
    )

    parser.add_argument(
        "--vals",
        type=str,
        required=True,
        help='JSON string. Example: \'{"1": "31.5", "2": "10"}\'',
    )

    args = parser.parse_args()

    settings = parse_json_values(args.vals)

    set_atts(settings)


if __name__ == "__main__":
    main()