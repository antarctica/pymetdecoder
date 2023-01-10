# CHANGELOG

## 0.1.2 [XXXX-XX-XX]

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

## 0.1.1 [2021-07-19]

### Fixed

* (#1) - Group 6 codes in section3 now properly decode when a group 5 code is present

## 0.1.0 [2021-05-27]

* First version
