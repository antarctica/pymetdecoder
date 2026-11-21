from typing import Dict, List, Literal, Optional, Tuple, TypedDict, Union

# Code tables can produce scalar values, ranges, or nested observations.
ObservationValue = Union[
    None, bool, int, float, str, "ObservationFields",
    List["ObservationValue"], Tuple["ObservationValue", ...],
]
ObservationFields = Dict[str, ObservationValue]


class _StationType(TypedDict):
    value: Literal["AAXX", "BBXX", "OOXX"]


class _RegionCode(TypedDict):
    value: str
    _table: str


class _CallsignValue(TypedDict):
    value: str


class _Callsign(_CallsignValue, total=False):
    region: _RegionCode


class _TimeValue(TypedDict):
    value: int


class _ObservationTime(TypedDict):
    day: Optional[_TimeValue]
    hour: Optional[_TimeValue]


class _Region(TypedDict):
    value: Union[str, _RegionCode]


class _WaveHeight(TypedDict):
    value: float
    unit: Literal["m"]


class _Temperature(TypedDict):
    value: float
    unit: Literal["Cel"]


class _Pressure(TypedDict):
    value: float
    unit: Literal["hPa"]


class _Elevation(TypedDict):
    value: int
    unit: Literal["m", "ft"]


class _WavePeriod(TypedDict):
    value: int
    unit: Literal["s"]


class _RelativeHumidity(TypedDict):
    value: int
    unit: Literal["%"]


class _Coordinates(TypedDict):
    latitude: Optional[float]
    longitude: Optional[float]


class _StationPosition(_Coordinates, total=False):
    marsden_square: Optional[int]
    elevation: Optional[_Elevation]
    confidence: Optional[Literal["Poor", "Excellent", "Good", "Fair"]]


class _SpeedValue(TypedDict):
    value: int


class _WindSpeed(_SpeedValue, total=False):
    unit: Optional[Literal["m/s", "KT"]]


class _WindDirection(TypedDict):
    value: Optional[int]
    unit: Literal["deg"]
    _table: str
    _code: int
    calm: bool
    varAllUnknown: bool


class _SurfaceWind(TypedDict):
    speed: Optional[_WindSpeed]
    direction: Optional[_WindDirection]


class _Wave(TypedDict):
    period: Optional[_WavePeriod]
    height: Optional[_WaveHeight]


class _SwellWave(_Wave):
    direction: Optional[_WindDirection]


class _WindWave(_Wave):
    instrumental: bool
    accurate: bool
    confused: bool


class _ExactObservationTime(TypedDict):
    hour: Optional[_TimeValue]
    minute: Optional[_TimeValue]


class _PrecipitationIndicator(TypedDict):
    value: int
    in_group_1: bool
    in_group_3: bool


class _WeatherIndicator(TypedDict):
    value: Optional[int]
    automatic: bool


class _WindIndicator(TypedDict):
    value: int
    unit: Literal["m/s", "KT"]
    estimated: bool


class _IntegerCode(TypedDict):
    value: int
    _table: str


class _PressureTendencyChange(TypedDict):
    value: Optional[float]
    unit: Literal["hPa"]


class _PressureTendency(TypedDict):
    tendency: Optional[_IntegerCode]
    change: Optional[_PressureTendencyChange]


class _WeatherCode(_IntegerCode, total=False):
    time_before_obs: ObservationFields
    location: Optional[ObservationFields]
    movement: Optional[ObservationFields]


class _CodedObservation(TypedDict):
    _code: int
    _table: str


class _PrecipitationAmount(_CodedObservation):
    value: Union[int, float]
    quantifier: Optional[Literal["isGreaterOrEqual"]]
    trace: bool
    unit: Literal["mm"]


class _PrecipitationDuration(_CodedObservation):
    value: Literal[1, 2, 3, 6, 9, 12, 15, 18, 24]
    unit: Literal["h"]


class _Precipitation(TypedDict):
    amount: Optional[_PrecipitationAmount]
    time_before_obs: Optional[_PrecipitationDuration]


class _RadiationDuration(TypedDict):
    value: Literal[1, 24]
    unit: Literal["h"]


class _Radiation(TypedDict):
    value: Optional[int]
    unit: Literal["kJ/m2", "J/cm2"]
    time_before_obs: _RadiationDuration


class _CloudCover(_CodedObservation):
    value: Optional[int]
    obscured: bool
    unit: Literal["okta"]


class _CloudAmount(TypedDict):
    value: int
    unit: Literal["okta"]


class _CloudTypeCodes(TypedDict):
    low_cloud_type: Optional[_IntegerCode]
    middle_cloud_type: Optional[_IntegerCode]
    high_cloud_type: Optional[_IntegerCode]


class _CloudTypes(_CloudTypeCodes, total=False):
    low_cloud_amount: Optional[_CloudAmount]
    middle_cloud_amount: Optional[_CloudAmount]
    cloud_amount: Optional[_CloudAmount]


class _LowestCloudBase(_CodedObservation):
    min: int
    max: Optional[int]
    quantifier: Optional[Literal["isGreaterOrEqual"]]
    unit: Literal["m"]


class _Visibility(_CodedObservation):
    value: int
    quantifier: Optional[str]
    use90: bool
    unit: Literal["m"]


