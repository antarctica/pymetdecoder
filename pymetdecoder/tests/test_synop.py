################################################################################
# pymetdecoder/tests/test_synop.py
#
# Unit tests for SYNOPs. Requires pytest
#
# TDBA 2023-01-05:
#   * First version
################################################################################
# CONFIGURATION
################################################################################
import pytest
from pymetdecoder import synop as s
from pymetdecoder import DecodeError, EncodeError
################################################################################
# CLASSES
################################################################################
class BaseTestSynop:
    """
    Base class for Synop tests
    """
    SYNOP = None
    @pytest.fixture
    def decoded(self):
        synop = s.SYNOP()
        data  = synop.decode(self.SYNOP)
        yield data
    def pytest_generate_tests(self, metafunc):
        data = s.SYNOP().decode(self.SYNOP)

        if metafunc.function.__name__ == "test_values":
            attrs = self.TEST_ATTRS if hasattr(self, "TEST_ATTRS") else list(data.keys())
            metafunc.parametrize("attr", attrs)

    def test_values(self, decoded, attr):
        if attr not in self.expected:
            assert False, "Expected attribute '{}' not present in decoded output".format(attr)
        else:
            assert decoded[attr] == self.expected[attr], "Decoded attribute '{}' does not match expected output".format(attr)

    def test_reencode(self, decoded):
        encoded = s.SYNOP().encode(decoded)
        assert encoded == self.SYNOP, "Re-encoded SYNOP does not match original"
class BaseTestSynopRadiationPrecip(BaseTestSynop):
    """
    Tests we get correct radiation and precipitation. We need to test multiple
    combinations due to the complexity
    """
    TEST_ATTRS = ["sunshine", "radiation", "precipitation_s3"]

class TestSynopAAXX(BaseTestSynop):
    """
    Tests a simple AAXX Synop
    """
    # SYNOP = "AAXX 01004 88889 12782 61506 10094 20047 30111 40197 53007 60001 70102 81541 333 10178 21073 34101 55055 00010 21073 30002 50001 60004 60035"
    SYNOP = "AAXX 01004 88889 12782 61506 10094 20047 30111 40197 53007 60001 70102 81541 333 10178 21073 34101"
    expected = {
        "station_type": { "value": "AAXX" },
        "obs_time": {
            "day":  { "value": 1 },
            "hour": { "value": 0 }
        },
        "wind_indicator": { "value": 4, "unit": "KT", "estimated": False },
        "station_id": { "value": "88889" },
        "region": { "value": "III" },
        "precipitation_indicator": {
            "value": 1, "in_group_1": True, "in_group_3": False
        },
        "weather_indicator": {
            "value": 2, "automatic": False
        },
        "lowest_cloud_base": {
            "_table": "1600", "min": 1500, "max": 2000, "quantifier": None, "_code": 7, "unit": "m"
        },
        "visibility": {
            "_table": "4377", "value": 40000, "quantifier": None, "use90": False, "_code": 82, "unit": "m"
        },
        "cloud_cover": {
            "_table": "2700", "value": 6, "obscured": False, "_code": 6, "unit": "okta"
        },
        "surface_wind": {
            "direction": { "_table": "0877", "value": 150, "varAllUnknown": False, "calm": False, "_code": 15, "unit": "deg" },
            "speed": { "value": 6, "unit": "KT" }
        },
        "air_temperature": { "value": 9.4, "unit": "Cel" },
        "dewpoint_temperature": { "value": 4.7, "unit": "Cel" },
        "station_pressure": { "value": 1011.1, "unit": "hPa" },
        "sea_level_pressure": { "value": 1019.7, "unit": "hPa" },
        "pressure_tendency": {
            "tendency": { "_table": "0200", "value": 3 },
            "change":   { "value": 0.7, "unit": "hPa" }
        },
        "precipitation_s1": {
            "amount":          { "_table": "3590", "value": 0, "quantifier": None, "trace": False, "_code": 0, "unit": "mm" },
            "time_before_obs": { "_table": "4019", "value": 6, "_code": 1, "unit": "h" }
        },
        "present_weather": {
            "_table": "4677", "value": 1, "time_before_obs": { "value": 6, "unit": "h" }
        },
        "past_weather": [
            { "_table": "4561", "value": 0 },
            { "_table": "4561", "value": 2 }
        ],
        "cloud_types": {
            "low_cloud_type":    { "_table": "0513", "value": 5 },
            "middle_cloud_type": { "_table": "0515", "value": 4 },
            "high_cloud_type":   { "_table": "0509", "value": 1 },
            "low_cloud_amount":  { "value": 1, "unit": "okta" }
        },
        "maximum_temperature": { "value": 17.8, "unit": "Cel" },
        "minimum_temperature": { "value": -7.3, "unit": "Cel" },
        "ground_state": {
            "state":       { "_table": "0901", "value": 4 },
            "temperature": { "value": -1.0, "unit": "Cel" }
        }
    }
