# CHANGELOG

## 0.1.2 [XXXX-XX-XX]

### Added

* Added unit tests!

### Fixed

* (#6) - Better exception handling
* `time_of_ending` in `weather_info` (SYNOP section 3, 901xx) now re-encodes correctly
* SYNOP section 3, 965xx now decodes correctly
* Multiple mirages can now be decoded and encoded (SYNOP section 3, 991xx)

## 0.1.1 [2021-07-19]

### Fixed

* (#1) - Group 6 codes in section3 now properly decode when a group 5 code is present

## 0.1.0 [2021-05-27]

* First version
