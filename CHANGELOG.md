# CHANGELOG

## Next [XXXX-XX-XX]

### Fixed

* (#11) - 0xxxx group handling in section 3 now extended to other regions
* Synops now jump to Section 5 even if it follows directly after Section 1 or 2

## 0.1.4 [2023-04-21]

### Fixed

* (#9) - Rainfall group in section 3 is now properly decoded when cloud group is present
* (#10) - Fixed erroneous error message for temperatures

## 0.1.3 [2023-04-17]

### Fixed

* (#8) - Removed logging configuration from `__init__.py`

## 0.1.2 [2023-01-25]

### Added

* Added unit tests!
* (#3, #7) - Decoding/encoding of SYNOP section 4 is now implemented

### Fixed

* (#4, #5) - Better handling of sunshine and radiation groups in SYNOP section 3
* (#6) - Better exception handling
* `time_of_ending` in `weather_info` (SYNOP section 3, 901xx) now re-encodes correctly
* SYNOP section 3, 965xx now decodes correctly
* Multiple mirages can now be decoded and encoded (SYNOP section 3, 991xx)
* Latitude and longitude in `station_position` now returned as floats instead of strings
* `quadrant` checked for validity
* Instrumental `wind_waves` are now decoded from SYNOP section 3 group 1 and group 7 correctly

## 0.1.1 [2021-07-19]

### Fixed

* (#1) - Group 6 codes in section3 now properly decode when a group 5 code is present

## 0.1.0 [2021-05-27]

* First version
