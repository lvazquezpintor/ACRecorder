"""
ACC Broadcasting Protocol - Tipos de mensajes y enums
"""

from enum import IntEnum


class InboundMessageTypes(IntEnum):
    """Tipos de mensajes que recibimos de ACC"""
    REGISTRATION_RESULT = 1
    REALTIME_UPDATE = 2
    REALTIME_CAR_UPDATE = 3
    ENTRY_LIST = 4
    TRACK_DATA = 5
    ENTRY_LIST_CAR = 6
    BROADCASTING_EVENT = 7


class OutboundMessageTypes(IntEnum):
    """Tipos de mensajes que enviamos a ACC"""
    REGISTER_COMMAND_APPLICATION = 1
    UNREGISTER_COMMAND_APPLICATION = 9
    REQUEST_ENTRY_LIST = 10
    REQUEST_TRACK_DATA = 11
    CHANGE_HUD_PAGE = 49
    CHANGE_FOCUS = 50
    REQUEST_INSTANT_REPLAY = 51
    PLAY_MANUAL_REPLAY_HIGHLIGHT = 52
    SAVE_MANUAL_REPLAY_HIGHLIGHT = 60


class BroadcastingCarLocationEnum(IntEnum):
    """Ubicación del coche"""
    NONE = 0
    TRACK = 1
    PITLANE = 2
    PIT_ENTRY = 3
    PIT_EXIT = 4


class SessionType(IntEnum):
    """Tipos de sesión"""
    PRACTICE = 0
    QUALIFYING = 1
    SUPERPOLE = 2
    RACE = 3
    HOTLAP = 4
    HOTSTINT = 5
    HOTLAP_SUPERPOLE = 6
    REPLAY = 7


class SessionPhase(IntEnum):
    """Fases de la sesión"""
    NONE = 0
    STARTING = 1
    PRE_FORMATION = 2
    FORMATION_LAP = 3
    PRE_SESSION = 4
    SESSION = 5
    SESSION_OVER = 6
    POST_SESSION = 7
    RESULT_UI = 8


class RaceSessionType(IntEnum):
    """Tipos de sesión de carrera"""
    PRACTICE = 0
    QUALIFYING = 4
    SUPERPOLE = 9
    RACE = 10
    HOTLAP = 11
    HOTSTINT = 12
    HOTLAP_SUPERPOLE = 13
    REPLAY = 14


class CarModelType(IntEnum):
    """Modelos de coches en ACC"""
    PORSCHE_991_GT3_R = 0
    MERCEDES_AMG_GT3 = 1
    FERRARI_488_GT3 = 2
    AUDI_R8_LMS = 3
    LAMBORGHINI_HURACAN_GT3 = 4
    MCLAREN_650S_GT3 = 5
    NISSAN_GT_R_NISMO_GT3_2018 = 6
    BMW_M6_GT3 = 7
    BENTLEY_CONTINENTAL_GT3_2018 = 8
    PORSCHE_991II_GT3_CUP = 9
    NISSAN_GT_R_NISMO_GT3_2017 = 10
    BENTLEY_CONTINENTAL_GT3_2016 = 11
    ASTON_MARTIN_VANTAGE_V12_GT3 = 12
    LAMBORGHINI_GALLARDO_R_EX = 13
    JAGUAR_G3 = 14
    LEXUS_RC_F_GT3 = 15
    LAMBORGHINI_HURACAN_EVO = 16
    HONDA_NSX_GT3 = 17
    LAMBORGHINI_HURACAN_SUPERTROFEO = 18
    AUDI_R8_LMS_EVO = 19
    AMR_V8_VANTAGE = 20
    HONDA_NSX_EVO = 21
    MCLAREN_720S_GT3 = 22
    PORSCHE_991II_GT3_R = 23
    FERRARI_488_GT3_EVO = 24
    MERCEDES_AMG_GT3_2020 = 25
    FERRARI_488_CHALLENGE_EVO = 26
    BMW_M2_CS_RACING = 27
    PORSCHE_992_GT3_CUP = 28
    LAMBORGHINI_HURACAN_SUPERTROFEO_EVO2 = 29
    BMW_M4_GT3 = 30
    AUDI_R8_LMS_GT3_EVO2 = 31
    FERRARI_296_GT3 = 32
    LAMBORGHINI_HURACAN_GT3_EVO2 = 33
    PORSCHE_992_GT3_R = 34
    MCLAREN_720S_GT3_EVO = 35
    FORD_MUSTANG_GT3 = 36


class DriverCategory(IntEnum):
    """Categorías de pilotos"""
    BRONZE = 0
    SILVER = 1
    GOLD = 2
    PLATINUM = 3


class CupCategory(IntEnum):
    """Categorías de Copa"""
    OVERALL = 0
    PRO_AM = 1
    AM = 2
    SILVER = 3
    NATIONAL = 4


class Nationality(IntEnum):
    """Nacionalidades - Lista simplificada de las más comunes"""
    ANY = 0
    ITALY = 1
    GERMANY = 2
    FRANCE = 3
    SPAIN = 4
    GREAT_BRITAIN = 5
    HUNGARY = 6
    BELGIUM = 7
    SWITZERLAND = 8
    AUSTRIA = 9
    RUSSIA = 10
    THAILAND = 11
    NETHERLANDS = 12
    POLAND = 13
    ARGENTINA = 14
    MONACO = 15
    IRELAND = 16
    BRAZIL = 17
    SOUTH_AFRICA = 18
    PUERTO_RICO = 19
    SLOVAKIA = 20
    OMAN = 21
    GREECE = 22
    SAUDI_ARABIA = 23
    NORWAY = 24
    TURKEY = 25
    SOUTH_KOREA = 26
    LEBANON = 27
    ARMENIA = 28
    MEXICO = 29
    SWEDEN = 30
    FINLAND = 31
    DENMARK = 32
    CROATIA = 33
    CANADA = 34
    CHINA = 35
    PORTUGAL = 36
    SINGAPORE = 37
    INDONESIA = 38
    USA = 39
    NEW_ZEALAND = 40
    AUSTRALIA = 41
    SAN_MARINO = 42
    UAE = 43
    LUXEMBOURG = 44
    KUWAIT = 45
    HONG_KONG = 46
    COLOMBIA = 47
    JAPAN = 48
    ANDORRA = 49
    AZERBAIJAN = 50
    BULGARIA = 51
    CUBA = 52
    CZECH_REPUBLIC = 53
    ESTONIA = 54
    GEORGIA = 55
    INDIA = 56
    ISRAEL = 57
    JAMAICA = 58
    LATVIA = 59
    LITHUANIA = 60
    MACAU = 61
    MALAYSIA = 62
    NEPAL = 63
    NEW_CALEDONIA = 64
    NIGERIA = 65
    NORTHERN_IRELAND = 66
    PAKISTAN = 67
    PALESTINE = 68
    PHILIPPINES = 69
    QATAR = 70
    ROMANIA = 71
    SCOTLAND = 72
    SERBIA = 73
    SLOVENIA = 74
    TAIWAN = 75
    UKRAINE = 76
    VENEZUELA = 77
    WALES = 78
    IRAN = 79
    BAHRAIN = 80
    ZIMBABWE = 81
    CHINESE_TAIPEI = 82
    CHILE = 83
    URUGUAY = 84
    MADAGASCAR = 85
