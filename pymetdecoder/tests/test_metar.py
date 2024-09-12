################################################################################
# pymetdecoder/tests/test_metar.py
#
# Unit tests for METARs. Requires pytest
#
# TDBA 2024-09-11
#   * First version
################################################################################
# CONFIGURATION
################################################################################
import pytest
from pymetdecoder import metar as m
from pymetdecoder import DecodeError, EncodeError
################################################################################
# CLASSES
################################################################################
class BaseTestMetar:
    """
    Base class for Metar tests
    """
    METAR = None
    @pytest.fixture
    def decoded(self):
        metar = m.METAR()
        data  = metar.decode(self.METAR)
        yield data
    def pytest_generate_tests(self, metafunc):
        data = m.METAR().decode(self.METAR)

        if metafunc.function.__name__ == "test_values":
            attrs = self.TEST_ATTRS if hasattr(self, "TEST_ATTRS") else list(data.keys())
            metafunc.parametrize("attr", attrs)

    def test_values(self, decoded, attr):
        if attr not in self.expected:
            assert False, "Extra attribute '{}' found in decoded output".format(attr)
        else:
            assert decoded[attr] == self.expected[attr], "Decoded attribute '{}' does not match expected output".format(attr)
        
    def test_reencode(self, decoded):
        encoded = m.METAR().encode(decoded)
        assert encoded == self.METAR, "Re-encoded METAR does not match original"
    
    def test_expected(self, decoded):
        for k in self.expected:
            if k not in decoded:
                assert False, "Expected attribute '{}' not present in decoded output".format(k)
class TestSimpleMetar(BaseTestMetar):
    """
    Tests a simple METAR
    """
    METAR = "METAR SBTE 080000Z 02002KT 9999 FEW030 SCT080 31/19 Q1010"
    expected = {
        "is_special": False,
        "callsign": { "value": "SBTE" },
        "obs_time": {
            "day":    { "value": 8 },
            "hour":   { "value": 0 },
            "minute": { "value": 0 }
        },
        "is_automatic": False,
        "surface_wind": {
            "direction": { "value": 20, "unit": "deg", "variable": False },
            "speed": { "value": 2, "unit": "KT" },
            "gust": None,
            "variation": None
        },
        "prevailing_visibility": { "value": 10000, "unit": "m", "quantifier": "isGreaterThan", "direction": None },
        "cloud_types": [{
            "amount": { "value": "FEW", "min": 1, "max": 2, "unit": "okta", "significant_cloud": True },
            "height": { "_table": "1690", "value": 900, "quantifier": None, "_code": 30, "unit": "m" },
            "convective": { "cumulonimbus": False, "towering_cumulus": False, "not_observable": False }
        },{
            "amount": { "value": "SCT", "min": 3, "max": 4, "unit": "okta", "significant_cloud": True },
            "height": { "_table": "1690", "value": 2400, "quantifier": None, "_code": 80, "unit": "m" },
            "convective": { "cumulonimbus": False, "towering_cumulus": False, "not_observable": False }
        }],
        "temperature": {
            "air_temperature": { "value": 31, "unit": "Cel", "min": 30.5, "max": 31.5 },
            "dew_point_temperature": { "value": 19, "unit": "Cel", "min": 18.5, "max": 19.5 }
        },
        "qnh": { "value": 1010, "unit": "hPa" }
    }