class TestSynopBBXX(BaseTestSynop):
    """
    Tests a simple BBXX synop
    """
    SYNOP = "BBXX 51002 19001 99170 71577 46/// /0709 10267 20232 30132 40135 92350 22251 00268 10804 20604 310// 40802 61234 70021 80092 333 91212 555 11102 22108 8//10 92344"
    expected = {
        "station_type": { "value": "BBXX" },
        "callsign": {
            "region": {
                "_table": "0161",
                "value": "V"
            },
            "value": "51002"
        },
        "obs_time": {
            "day":  { "value": 19 },
            "hour": { "value":  0 }
        },
        "wind_indicator": {
            "value": 1, "unit": "m/s", "estimated": False
        },
        "station_position": {
            "latitude": 17.0, "longitude": -157.7
        },
        "region": {
            "value": { "_table": "0161", "value": "V" }
        },
        "precipitation_indicator": {
            "value": 4, "in_group_1": False, "in_group_3": False
        },
        "weather_indicator": {
            "value": 6, "automatic": True
        },
        "lowest_cloud_base": None,
        "visibility": None,
        "cloud_cover": None,
        "surface_wind": {
            "direction": { "_table": "0877", "value": 70, "varAllUnknown": False, "calm": False, "_code": 7, "unit": "deg" },
            "speed": { "value": 9, "unit": "m/s" }
        },
        "air_temperature": { "value": 26.7, "unit": "Cel" },
        "dewpoint_temperature": { "value": 23.2, "unit": "Cel" },
        "station_pressure": { "value": 1013.2, "unit": "hPa" },
        "sea_level_pressure": { "value": 1013.5, "unit": "hPa" },
        "exact_obs_time": {
            "hour":   { "value": 23 },
            "minute": { "value": 50 }
        },
        "displacement": {
            "direction": { "_table": "0700", "value": "SW", "isCalmOrStationary": False, "allDirections": False, "_code": 5 },
            "speed": { "_table": "4451", "_code": 1, "value": [
                { "min": 1, "max":  5, "quantifier": None, "unit": "KT"   },
                { "min": 1, "max": 10, "quantifier": None, "unit": "km/h" }
            ]}
        },
        "sea_surface_temperature": {
            "value": 26.8, "unit": "Cel", "measurement_type": {
                "_table": "3850", "value": "Intake", "_code": 0
            }
        },
        "wind_waves": [{
            "period": { "value": 8,   "unit": "s" },
            "height": { "value": 2.1, "unit": "m" },
            "instrumental": True, "accurate": True, "confused": False
        },{
            "period": { "value": 6,   "unit": "s" },
            "height": { "value": 2.0, "unit": "m" },
            "instrumental": False, "accurate": False, "confused": False
        }],
        "swell_waves": [{
            "direction": { "_table": "0877", "value": 100, "varAllUnknown": False, "calm": False, "_code": 10, "unit": "deg" },
            "period": { "value": 8,   "unit": "s" },
            "height": { "value": 1.0, "unit": "m" }
        }],
        "ice_accretion": {
            "source": { "_table": "1751", "spray": True, "fog": False, "rain": False, "_code": 1 },
            "thickness": { "value": 23, "unit": "cm" },
            "rate": { "_table": "3551", "value": "Ice melting or breaking up rapidly", "_code": 4 }
        },
        "wet_bulb_temperature": {
            "value": 9.2, "unit": "Cel", "_table": "3855", "sign": 1, "measured": True, "iced": False, "_code": 0
        },
        "sea_land_ice": {
            "concentration":   { "_table": "0639", "value": 1 },
            "development":     { "_table": "3739", "value": 3 },
            "land_origin":     { "_table": "0439", "value": 9 },
            "direction":       { "_table": "0739", "value": "S", "in_shore": False, "in_ice": False, "_code": 4 },
            "condition_trend": { "_table": "5239", "value": 0 }
        },
        "section5": ["11102", "22108", "8//10", "92344"],
        "_not_implemented": ["91212"]
    }
    def test_reencode(self, decoded):
        # Skip this test because it contains a "_not_implemented"
        pytest.skip()
class TestSynopOOXX(BaseTestSynop):
    """
    Tests a simple OOXX synop
    """
    SYNOP = "OOXX AAATN 18214 99759 50874 56057 12501 46/// /1219 11259 38338 49778 5//// 92100"
    expected = {
        "station_type": { "value": "OOXX" },
        "callsign": { "value": "AAATN" },
        "obs_time": {
            "day":  { "value": 18 },
            "hour": { "value": 21 }
        },
        "wind_indicator": {
            "value": 4, "unit": "KT", "estimated": False
        },
        "station_position": {
            "latitude": -75.9,
            "longitude": -87.4,
            "marsden_square": 560,
            "elevation": {
                "value": 1250,
                "unit": "m"
            },
            "confidence": "Excellent"
        },
        "precipitation_indicator": {
            "value": 4, "in_group_1": False, "in_group_3": False
        },
        "weather_indicator": {
            "value": 6, "automatic": True
        },
        "lowest_cloud_base": None,
        "visibility": None,
        "cloud_cover": None,
        "surface_wind": {
            "direction": { "_table": "0877", "value": 120, "varAllUnknown": False, "calm": False, "_code": 12, "unit": "deg" },
            "speed": { "value": 19, "unit": "KT" }
        },
        "air_temperature": { "value": -25.9, "unit": "Cel" },
        "station_pressure": { "value": 833.8, "unit": "hPa" },
        "sea_level_pressure": { "value": 977.8, "unit": "hPa" },
        "pressure_tendency": { "change": None, "tendency": None },
        "exact_obs_time": {
            "hour":   { "value": 21 },
            "minute": { "value":  0 }
        }
    }
