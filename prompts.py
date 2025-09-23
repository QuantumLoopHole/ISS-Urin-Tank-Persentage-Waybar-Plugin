import subprocess


def ask_user(question, options=("Yes", "No")):
    try:
        rofi = subprocess.run(
            ["rofi", "-dmenu", "-p", question],
            input="\n".join(options).encode(),
            capture_output=True,
        )
        return rofi.stdout.decode().strip()
    except FileNotFoundError:
        while True:
            choice = input(f"{question} ({'/'.join(options)}): ").strip()
            if choice in options:
                return choice