class TestSpeci(BaseTestMetar):
    """
    Tests METAR is correctly identified as a SPECI and that everything decodes as
    expected
    """
    # METAR = "SPECI ETAD 170808Z 25007KT 9999 SCT011 OVC034 21/17 A2995 RMK AO2A"
    METAR = "SPECI LEJR 110350Z 16004KT 9999 FEW012 17/15 Q1013"
    # TEST_ATTRS = ["is_special"]
    expected = {
        "is_special": True,
        "callsign": { "value": "LEJR" },
        "obs_time": {
            "day":    { "value": 11 },
            "hour":   { "value": 3  },
            "minute": { "value": 50 }
        },
        "is_automatic": False,
        "surface_wind": {
            "direction": { "value": 160, "unit": "deg", "variable": False },
            "speed": { "value": 4, "unit": "KT" },
            "gust": None,
            "variation": None
        },
        "prevailing_visibility": { "value": 10000, "unit": "m", "quantifier": "isGreaterThan", "direction": None },
        "cloud_types": [{
            "amount": { "value": "FEW", "min": 1, "max": 2, "unit": "okta", "significant_cloud": True },
            "height": { "_table": "1690", "value": 360, "quantifier": None, "_code": 12, "unit": "m" },
            "convective": { "cumulonimbus": False, "towering_cumulus": False, "not_observable": False }
        }],
        "temperature": {
            "air_temperature": { "value": 17, "unit": "Cel", "min": 16.5, "max": 17.5 },
            "dew_point_temperature": { "value": 15, "unit": "Cel", "min": 14.5, "max": 15.5 }
        },
        "qnh": { "value": 1013, "unit": "hPa" }
    }
class TestComplexMetar(BaseTestMetar):
    """
    Tests complex functionality in a METAR including runway visual range (RVR), 
    present weather, visibility variation, no significant clouds (NSC) and 
    temperatures around 0 Cel
    """
    METAR = "METAR SBRB 080200Z 00000KT 7000 2000NW R24///// R06L/P2000 R22/1100VP2000U -RA FU NSC 00/M00 Q0987"
    expected = {
        "is_special": False,
        "callsign": { "value": "SBRB" },
        "obs_time": {
            "day":    { "value": 8 },
            "hour":   { "value": 2 },
            "minute": { "value": 0 }
        },
        "is_automatic": False,
        "surface_wind": {
            "direction": { "value": 0, "unit": "deg", "variable": False },
            "speed": { "value": 0, "unit": "KT" },
            "gust": None,
            "variation": None
        },
        "prevailing_visibility": { "value": 7000, "min": 7000, "max": 8000, "unit": "m", "direction": None },
        "visibility_variation":  { "value": 2000, "min": 2000, "max": 2100, "unit": "m", "direction": "NW" },
        "runway_visual_range": [{
            "runway": { "value": "24" },
            "visibility": None
        },{
            "runway": { "value": "06L" },
            "visibility": { "value": 2000, "unit": "m", "quantifier": "isGreaterOrEqual" }
        },{
            "runway": { "value": "22" },
            "visibility": { 
                "variation": { 
                    "min": { "value": 1100, "unit": "m" },
                    "max": { "value": 2000, "unit": "m", "quantifier": "isGreaterOrEqual", "tendency": "up" }
                }
            }
        }],
        "present_weather": [
            { "_table": "4678", "intensity": "light", "precipitation": ["rain"] },
            { "_table": "4678", "obscuration": "smoke" }
        ],
        "cloud_types": [{ 
            "amount": { "value": None, "significant_cloud": False },
            "height": None,
            "convective": { "cumulonimbus": False, "towering_cumulus": False, "not_observable": False }
        }],
        "temperature": {
            "air_temperature": { "value": 0, "unit": "Cel", "min": 0, "max": 0.5 },
            "dew_point_temperature": { "value": 0, "unit": "Cel", "min": -0.5, "max": 0 }
        },
        "qnh": { "value": 987, "unit": "hPa" }
    }
class TestCORAtStart(BaseTestMetar):
    """
    Tests METAR is decoded successfully if COR is at the start
    """
    METAR = "METAR COR SMJP 082200Z 14002KT 9999 FEW018 32/23 Q1010"
    expected = { 
        "is_special": False,
        "is_corrected": True,
        "callsign": { "value": "SMJP" },
        "obs_time": {
            "day":    { "value": 8  },
            "hour":   { "value": 22 },
            "minute": { "value": 0  }
        },
        "is_automatic": False,
        "surface_wind": {
            "direction": { "value": 140, "unit": "deg", "variable": False },
            "speed": { "value": 2, "unit": "KT" },
            "gust": None,
            "variation": None
        },
        "prevailing_visibility": { "value": 10000, "unit": "m", "quantifier": "isGreaterThan", "direction": None },
        "cloud_types": [{
            "amount": { "value": "FEW", "min": 1, "max": 2, "unit": "okta", "significant_cloud": True },
            "height": { "_table": "1690", "value": 540, "quantifier": None, "_code": 18, "unit": "m" },
            "convective": { "cumulonimbus": False, "towering_cumulus": False, "not_observable": False }
        }],
        "temperature": {
            "air_temperature": { "value": 32, "unit": "Cel", "min": 31.5, "max": 32.5 },
            "dew_point_temperature": { "value": 23, "unit": "Cel", "min": 22.5, "max": 23.5 }
        },
        "qnh": { "value": 1010, "unit": "hPa" }
    }