class TestSynopAAXXAntarctic(BaseTestSynop):
    """
    Tests a AAXX synop with Antarctic specific options (plus some additional options
    that couldn't be tested in the simple example)

    * wind speed > 99
    * relative humidity
    * geopotential
    * max wind (Antarctic-specific)
    """
    SYNOP = "AAXX 20104 89646 46/// /2299 00113 29079 37708 42010 333 01268"
    expected = {
        "station_type": { "value": "AAXX" },
        "obs_time": {
            "day":  { "value": 20 },
            "hour": { "value": 10 }
        },
        "wind_indicator": { "value": 4, "unit": "KT", "estimated": False },
        "station_id": { "value": "89646" },
        "region": { "value": "Antarctic" },
        "precipitation_indicator": {
            "value": 4, "in_group_1": False, "in_group_3": False
        },
        "weather_indicator": {
            "value": 6, "automatic": True
        },
        "lowest_cloud_base": None,
        "visibility": None,
        "cloud_cover": None,
        "surface_wind": {
            "direction": { "_table": "0877", "value": 220, "varAllUnknown": False, "calm": False, "_code": 22, "unit": "deg" },
            "speed": { "value": 113, "unit": "KT" }
        },
        "relative_humidity": { "value": 79, "unit": "%" },
        "station_pressure": { "value": 770.8, "unit": "hPa" },
        "geopotential": {
            "surface": { "_table": "0264", "value": 925, "unit": "hPa", "_code": 2 },
            "height":  { "value": 1010, "unit": "gpm" }
        },
        "max_wind": {
            "direction": { "_table": "0877", "value": 120, "varAllUnknown": False, "calm": False, "_code": 12, "unit": "deg" },
            "speed": { "value": 68, "unit": "KT" }
        }
    }
class TestSynopAAXXRegionI(BaseTestSynop):
    """
    Tests a AAXX synop with Region I specific options

    * ground minimum temperature
    * local precipitation
    """
    SYNOP = "AAXX 20064 67005 12570 50402 60004 333 02434"
    expected = {
        "station_type": { "value": "AAXX" },
        "obs_time": {
            "day":  { "value": 20 },
            "hour": { "value":  6 }
        },
        "wind_indicator": { "value": 4, "unit": "KT", "estimated": False },
        "station_id": { "value": "67005" },
        "region": { "value": "I" },
        "precipitation_indicator": {
            "value": 1, "in_group_1": True, "in_group_3": False
        },
        "weather_indicator": {
            "value": 2, "automatic": False
        },
        "lowest_cloud_base": {
            "_table": "1600", "min": 600, "max": 1000, "quantifier": None, "_code": 5, "unit": "m"
        },
        "visibility": {
            "_table": "4377", "value": 20000, "quantifier": None, "use90": False, "_code": 70, "unit": "m"
        },
        "cloud_cover": {
            "_table": "2700", "value": 5, "obscured": False, "_code": 5, "unit": "okta"
        },
        "surface_wind": {
            "direction": { "_table": "0877", "value": 40, "varAllUnknown": False, "calm": False, "_code": 4, "unit": "deg" },
            "speed": { "value": 2, "unit": "KT" }
        },
        "precipitation_s1": {
            "amount":          { "_table": "3590", "value": 0, "quantifier": None, "trace": False, "_code": 0, "unit": "mm" },
            "time_before_obs": { "_table": "4019", "value": 24, "_code": 4, "unit": "h" }
        },
        "ground_minimum_temperature": { "value": 24, "unit": "Cel" },
        "local_precipitation": {
            "character": { "_table": "167", "value": "Heavy intermittent", "_code": 3 },
            "time":      { "_table": "168", "min": 3, "max": 4, "quantifier": None, "unit": "h", "_code": 4 }
        }
    }
class TestSynopAAXXSection4(BaseTestSynop):
    """
    Tests that section 4 groups are added to the "cloud_base_below_station" key
    """
    SYNOP = "AAXX 01004 89022 32782 61506 30111 333 10178 444 21053 34810"
    expected = {
        "station_type": { "value": "AAXX" },
        "obs_time": {
            "day":  { "value": 1 },
            "hour": { "value": 0 }
        },
        "wind_indicator": { "value": 4, "unit": "KT", "estimated": False },
        "station_id": { "value": "89022" },
        "region": { "value": "Antarctic" },
        "precipitation_indicator": {
            "value": 3, "in_group_1": False, "in_group_3": False
        },
        "weather_indicator": {
            "value": 2, "automatic": False
        },
        "lowest_cloud_base": {
            "_table": "1600", "min": 1500, "max": 2000, "quantifier": None, "_code": 7, "unit": "m"
        },
        "visibility": {
            "_table": "4377", "value": 40000, "quantifier": None, "use90": False, "_code": 82, "unit": "m"
        },
        "cloud_cover": {
            "_table": "2700", "value": 6, "obscured": False, "_code": 6, "unit": "okta"
        },
        "surface_wind": {
            "direction": { "_table": "0877", "value": 150, "varAllUnknown": False, "calm": False, "_code": 15, "unit": "deg" },
            "speed": { "value": 6, "unit": "KT" }
        },
        "station_pressure": { "value": 1011.1, "unit": "hPa" },
        "maximum_temperature": { "value": 17.8, "unit": "Cel" },
        "cloud_base_below_station": [{
            "cloud_cover": { "_table": "2700", "value": 2, "obscured": False, "unit": "okta", "_code": 2 },
            "genus": { "_table": "0500", "value": "Cc", "_code": 1 },
            "upper_surface_altitude": { "value": 500, "quantifier": None, "unit": "m" },
            "description": { "_table": "0552", "value": "Broken cloud - large breaks (flat tops)", "_code": 3 }
        },{
            "cloud_cover": { "_table": "2700", "value": 3, "obscured": False, "unit": "okta", "_code": 3 },
            "genus": { "_table": "0500", "value": "As", "_code": 4 },
            "upper_surface_altitude": { "value": 8100, "quantifier": None, "unit": "m" },
            "description": { "_table": "0552", "value": "Isolated cloud or fragments of cloud", "_code": 0 }
        }]
    }
