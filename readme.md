# Control LED strip with Raspberry Pi and Python (WIP)

## API
### Usage
Start the API server with `python api.py`

By default it runs at `http://127.0.0.1:5000`

### Endpoints

```
endpoint: /set-color
method: POST
query params: color=<r,g,b>

endpoint: /shift
method: POST
query params:
    start_color=<r,g,b>
    end_color=<r,g,b>
    period=<int> (seconds)
    cont=<bool>

endpoint: /turn-off
method: POST
query params: None
```



## CLI
### Set LED strip color
```
python main.py --color=<comma-separated RGB color value> (e.g. --color=253,8,226)
```

### Shift between colors
```
python main.py --shift-start=<comma-separated RGB color value> --shift-end=<comma-separated RGB color value> --shift-period=<seconds> --shift-cont=<bool>
```
Arguments

`--shift-start` Shift from this color, e.g. `253,8,226`

`--shift-end` Shift to this color, e.g. `8,251,255`

`--shift-period` Shifting period, i.e. how long time to go from start color to end color (seconds). Default: `1`

`--shift-cont` Continious shifting. If `True`, keep switching between start and end colors. Otherwise shift once. Default: `False`
