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
################################################################################
# CLASSES
################################################################################
class SynopTest:
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
            metafunc.parametrize("attr", list(data.keys()))

    def test_values(self, decoded, attr):
        if attr not in self.expected:
            assert False, "Expected attribute '{}' not present in decoded output".format(attr)
        else:
            assert decoded[attr] == self.expected[attr], "Decoded attribute '{}' does not match expected output".format(attr)

    def test_reencode(self, decoded):
        encoded = s.SYNOP().encode(decoded)
        assert encoded == self.SYNOP, "Re-encoded SYNOP does not match original"

class TestSynopAAXX(SynopTest):
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
class TestSynopBBXX(SynopTest):
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
            "latitude": "17.0", "longitude": "-157.7"
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
            "height": { "value": 2.0, "unit": "m" },
            "instrumental": True, "accurate": False, "confused": False
        },{
            "period": { "value": 6,   "unit": "s" },
            "height": { "value": 2.0, "unit": "m" },
            "instrumental": False, "accurate": False, "confused": False
        },{
            "period": None,
            "height": { "value": 2.1, "unit": "m" },
            "instrumental": True, "accurate": True, "confused": False
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
class TestSynopOOXX(SynopTest):
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
            "latitude": "-75.9",
            "longitude": "-87.4",
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
class TestSynopAAXXAntarctic(SynopTest):
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
class TestSynopAAXXRegionI(SynopTest):
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
class TestSynopBBXXAlternative(SynopTest):
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
            "latitude": "-60.7", "longitude": "-45.5"
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