class TestSynopAAXX1Rad1Precip(BaseTestSynopRadiationPrecip):
    """
    Tests we get correct radiation and precipitation when section 3 precipitation
    is required and 1 radiation and 1 6xxxx group are specified.

    Should return 1 radiation and section 3 precipitation entry
    """
    SYNOP = "AAXX 01004 89022 22782 61506 30111 333 55032 01234 60123"
    expected = {
        "sunshine": [
            { "amount": { "value": 3.2, "unit": "h" }, "duration": { "value": 24, "unit": "h" }}
        ],
        "precipitation_s3": {
            "amount": { "_table": "3590", "value": 12, "quantifier": None, "trace": False, "_code": 12, "unit": "mm" },
            "time_before_obs": { "_table": "4019", "value": 18, "unit": "h", "_code": 3 }
        },
        "radiation": {
            "positive_net": [
                { "value": 1234, "unit": "J/cm2", "time_before_obs": { "value": 24, "unit": "h" }}
            ]
        }
    }
class TestSynopAAXX2RadPrecip(BaseTestSynopRadiationPrecip):
    """
    Tests we get correct radiation and precipitation when section 3 precipitation
    is required and 2 radiation and 1 6xxxx groups are specified.

    Should return 2 radiation entries and section 3 precipitation
    """
    SYNOP = "AAXX 01004 89022 22782 61506 30111 333 55055 01234 10329 60123"
    expected = {
        "sunshine": [
            { "amount": { "value": 5.5, "unit": "h" }, "duration": { "value": 24, "unit": "h" }}
        ],
        "precipitation_s3": {
            "amount": { "_table": "3590", "value": 12, "quantifier": None, "trace": False, "_code": 12, "unit": "mm" },
            "time_before_obs": { "_table": "4019", "value": 18, "unit": "h", "_code": 3 }
        },
        "radiation": {
            "positive_net": [
                { "value": 1234, "unit": "J/cm2", "time_before_obs": { "value": 24, "unit": "h" }}
            ],
            "negative_net": [
                { "value": 329, "unit": "J/cm2", "time_before_obs": { "value": 24, "unit": "h" }}
            ]
        }
    }
class TestSynopAAXXRadPrecip2Group6(BaseTestSynopRadiationPrecip):
    """
    Tests we get correct radiation and precipitation when section 3 precipitation
    is required and 2 6xxxx groups are specified

    Should return 2 radiation entries and 1 section 3 precipitation entry
    """
    SYNOP = "AAXX 01004 89022 22782 61506 30111 333 55055 01234 60329 60123"
    expected = {
        "sunshine": [
            { "amount": { "value": 5.5, "unit": "h" }, "duration": { "value": 24, "unit": "h" }}
        ],
        "precipitation_s3": {
            "amount": { "_table": "3590", "value": 12, "quantifier": None, "trace": False, "_code": 12, "unit": "mm" },
            "time_before_obs": { "_table": "4019", "value": 18, "unit": "h", "_code": 3 }
        },
        "radiation": {
            "positive_net": [
                { "value": 1234, "unit": "J/cm2", "time_before_obs": { "value": 24, "unit": "h" }}
            ],
            "short_wave": [
                { "value": 329, "unit": "J/cm2", "time_before_obs": { "value": 24, "unit": "h" }}
            ]
        }
    }
class TestSynopAAXXNoS3PrecipWith6(BaseTestSynopRadiationPrecip):
    """
    Tests we get correct radiation and precipitation when section 3 precipitation
    is not required and 1 radiation and 1 6xxxx groups are specified

    Should return 2 radiation entries
    """
    SYNOP = "AAXX 01004 89022 12782 61506 30111 333 55055 01234 60329"
    TEST_ATTRS = ["radiation"]
    expected = {
        "radiation": {
            "positive_net": [
                { "value": 1234, "unit": "J/cm2", "time_before_obs": { "value": 24, "unit": "h" }}
            ],
            "short_wave": [
                { "value": 329, "unit": "J/cm2", "time_before_obs": { "value": 24, "unit": "h" }}
            ]
        }
    }
class TestSynopAAXXNoS3PrecipWithNo6(BaseTestSynopRadiationPrecip):
    """
    Tests we get correct radiation and precipitation when section 3 precipitation
    is not required and 2 radiation groups are specified

    Should return 2 radiation entries
    """
    SYNOP = "AAXX 01004 89022 12782 61506 30111 333 55055 01234 30801"
    TEST_ATTRS = ["radiation"]
    expected = {
        "radiation": {
            "positive_net": [
                { "value": 1234, "unit": "J/cm2", "time_before_obs": { "value": 24, "unit": "h" }}
            ],
            "diffused_solar": [
                { "value": 801, "unit": "J/cm2", "time_before_obs": { "value": 24, "unit": "h" }}
            ]
        }
    }
