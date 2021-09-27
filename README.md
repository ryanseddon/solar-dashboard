
# MagTag Solar Dashboard

A solar monitoring dashboard for your [Adafruit MagTag](https://www.adafruit.com/product/4800).

![Photo of my MagTag displaying my solar dashboard](/screenshot.webp?raw=true)



## Usage/Examples

Copy `code.py` and `bmps` folder to your magtag device.

### API response

The program expects the json to have these properties when it requests the url provided to the `gist` property in `secrets.py`:

```json
{
    "consumed": 200.8,
    "generated": 14281.4,
    "diff": 14080.6,
    "total": {
        "consumed": 7472.8718,
        "generated": 62460.1293,
        "exported": 54987.2575
    },
    "sunrise": "6:00AM",
    "sunset": "6:21PM"
}
```

### Secrets.py

The MagTag program will call out to the secrets.py file which needs to contain the following information:

```python
secrets = {
    'ssid' : '',
    'password' : '',
    'aio_username' : '',
    'aio_key' : '',
    'timezone' : "Australia/Melbourne", # http://worldtimeapi.org/timezones
    'gist': ""
}
```

The first 4 properties are required for the device to function. The last 2 are for this solar dashboard.

  #### timezone

| Property | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `timezone` | `string` | **Required**. The timezone your device is operating in  |

#### gist

| Property | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `gist` | `url` | **Required**. An API endpoint that returns json in expected format  |
  
## Contributing

Contributions are always welcome!

  