class TestCORInMiddle(TestCORAtStart):
    """
    Tests METAR is decoded successfully if COR is later on in the METAR. Note, 
    when re-encoding, this will put COR at the start, which the documentation
    implies is the correct way. Therefore, we compare a different result for re-encoding
    """
    METAR = "METAR SMJP 082200Z COR 14002KT 9999 FEW018 32/23 Q1010"
    def test_reencode(self, decoded):
        encoded = m.METAR().encode(decoded)
        assert encoded == TestCORAtStart.METAR, "Re-encoded METAR does not match original"
class TestCAVOK(BaseTestMetar):
    """
    Tests CAVOK correctly decoded
    """
    METAR = "METAR SBSM 082300Z 09010KT CAVOK 20/17 Q1015"
    expected = {
        "is_special": False,
        "callsign": { "value": "SBSM" },
        "obs_time": {
            "day":    { "value": 8  },
            "hour":   { "value": 23 },
            "minute": { "value": 0  }
        },
        "is_automatic": False,
        "surface_wind": {
            "direction": { "value": 90, "unit": "deg", "variable": False },
            "speed": { "value": 10, "unit": "KT" },
            "gust": None,
            "variation": None
        },
        "cavok": True,
        "temperature": {
            "air_temperature": { "value": 20, "unit": "Cel", "min": 19.5, "max": 20.5 },
            "dew_point_temperature": { "value": 17, "unit": "Cel", "min": 16.5, "max": 17.5 }
        },
        "qnh": { "value": 1015, "unit": "hPa" }
    }
class TestWindGustAndVariation(BaseTestMetar):
    """
    Tests wind gusts and variations are correctly decoded
    """
    METAR = "METAR SBMS 081700Z AUTO 12008G19KT 080V150 CAVOK 30/21 Q1014"
    expected = {
        "is_special": False,
        "callsign": { "value": "SBMS" },
        "obs_time": {
            "day":    { "value": 8  },
            "hour":   { "value": 17 },
            "minute": { "value": 0  }
        },
        "is_automatic": True,
        "surface_wind": {
            "direction": { "value": 120, "unit": "deg", "variable": False },
            "speed": { "value": 8, "unit": "KT" },
            "gust": { "value": 19, "unit": "KT" },
            "variation": { "from": 80, "to": 150, "unit": "deg" }
        },
        "cavok": True,
        "temperature": {
            "air_temperature": { "value": 30, "unit": "Cel", "min": 29.5, "max": 30.5 },
            "dew_point_temperature": { "value": 21, "unit": "Cel", "min": 20.5, "max": 21.5 }
        },
        "qnh": { "value": 1014, "unit": "hPa" }
    }
class BaseTrendsTest(BaseTestMetar):
    """
    Base class for trends tests
    """
    def pytest_generate_tests(self, metafunc):
        data = m.METAR().decode(self.METAR)

        if "trend" not in data:
            assert False, "No trend found in decoded output"
        if metafunc.function.__name__ == "test_values":
            attrs = self.TEST_ATTRS if hasattr(self, "TEST_ATTRS") else list(data["trend"].keys())
            metafunc.parametrize("attr", attrs)
    def test_values(self, decoded, attr):
        if attr not in self.expected:
            assert False, "Expected attribute '{}' not present in decoded output".format(attr)
        elif "trend" not in decoded:
            assert False, "No trend found in decoded output"
        else:
            assert decoded["trend"][attr] == self.expected[attr], "Decoded attribute '{}' does not match expected output".format(attr)
    def test_expected(self, decoded):
        for k in self.expected:
            if k not in decoded["trend"]:
                assert False, "Expected attribute '{}' not present in decoded output".format(k)