class TestSynopAAXXMultipleRadiationWithPrecip(BaseTestSynopRadiationPrecip):
    """
    Tests we get correct radiation when section 3 precipitation is required and
    multiple different radiation groups are specified
    """
    SYNOP = "AAXX 01004 89022 22782 61506 30111 333 55055 01234 60300 55301 00331 60001 60123"
    expected = {
        "sunshine": [
            { "amount": { "value": 5.5, "unit": "h" }, "duration": { "value": 24, "unit": "h" }},
            { "amount": { "value": 0.1, "unit": "h" }, "duration": { "value":  1, "unit": "h" }}
        ],
        "radiation": {
            "positive_net": [
                { "value": 1234, "unit": "J/cm2", "time_before_obs": { "value": 24, "unit": "h" }},
                { "value":  331, "unit": "kJ/m2", "time_before_obs": { "value":  1, "unit": "h" }}
            ],
            "short_wave": [
                { "value": 300, "unit": "J/cm2", "time_before_obs": { "value": 24, "unit": "h" }},
                { "value":   1, "unit": "kJ/m2", "time_before_obs": { "value":  1, "unit": "h" }}
            ]
        },
        "precipitation_s3": {
            "amount": { "_table": "3590", "value": 12, "quantifier": None, "trace": False, "_code": 12, "unit": "mm" },
            "time_before_obs": { "_table": "4019", "value": 18, "unit": "h", "_code": 3 }
        }
    }
class TestSynopAAXXNoSunshine(BaseTestSynopRadiationPrecip):
    """
    Tests SYNOP with no sunshine is decoded and encoded correctly
    """
    SYNOP = "AAXX 01004 89022 22782 61506 30111 333 55/// 20884 60192"
    expected = {
        "sunshine": [None],
        "radiation": {
            "global_solar": [
                { "value": 884, "unit": "J/cm2", "time_before_obs": { "value": 24, "unit": "h" }}
            ]
        },
        "precipitation_s3": {
            "amount": { "_table": "3590", "value": 19, "quantifier": None, "trace": False, "_code": 19, "unit": "mm" },
            "time_before_obs": { "_table": "4019", "value": 12, "unit": "h", "_code": 2 }
        }
    }
class TestSynopAAXXExtraGroupAfterRainfall(BaseTestSynop):
    """
    Tests SYNOP with extra groups after section 3 rainfall (as mentioned in issue #9)
    """
    SYNOP = "AAXX 24121 80110 01565 79901 10173 20173 38512 60004 7052/ 81550 333 20167 30/// 55066 56990 59006 60007 81630"
    TEST_ATTRS = ["precipitation_s3", "cloud_layer"]
    expected = {
        "precipitation_s3": {
            "amount": { "_table": "3590", "value": 0, "quantifier": None, "trace": False, "_code": 0, "unit": "mm"},
            "time_before_obs": { "_table": "4019", "value": 3, "unit": "h", "_code": 7 }
        },
        "cloud_layer": [{
            "cloud_cover":  { "_table": "2700", "value": 1, "obscured": False, "unit": "okta", "_code": 1 },
            "cloud_genus":  { "_table": "0500", "value": "Sc", "_code": 6 },
            "cloud_height": { "_table": "1677", "value": 900, "quantifier": None, "_code": 30, "unit": "m" }
        }]
    }
class TestSynopAAXX9Groups90(BaseTestSynop):
    """
    Tests SYNOP with various 9-groups in section 3 (900-909 - time and variability)
    """
    SYNOP = "AAXX 10034 89004 46/// /1312 11202 21292 38818 49879 51005 333 11155 21214 90047 90083 90101 90521 90973"
    TEST_ATTRS = ["weather_info", "precipitation_end"]
    expected = {
        "weather_info": {
            "time_before_obs": { "_table": "4077", "value": 282, "unit": "min", "_code": 47 },
            "variability": { "_table": "4077", "value": 83, "_code": 83 },
            "time_of_ending": { "_table": "4077", "value": 6, "unit": "min", "_code": 1 },
            "non_persistent": { "_table": "4077", "value": 126, "unit": "min", "_code": 21 },
        },
        "precipitation_end": {
            "time": { "_table": "3552", "min": 6, "max": 12, "quantifier": None, "unknown": False, "unit": "h", "_code": 7 },
            "character": { "_table": "0833", "min": 6, "max": None, "quantifier": "isGreater", "unknown": False, "unit": "h", "_code": 3 }
        }
    }
class TestSynopAAXX9Groups91(BaseTestSynop):
    """
    Tests SYNOP with various 9-groups in section 3 (910-919 - wind and squall)
    """
    SYNOP = "AAXX 10034 89004 46/// /1312 11202 21292 38818 49879 51005 333 11155 21214 91015 91103 91523"
    TEST_ATTRS = ["highest_gust"]
    expected = {
        "highest_gust": [{
            "speed": { "value": 15, "unit": "KT" },
            "direction": None,
            "measure_period": { "value": 10, "unit": "min" }
        },{
            "speed": { "value": 3, "unit": "KT" },
            "direction": { "_table": "0877", "value": 230, "varAllUnknown": False, "calm": False, "_code": 23, "unit": "deg" },
            "time_before_obs": { "value": 3, "unit": "h" }
        }]
    }
