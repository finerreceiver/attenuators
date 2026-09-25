import subprocess
import argparse
import json
import numpy as np


PIN1 = [22, 27, 17, 26, 3, 2]
PIN2 = [13, 6, 5, 11, 9, 10]
PIN3 = [14, 15, 18, 23, 24, 25]
PIN4 = [8, 7, 12, 16, 20, 21]

PIN_GROUPS = [PIN1, PIN2, PIN3, PIN4]

WEIGHTS = np.array([0.5, 1, 2, 4, 8, 16], dtype=float)


def read_pin_level(pin):
    """
    pinctrl get <pin> ??????
    GPIO???? 0 or 1 ??????

    op ???:
        hi -> 1
        lo -> 0

    ip ???:
        ???????????????
    """

    result = subprocess.run(
        ["pinctrl", "get", str(pin)],
        capture_output=True,
        text=True,
        check=True,
    )

    output = result.stdout.strip()
    output_lower = output.lower()

    # input mode ???hi/lo ???????????
    if " ip" in output_lower or "| ip" in output_lower or "\tip" in output_lower:
        raise RuntimeError(
            f"GPIO{pin} is input mode (ip), not output mode (op): {output}"
        )

    if " hi" in output_lower or "| hi" in output_lower or "\thi" in output_lower:
        return 1, output

    if " lo" in output_lower or "| lo" in output_lower or "\tlo" in output_lower:
        return 0, output

    raise RuntimeError(f"Could not parse pin state for GPIO{pin}: {output}")


def calc_att(pin_group):
    """
    6??GPIO???????[dB]??????
    """

    values = []
    raw_outputs = []

    for pin in pin_group:
        level, raw_output = read_pin_level(pin)
        values.append(level)
        raw_outputs.append(raw_output)

    values = np.array(values, dtype=float)
    att = float(np.sum(values * WEIGHTS))

    return att, values.astype(int).tolist(), raw_outputs


def get_att():
    """
    ????????????????
    """

    results = []

    for pin_group in PIN_GROUPS:
        att, values, raw_outputs = calc_att(pin_group)
        results.append((att, values, raw_outputs))

    return results


def make_output_json(mode):
    """
    mode????JSON??????????

    mode = "val"
        ??????????????????

    mode = "pin"
        ???????????GPIO???????????
    """

    results = get_att()

    if mode == "val":
        values = {}

        for attid, (att, pin_values, raw_outputs) in enumerate(results, start=1):
            values[str(attid)] = f"{att:.1f}"

        output = {
            "mode": "val",
            "values": values,
        }

        return output

    if mode == "pin":
        values = {}

        for attid, (att, pin_values, raw_outputs) in enumerate(results, start=1):
            pin_group = PIN_GROUPS[attid - 1]

            pin_states = {}

            for pin, level in zip(pin_group, pin_values):
                pin_states[str(pin)] = level

            values[str(attid)] = pin_states

        output = {
            "mode": "pin",
            "values": values,
        }

        return output

    raise ValueError("mode must be 'val' or 'pin'")


def main():
    parser = argparse.ArgumentParser(
        description="Get attenuator states using pinctrl and output JSON."
    )

    parser.add_argument(
        "--mode",
        type=str,
        choices=["val", "pin"],
        required=True,
        help="output mode: val = attenuation values, pin = GPIO pin states",
    )

    parser.add_argument(
        "--pretty",
        action="store_true",
        help="pretty-print JSON",
    )

    args = parser.parse_args()

    output = make_output_json(args.mode)

    if args.pretty:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()