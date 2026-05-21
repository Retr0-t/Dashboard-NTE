"""
Master data untuk NTE Dashboard
"""

# Konfigurasi Area dan Warehouse
AREA_CONFIG = {
    "TELKOM BANDUNG": {
        "warehouses": [
            "WH Bandung Pusat",
            "WH Bandung Utara",
            "WH Bandung Selatan",
            "WH Bandung Timur",
            "WH Bandung Barat",
            "WH Cicadas",
            "WH Cimahi",
            "WH Cibeunying",
            "WH Bojonagara",
            "WH Kiaracondong",
            "WH Ujungberung",
            "WH Gedebage",
        ]
    },
    "TELKOM SOREANG": {
        "warehouses": [
            "WH Banjaran",
            "WH Kadipaten",
            "WH Majalaya",
            "WH Majalengka",
            "WH Sumedang",
        ]
    },
}

ALL_WAREHOUSES = []
WAREHOUSE_TO_AREA = {}
for area, config in AREA_CONFIG.items():
    for wh in config["warehouses"]:
        ALL_WAREHOUSES.append(wh)
        WAREHOUSE_TO_AREA[wh] = area

# Status NTE
NTE_STATUS = ["Baru", "Refurbish"]

# Jenis dan Type NTE
NTE_CATALOG = {
    "ONT": [
        "ONT_FiberHome_AN5506-04-FS",
        "ONT_FiberHome_AN5506-04-F",
        "ONT_FiberHome_AN5506-04-FA",
        "ONT_ZTE_F609",
        "ONT_ZTE_F660",
        "ONT_ZTE_F670L",
        "ONT_Huawei_HG8245H5",
        "ONT_Huawei_EG8145V5",
        "ONT_Nokia_G-010G-P",
    ],
    "STB": [
        "STB_ZTE_B700",
        "STB_ZTE_B760H",
        "STB_Huawei_EC6108V9",
        "STB_Skyworth_Q5001",
    ],
    "Kartu Perdana": [
        "KartuPerdana_IndiHome",
        "KartuPerdana_Orbit",
    ],
    "Remote": [
        "Remote_STB_Standard",
        "Remote_STB_Magic",
        "Remote_IndiHome",
    ],
    "Mesh WiFi": [
        "MeshWiFi_Huawei_WS7200",
        "MeshWiFi_Nokia_WiFi_Beacon",
        "MeshWiFi_ZTE_MF279",
        "AP_Cisco_C9105AXI-F",
        "AP_Cisco_C9115AXI-E",
    ],
    "Aksesoris": [
        "Kabel_Patch_Cord",
        "Splitter_1x2",
        "Splitter_1x4",
        "Splitter_1x8",
    ],
}

# Flatten semua type NTE
ALL_NTE_TYPES = []
NTE_TYPE_TO_JENIS = {}
for jenis, types in NTE_CATALOG.items():
    for t in types:
        ALL_NTE_TYPES.append(t)
        NTE_TYPE_TO_JENIS[t] = jenis

ALL_JENIS = list(NTE_CATALOG.keys())