class _CardinalDirection(_CodedObservation):
    value: Optional[str]
    isCalmOrStationary: Optional[bool]
    allDirections: Optional[bool]


class _SpeedRange(TypedDict):
    min: int
    max: Optional[int]
    quantifier: Optional[str]
    unit: Literal["KT", "km/h"]


class _DisplacementSpeed(_CodedObservation):
    value: List[_SpeedRange]


class _Displacement(TypedDict):
    direction: Optional[_CardinalDirection]
    speed: Optional[_DisplacementSpeed]


class _SeaTemperatureMethod(_CodedObservation):
    value: str


class _SeaTemperatureValue(TypedDict):
    value: Optional[float]
    measurement_type: _SeaTemperatureMethod


class _SeaTemperature(_SeaTemperatureValue, total=False):
    unit: Literal["Cel"]


class _WetBulbTemperature(_Temperature, _CodedObservation):
    sign: int
    measured: bool
    iced: bool


class SYNOPData(TypedDict, total=False):
    """Decoded observations. Available keys depend on the report and its groups."""

    _error: List[str]
    _not_implemented: List[str]
    air_temperature: Optional[_Temperature]
    callsign: Optional[_Callsign]
    cloud_base_below_station: List[Optional[ObservationFields]]
    cloud_cover: Optional[_CloudCover]
    cloud_drift_direction: Optional[ObservationFields]
    cloud_elevation: Optional[ObservationFields]
    cloud_evolution: List[Optional[ObservationFields]]
    cloud_layer: List[Optional[ObservationFields]]
    cloud_types: Optional[_CloudTypes]
    condensation_trails: Optional[ObservationFields]
    day_darkness: Optional[ObservationFields]
    deposit_diameter: List[Optional[ObservationFields]]
    dewpoint_temperature: Optional[_Temperature]
    displacement: Optional[_Displacement]
    drift_snow: Optional[ObservationFields]
    evapotranspiration: Optional[ObservationFields]
    exact_obs_time: Optional[_ExactObservationTime]
    frozen_deposit: Optional[ObservationFields]
    geopotential: Optional[ObservationFields]
    ground_minimum_temperature: Optional[_Temperature]
    ground_state: Optional[ObservationFields]
    ground_state_grass: Optional[ObservationFields]
    ground_state_snow: Optional[ObservationFields]
    highest_gust: List[Optional[ObservationFields]]
    ice_accretion: Optional[ObservationFields]
    important_weather: List[Optional[ObservationFields]]
    local_precipitation: Optional[ObservationFields]
    lowest_cloud_base: Optional[_LowestCloudBase]
    max_low_cloud_concentration: List[Optional[ObservationFields]]
    max_wind: Optional[_SurfaceWind]
    maximum_temperature: Optional[_Temperature]
    minimum_temperature: Optional[_Temperature]
    mirage: List[Optional[ObservationFields]]
    mountain_condition: Optional[ObservationFields]
    obs_time: Optional[_ObservationTime]
    optical_phenomena: Optional[ObservationFields]
    past_weather: List[Optional[_WeatherCode]]
    precipitation_24h: Optional[_Precipitation]
    precipitation_begin: Optional[ObservationFields]
    precipitation_end: Optional[ObservationFields]
    precipitation_indicator: Optional[_PrecipitationIndicator]
    precipitation_s1: Optional[_Precipitation]
    precipitation_s3: Optional[_Precipitation]
    present_weather: Optional[_WeatherCode]
    present_weather_additional: List[Optional[_WeatherCode]]
    pressure_change: Optional[_Pressure]
    pressure_tendency: Optional[_PressureTendency]
    prevailing_wind: Optional[ObservationFields]
    radiation: Dict[str, List[Optional[_Radiation]]]
    region: Optional[_Region]
    relative_humidity: Optional[_RelativeHumidity]
    sea_land_ice: Optional[ObservationFields]
    sea_level_pressure: Optional[_Pressure]
    sea_state: Optional[ObservationFields]
    sea_surface_temperature: Optional[_SeaTemperature]
    sea_visibility: Optional[ObservationFields]
    section5: List[str]
    snow_cover_regularity: Optional[ObservationFields]
    snow_fall: Optional[ObservationFields]
    special_clouds: Optional[ObservationFields]
    st_elmos_fire: bool
    station_id: Optional[_CallsignValue]
    station_position: Optional[_StationPosition]
    station_pressure: Optional[_Pressure]
    station_type: _StationType
    sudden_humidity_change: Optional[ObservationFields]
    sudden_temperature_change: Optional[_Temperature]
    sunshine: List[Optional[ObservationFields]]
    surface_wind: Optional[_SurfaceWind]
    swell_waves: List[Optional[_SwellWave]]
    temperature_change: Optional[ObservationFields]
    tropical_cloud_drift_direction: Optional[ObservationFields]
    tropical_sky_state: Optional[ObservationFields]
    valley_clouds: Optional[ObservationFields]
    visibility: Optional[_Visibility]
    visibility_direction: List[Optional[ObservationFields]]
    weather_indicator: Optional[_WeatherIndicator]
    weather_info: Dict[str, Optional[ObservationFields]]
    wet_bulb_temperature: Optional[_WetBulbTemperature]
    wind_indicator: Optional[_WindIndicator]
    wind_waves: List[Optional[_WindWave]]