class TestTrendsNOSIG(BaseTrendsTest):
    METAR = "METAR SYCJ 170100Z 04006KT 9999 SCT019 SCT100 27/25 Q1011 NOSIG"
    expected = {
        "change": "NOSIG"
    }
class TestTrendsTEMPO(BaseTrendsTest):
    METAR = "METAR COR SFAL 091450Z 27016KT 9999 SCT048 06/02 Q1005 TEMPO 24001KT 6000 -SHRASN SCT015"
    expected = {
        "change": "TEMPO",
        "surface_wind": {
            "direction": { "value": 240, "unit": "deg", "variable": False },
            "speed": { "value": 1, "unit": "KT" },
            "gust": None,
            "variation": None
        },
        "visibility": { "value": 6000, "unit": "m", "min": 6000, "max": 7000, "direction": None },
        "present_weather": [
            { "_table": "4678", "intensity": "light", "precipitation": ["rain", "snow"], "descriptor": "shower(s)" }
        ],
        "cloud_types": [{
            "amount": { "value": "SCT", "min": 3, "max": 4, "unit": "okta", "significant_cloud": True },
            "height": { "_table": "1690", "value": 450, "quantifier": None, "_code": 15, "unit": "m" },
            "convective": { "cumulonimbus": False, "towering_cumulus": False, "not_observable": False }
        }]
    }
class TestTrendsBECMG(BaseTrendsTest):
    METAR = "METAR SKBQ 221200Z 08004KT 6000 BKN010 26/25 Q1011 BECMG FM1230 TL1330 SCT012"
    expected = {
        "change": "BECMG",
        "from": {
            "hour":  { "value": 12 },
            "minute": { "value": 30 }
        },
        "to": {
            "hour":  { "value": 13 },
            "minute": { "value": 30 }
        },
        "cloud_types": [{
            "amount": { "value": "SCT", "min": 3, "max": 4, "unit": "okta", "significant_cloud": True },
            "height": { "_table": "1690", "value": 360, "quantifier": None, "_code": 12, "unit": "m" },
            "convective": { "cumulonimbus": False, "towering_cumulus": False, "not_observable": False }
        }]
    }
class TestNonStandardMetar(BaseTestMetar):
    """
    Tests non-standard elements (visibility in statute miles and QNH in inches of
    Hg). Also tests recent weather (RExxx) and convective clouds
    """
    METAR = "METAR SYCJ 111700Z 20004KT 5SM FEW017CB BKN038TCU 28/25 A2992 RETS NOSIG"
    expected = {
        "is_special": False,
        "callsign": { "value": "SYCJ" },
        "obs_time": {
            "day":    { "value": 11  },
            "hour":   { "value": 17 },
            "minute": { "value": 0  }
        },
        "is_automatic": False,
        "surface_wind": {
            "direction": { "value": 200, "unit": "deg", "variable": False },
            "speed": { "value": 4, "unit": "KT" },
            "gust": None,
            "variation": None
        },
        "prevailing_visibility": { "value": 5, "unit": "[mi_us]", "direction": None },
        "cloud_types": [{
            "amount": { "value": "FEW", "min": 1, "max": 2, "unit": "okta", "significant_cloud": True },
            "height": { "_table": "1690", "value": 510, "quantifier": None, "_code": 17, "unit": "m" },
            "convective": { "cumulonimbus": True, "towering_cumulus": False, "not_observable": False }
        },{
            "amount": { "value": "BKN", "min": 5, "max": 7, "unit": "okta", "significant_cloud": True },
            "height": { "_table": "1690", "value": 1140, "quantifier": None, "_code": 38, "unit": "m" },
            "convective": { "cumulonimbus": False, "towering_cumulus": True, "not_observable": False }
        }],
        "temperature": {
            "air_temperature": { "value": 28, "unit": "Cel", "min": 27.5, "max": 28.5 },
            "dew_point_temperature": { "value": 25, "unit": "Cel", "min": 24.5, "max": 25.5 }
        },
        "qnh": { "value": 29.92, "unit": "inHg" },
        "recent_weather": { "_table": "4678", "descriptor": "thunderstorm" },
        "trend": { "change": "NOSIG" }
    }
