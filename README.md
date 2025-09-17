# ISS-Urine-Tank-Persentage-Waybar-Plugin

ISS Urine Tank Persentage Waybar Plugin built in python

> [!NOTE]
> This repository contains crude humor.

I butchered this python script together in about an hour. I plan on updating the script to be more efficient and add more features in the future.

For requests: Please feel free to send them my way.

## How to install

1. Move the python script to `~/.config/waybar/scripts/`

2. add the following to your waybar config file:

```
    "custom/ISS_Urine_Tank": {
      "exec": "~/.config/waybar/scripts/piss.py",
      "restart-interval": 0, // keeps it running, not rerun
      "return-type": "json"
    },
```

3. Add iss_urine_tank to your waybar modules list

```custom/ISS_Urine_Tank```