class TestSynopAAXX9Groups92(BaseTestSynop):
    """
    Tests SYNOP with various 9-groups in section 3 (920-929 - state of the sea, icing phenomena and snow cover)
    """
    SYNOP = "AAXX 10034 89004 46/// /1312 11202 21292 38818 49879 51005 333 92416 92734 92882 92921"
    TEST_ATTRS = ["sea_state", "sea_visibility", "frozen_deposit", "snow_cover_regularity", "drift_snow"]
    expected = {
        "sea_state": {
            "_table": "3700", "value": "Calm (rippled)", "_code": 1
        },
        "sea_visibility": {
            "_table": "4300", "min": 4000, "max": 10000, "quantifier": None, "_code": 6, "unit": "m"
        },
        "frozen_deposit": {
            "deposit": { "_table": "3764", "value": "Snow deposit", "_code": 3 },
            "variation": { "_table": "3955", "value": 4 }
        },
        "snow_cover_regularity": {
            "cover": { "_table": "3765", "value": "Moist snow, with surface crust", "_code": 8 },
            "regularity": { "_table": "3775", "value": "Even snow cover, state of ground unknown, no drifts", "_code": 2 }
        },
        "drift_snow": {
            "phenomena": { "_table": "3766", "value": 2 },
            "evolution": { "_table": "3776", "value": 1 }
        }
    }
class TestSynopAAXX9Groups93(BaseTestSynop):
    """
    Tests SYNOP with various 9-groups in section 3 (930-939 - amount of precipitation or deposit)
    """
    SYNOP = "AAXX 10034 89004 46/// /1312 11202 21292 38818 49879 51005 333 93105 93349 93402 93509 93610 93704"
    TEST_ATTRS = ["snow_fall", "deposit_diameter"]
    expected = {
        "snow_fall": {
            "amount": { "_table": "3870", "value": 50, "quantifier": None, "inaccurate": False, "_code": 5, "unit": "mm" },
            "time_before_obs": { "value": 3, "unit": "h" }
        },
        "deposit_diameter": [{
            "solid": { "_table": "3570", "value": 49, "non_measurable": False, "quantifier": None, "impossible": False, "_code": 49, "unit": "mm" }
        },{
            "glaze": { "_table": "3570", "value": 2, "non_measurable": False, "quantifier": None, "impossible": False, "_code": 2, "unit": "mm" }
        },{
            "rime": { "_table": "3570", "value": 9, "non_measurable": False, "quantifier": None, "impossible": False, "_code": 9, "unit": "mm" }
        },{
            "compound": { "_table": "3570", "value": 10, "non_measurable": False, "quantifier": None, "impossible": False, "_code": 10, "unit": "mm" }
        },{
            "wet_snow": { "_table": "3570", "value": 4, "non_measurable": False, "quantifier": None, "impossible": False, "_code": 4, "unit": "mm" }
        }]
    }
class TestSynopAAXX9Groups94(BaseTestSynop):
    """
    Tests SYNOP with various 9-groups in section 3 (940-949 - amount of precipitation or deposit)
    """
    SYNOP = "AAXX 10034 89004 46/// /1312 11202 21292 38818 49879 51005 333 94060 94072 94469 94478"
    TEST_ATTRS = ["cloud_evolution", "max_low_cloud_concentration"]
    expected = {
        "cloud_evolution": [{
            "genus": { "_table": "0500", "value": "Sc", "_code": 6 },
            "evolution": { "_table": "2863", "value": "No change", "_code": 0 }
        },{
            "genus": { "_table": "0500", "value": "St", "_code": 7 },
            "evolution": { "_table": "2863", "value": "Slow elevation", "_code": 2 }
        }],
        "max_low_cloud_concentration": [{
            "cloud_type": { "_table": "0513", "value": 6 },
            "direction": { "_table": "0700", "value": None, "isCalmOrStationary": False, "allDirections": True, "_code": 9 }
        },{
            "cloud_type": { "_table": "0513", "value": 7 },
            "direction": { "_table": "0700", "value": "N", "isCalmOrStationary": False, "allDirections": False, "_code": 8 }
        }]
    }
class TestSynopAAXX9Groups95(BaseTestSynop):
    """
    Tests SYNOP with various 9-groups in section 3 (950-959 - cloud conditions over mountains and passes)
    """
    SYNOP = "AAXX 10034 89004 46/// /1312 11202 21292 38818 49879 51005 333 95095 95150"
    TEST_ATTRS = ["mountain_condition", "valley_clouds"]
    expected = {
        "mountain_condition": {
            "condition": { "_table": "2745", "value": 9 },
            "evolution": { "_table": "2863", "value": "Slow lowering", "_code": 5 }
        },
        "valley_clouds": {
            "condition": { "_table": "2754", "value": "Some isolated clouds", "_code": 5  },
            "evolution": { "_table": "2864", "value": "No change", "_code": 0 }
        }
    }
class TestSynopAAXX9Groups96(BaseTestSynop):
    """
    Tests SYNOP with various 9-groups in section 3 (960-969 - present weather and past weather)
    """
    SYNOP = "AAXX 10034 89004 46/// /1312 11202 21292 38818 49879 51005 333 96010 96120 96447 96510"
    TEST_ATTRS = ["present_weather_additional", "important_weather"]
    expected = {
        "present_weather_additional": [{
            "_table": "4677", "value": 10, "time_before_obs": { "value": 3, "unit": "h" }
        },{
            "_table": "4677", "value": 20, "time_before_obs": { "value": 3, "unit": "h" }
        }],
        "important_weather": [
            { "_table": "4677", "value": 47, "time_before_obs": { "value": 3, "unit": "h" }},
            { "_table": "4687", "value": 10, "time_before_obs": { "value": 3, "unit": "h" }}
        ]
    }
