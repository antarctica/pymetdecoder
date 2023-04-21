# README

This is a Python module which decodes meteorological reports (e.g. SYNOPs) into a Python dictionary. It can also take a Python dictionary and encode a meteorological report from it.

## Currently supported

The current version of the module supports the following (in most cases; see Known Issues below):

* SYNOP (FM-12)
* SHIP (FM-13)
* SYNOP MOBIL (FM-14)

## Example usage

To decode a SYNOP:

```python
from pymetdecoder import synop as s

synop = "AAXX 01004 88889 12782 61506 10094 20047 30111 40197 53007 60001 81541 333 81656 86070"
output = s.SYNOP().decode(synop)
print(output)
```

This yields the following output (pretty-printed):

```json
{
  "station_type": {
    "value": "AAXX"
  },
  "obs_time": {
    "day": {
      "value": 1
    },
    "hour": {
      "value": 0
    }
  },
  "wind_indicator": {
    "value": 4,
    "unit": "KT",
    "estimated": false
  },
  "station_id": {
    "value": "88889"
  },
  "region": {
    "value": "III"
  },
  "precipitation_indicator": {
    "value": 1,
    "in_group_1": true,
    "in_group_3": false
  },
  "weather_indicator": {
    "value": 2,
    "automatic": false
  },
  "lowest_cloud_base": {
    "_table": "1600",
    "min": 1500,
    "max": 2000,
    "quantifier": null,
    "_code": 7,
    "unit": "m"
  },
  "visibility": {
    "_table": "4377",
    "value": 40000,
    "quantifier": null,
    "use90": false,
    "_code": 82,
    "unit": "m"
  },
  "cloud_cover": {
    "_table": "2700",
    "value": 6,
    "obscured": false,
    "unit": "okta",
    "_code": 6
  },
  "surface_wind": {
    "direction": {
      "_table": "0877",
      "value": 150,
      "varAllUnknown": false,
      "calm": false,
      "_code": 15,
      "unit": "deg"
    },
    "speed": {
      "value": 6,
      "unit": "KT"
    }
  },
  "air_temperature": {
    "value": 9.4,
    "unit": "Cel"
  },
  "dewpoint_temperature": {
    "value": 4.7,
    "unit": "Cel"
  },
  "station_pressure": {
    "value": 1011.1,
    "unit": "hPa"
  },
  "sea_level_pressure": {
    "value": 1019.7,
    "unit": "hPa"
  },
  "pressure_tendency": {
    "tendency": {
      "_table": "0200",
      "value": 3
    },
    "change": {
      "value": 0.7,
      "unit": "hPa"
    }
  },
  "precipitation_s1": {
    "amount": {
      "_table": "3590",
      "value": 0,
      "quantifier": null,
      "trace": false,
      "_code": 0,
      "unit": "mm"
    },
    "time_before_obs": {
      "_table": "4019",
      "value": 6,
      "unit": "h",
      "_code": 1
    }
  },
  "cloud_types": {
    "low_cloud_type": {
      "_table": "0513",
      "value": 5
    },
    "middle_cloud_type": {
      "_table": "0515",
      "value": 4
    },
    "high_cloud_type": {
      "_table": "0509",
      "value": 1
    },
    "low_cloud_amount": {
      "value": 1,
      "unit": "okta"
    }
  },
  "cloud_layer": [
    {
      "cloud_cover": {
        "_table": "2700",
        "value": 1,
        "obscured": false,
        "unit": "okta",
        "_code": 1
      },
      "cloud_genus": {
        "_table": "0500",
        "value": "Sc",
        "_code": 6
      },
      "cloud_height": {
        "_table": "1677",
        "value": 1800,
        "quantifier": null,
        "_code": 56,
        "unit": "m"
      }
    },
    {
      "cloud_cover": {
        "_table": "2700",
        "value": 6,
        "obscured": false,
        "unit": "okta",
        "_code": 6
      },
      "cloud_genus": {
        "_table": "0500",
        "value": "Ci",
        "_code": 0
      },
      "cloud_height": {
        "_table": "1677",
        "value": 6000,
        "quantifier": null,
        "_code": 70,
        "unit": "m"
      }
    }
  ]
}
```

Re-encoding this dict gets back the original SYNOP:

```python
from pymetdecoder import synop as s

original = "AAXX 01004 88889 12782 61506 10094 20047 30111 40197 53007 60001 81541 333 81656 86070"
synop = s.SYNOP()
output = synop.decode(synop)
msg = synop.encode(output)

print(msg)
# Returns AAXX 01004 88889 12782 61506 10094 20047 30111 40197 53007 60001 81541 333 81656 86070
```

Commonly seen attributes in the output dict are as follows:

* `value` - The absolute value of the attribute
* `min`, `max` - If a code value converts to a range, the min/max specifies the limit of the range
* `quantifier` - Used alongside min/max/value to add an inequality if needs be (e.g. `{ "value": 6000, "quantifier": "isGreater"}` represents a value >6000). This is often the case when looking up values in a code table
* `unit` - The unit the value is measured in. The Unified Code for Units of Measure is used here (https://ucum.org/ucum.html)
* `_table` - This is the code table used to look up the value
* `_code` - The code value looked up in the code table. When encoding a message, if this attribute is present, it will use that, rather than trying to calculate it from the value

### Malformed reports

The module will try to decode as much of a report as it can. Non-fatal problems (e.g. invalid codes) will emit a warning message and continue. Fatal problems will emit a `DecodeError` exception, which can be caught in a `try...except` block.

## Changelog

See `CHANGELOG.md` for the list of changes

## Known issues

This version is 0.1.4. There may be some uncaught bugs/issues or other problems that have not been found yet. The following is a list of known issues which are still to be addressed:

* Not all countries are auto-detected. As more region-specific handling is added, more countries will be added to the list
* Section 5 of the SYNOP messages are not handled yet. Any codes in these sections are stored in the output dict under the `section5` attribute
* Most of the group 9 codes of section 3 are handled. Any codes not handled are added to a list in the output dict under the `_not_implemented` attribute
* Some aspects of encoding have not been fully tested

Feel free to raise any additional issues/bugs in the issue tracker

## Future plans

In future, it is intended that the module will support the following:

* SYNOP section 5
* BUOY (FM-18)
* TEMP (FM-35)
* CLIMAT (FM-71)
* METAR (FM-15)

If you would like to contribute to this module by adding in the functionality to support any of these reports (or other reports), then feel free to do so!

## License

(c) UK Research and Innovation (UKRI), 2021 - 2023, British Antarctic Survey.
You may use and re-use this software and associated documentation files free of charge in any format or medium, under the terms of the Open Government Licence v3.0.
You may obtain a copy of the Open Government Licence at http://www.nationalarchives.gov.uk/doc/open-government-licence/