class TestSynopAAXX9Groups98(BaseTestSynop):
    """
    Tests SYNOP with various 9-groups in section 3 (980-989 - visibility)
    """
    SYNOP = "AAXX 10034 89004 46/// /1312 11202 21292 38818 49879 51005 71322 333 98362 98732"
    TEST_ATTRS = ["visibility_direction"]
    expected = {
        "visibility_direction": [{
            "direction": { "value": "SE" },
            "visibility": { "_table": "4377", "value": 12000, "quantifier": None, "use90": False, "_code": 62, "unit": "m" }
        },{
            "direction": { "value": "NW" },
            "visibility": { "_table": "4377", "value": 3200, "quantifier": None, "use90": False, "_code": 32, "unit": "m" }
        }]
    }
class TestSynopAAXX9Groups99(BaseTestSynop):
    """
    Tests SYNOP with various 9-groups in section 3 (990-999 - optical phenomena and miscellaneous)
    """
    SYNOP = "AAXX 10034 89004 46/// /1312 11202 21292 38818 49879 51005 71322 333 99050 99114 99115 99190 99273 99349 99429 99605 99918"
    TEST_ATTRS = [
        "optical_phenomena", "mirage", "st_elmos_fire", "condensation_trails", "special_clouds",
        "day_darkness", "sudden_temperature_change", "sudden_humidity_change"
    ]
    expected = {
        "optical_phenomena": {
            "phenomena": { "_table": "5161", "value": "Corona", "_code": 5 },
            "intensity": { "_table": "1861", "value": "Slight", "_code": 0 }
        },
        "mirage": [{
            "mirage_type": { "_table": "0101", "value": 1 },
            "direction": { "_table": "0700", "value": "S", "isCalmOrStationary": False, "allDirections": False, "_code": 4 }
        },{
            "mirage_type": { "_table": "0101", "value": 1 },
            "direction": { "_table": "0700", "value": "SW", "isCalmOrStationary": False, "allDirections": False, "_code": 5 }
        }],
        "st_elmos_fire": True,
        "condensation_trails": {
            "trail": { "_table": "2752", "value": "Persistent, covering 1/8 of the sky", "_code": 7 },
            "time":  { "_table": "4055", "min": 90, "max": 120, "unit": "min", "_code": 3 }
        },
        "special_clouds": {
            "cloud_type": { "_table": "0521", "value": "Clouds from fires", "_code": 4 },
            "direction":  { "_table": "0700", "value": None, "isCalmOrStationary": False, "allDirections": True, "_code": 9 }
        },
        "day_darkness": {
            "darkness":  { "_table": "0163", "value": "black", "_code": 2 },
            "direction": { "_table": "0700", "value": None, "isCalmOrStationary": False, "allDirections": True, "_code": 9 }
        },
        "sudden_temperature_change": { "value": 5, "unit": "Cel" },
        "sudden_humidity_change":    { "value": -18, "unit": "%" }
    }
class TestSynopAAXXRegion1Section3Group0(BaseTestSynop):
    """
    Tests SYNOP from Region I with section 3 group 0
    """
    SYNOP = "AAXX 25064 67243 11465 50604 333 01223"
    TEST_ATTRS = ["ground_minimum_temperature", "local_precipitation"]
    expected = {
        "ground_minimum_temperature": { "value": 12, "unit": "Cel" },
        "local_precipitation": {
            "character": { "_table": "167", "value": "Moderate intermittent", "_code": 2 },
            "time":      { "_table": "168", "min": 2, "max": 3, "unit": "h", "quantifier": None, "_code": 3 }
        }
    }
class TestSynopAAXXRegion2Section3Group0(BaseTestSynop):
    """
    Tests SYNOP from Region II with section 3 group 0
    """
    SYNOP = "AAXX 25064 21998 11465 50604 333 00017"
    TEST_ATTRS = ["ground_state_grass"]
    expected = {
        "ground_state_grass": {
            "state":       { "_table": "0901", "value": 0 },
            "temperature": { "value": 17, "unit": "Cel" }
        }
    }
class TestSynopAAXXRegion4Section3Group0(BaseTestSynop):
    """
    Tests SYNOP from Region IV with section 3 group 0
    """
    SYNOP = "AAXX 25064 78962 11465 50604 333 00275"
    TEST_ATTRS = ["tropical_sky_state", "tropical_cloud_drift_direction"]
    expected = {
        "tropical_sky_state": { "_table": "430", "value": 0 },
        "tropical_cloud_drift_direction": {
            "low":    { "_table": "0700", "value": "E",  "isCalmOrStationary": False, "allDirections": False, "_code": 2 },
            "middle": { "_table": "0700", "value": "NW", "isCalmOrStationary": False, "allDirections": False, "_code": 7 },
            "high":   { "_table": "0700", "value": "SW", "isCalmOrStationary": False, "allDirections": False, "_code": 5 },
        }
    }
class TestSynopAAXXRegionAntarcticSection3Group0(BaseTestSynop):
    """
    Tests SYNOP from Antarctic region with section 3 group 0
    """
    SYNOP = "AAXX 25064 89022 11465 50604 333 02022"
    TEST_ATTRS = ["max_wind"]
    expected = {
        "max_wind": {
            "direction": { "_table": "0877", "value": 200, "varAllUnknown": False, "calm": False, "_code": 20, "unit": "deg" },
            "speed":     { "value": 22, "unit": "KT" }
        }
    }
class TestSynopBBXXAlternative(BaseTestSynop):
    """
    Tests a BBXX synop with alternative options:

    * stationary ship displacement
    * textual ice conditions
    """
    SYNOP = "BBXX ZDLP 19004 99607 50455 41298 81307 10001 21004 49894 52012 70211 886// 22200 04019 20000 300// 40000 5//// 81001 ICE icy conditions"
    expected = {
        "station_type": { "value": "BBXX" },
        "callsign": { "value": "ZDLP" },
        "obs_time": {
            "day":  { "value": 19 },
            "hour": { "value":  0 }
        },
        "wind_indicator": {
            "value": 4, "unit": "KT", "estimated": False
        },
        "station_position": {
            "latitude": -60.7, "longitude": -45.5
        },
        "region": {
            "value": "SHIP"
        },
        "precipitation_indicator": {
            "value": 4, "in_group_1": False, "in_group_3": False
        },
        "weather_indicator": {
            "value": 1, "automatic": False
        },
        "lowest_cloud_base": {
            "_table": "1600", "min": 100, "max": 200, "quantifier": None, "_code": 2, "unit": "m"
        },
        "visibility": {
            "_table": "4377", "value": 20000, "quantifier": None, "use90": True, "_code": 98, "unit": "m"
        },
        "cloud_cover": {
            "_table": "2700", "value": 8, "obscured": False, "_code": 8, "unit": "okta"
        },
        "surface_wind": {
            "direction": { "_table": "0877", "value": 130, "varAllUnknown": False, "calm": False, "_code": 13, "unit": "deg" },
            "speed": { "value": 7, "unit": "KT" }
        },
        "air_temperature": { "value": 0.1, "unit": "Cel" },
        "dewpoint_temperature": { "value": -0.4, "unit": "Cel" },
        "sea_level_pressure": { "value": 989.4, "unit": "hPa" },
        "pressure_tendency": {
            "tendency": { "_table": "0200", "value": 2 },
            "change":   { "value": 1.2, "unit": "hPa" }
        },
        "present_weather": {
            "_table": "4677", "value": 2, "time_before_obs": { "value": 6, "unit": "h" }
        },
        "past_weather": [
            { "_table": "4561", "value": 1 },
            { "_table": "4561", "value": 1 }
        ],
        "cloud_types": {
            "low_cloud_type":    { "_table": "0513", "value": 6 },
            "middle_cloud_type": None,
            "high_cloud_type":   None,
            "low_cloud_amount":  { "value": 8, "unit": "okta" }
        },
        "displacement": None,
        "sea_surface_temperature": {
            "value": 1.9, "unit": "Cel", "measurement_type": {
                "_table": "3850", "value": "Hull contact sensor", "_code": 4
            }
        },
        "wind_waves": [{
            "period": { "value": 0,   "unit": "s" },
            "height": { "value": 0.0, "unit": "m" },
            "instrumental": False, "accurate": False, "confused": False
        }],
        "swell_waves": [{
            "direction": { "_table": "0877", "value": None, "varAllUnknown": False, "calm": True, "_code": 0, "unit": "deg" },
            "period": { "value": 0,   "unit": "s" },
            "height": { "value": 0.0, "unit": "m" }
        },{
            "direction": None, "period": None, "height": None
        }],
        "wet_bulb_temperature": {
            "value": -0.1, "unit": "Cel", "_table": "3855", "sign": -1, "measured": True, "iced": False, "_code": 1
        },
        "sea_land_ice": {
            "text": "icy conditions"
        }
    }
class TestSynopAAXXSection5AfterSection1(BaseTestSynop):
    """
    Tests that section 5 groups are added to the "section5" key even if it follows
    directly after section 1
    """
    SYNOP = "AAXX 25064 04018 42589 43120 555 3//32 84619"
    expected = {
        'station_type': {'value': 'AAXX'},
        'obs_time': {
            'day': {'value': 25}, 'hour': {'value': 6}},
            'wind_indicator': {'value': 4, 'unit': 'KT', 'estimated': False},
            'station_id': {'value': '04018'},
            'region': {'value': 'VI'},
            'precipitation_indicator': {
                'value': 4, 'in_group_1': False, 'in_group_3': False
            },
        'weather_indicator': {'value': 2, 'automatic': False},
        'lowest_cloud_base': {
            '_table': '1600',
            'min': 600,
            'max': 1000,
            'quantifier': None,
            '_code': 5,
            'unit': 'm'
        },
        'visibility': {
            '_table': '4377',
            'value': 70000,
            'quantifier': 'isGreater',
            'use90': False,
            '_code': 89,
            'unit': 'm'
        },
        'cloud_cover': {
            '_table': '2700',
            'value': 4,
            'obscured': False,
            'unit': 'okta',
            '_code': 4
        },
        'surface_wind': {
            'direction': {
                '_table': '0877',
                'value': 310,
                'varAllUnknown': False,
                'calm': False,
                '_code': 31,
                'unit': 'deg'
            },
            'speed': {'value': 20, 'unit': 'KT'}
        },
        'section5': ['3//32', '84619']
    }
class TestSynopException:
    """
    Tests the various exceptions
    """
    SYNOP = "AAXX 27108 83/// /3502 11022 21042 39841 40025 52047"
    data  = {}
    def test_decode_exception(self):
        with pytest.raises(DecodeError):
            synop = s.SYNOP()
            data  = synop.decode(self.SYNOP)
    def test_encode_exception(self):
        with pytest.raises(EncodeError):
            encoded = s.SYNOP().encode(self.data)
