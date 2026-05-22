"""
Master data NTE Dashboard
Operator: Telkomsel, Telkom, TIF
Area    : Bandung, Soreang
"""

# ── Area & Warehouse ─────────────────────────────────────────────────────────
# Key format: "OPERATOR - AREA"
AREA_CONFIG = {

    # ── TELKOMSEL ─────────────────────────────────────────────────────────────
    "TELKOMSEL - BANDUNG": {
        "operator": "TELKOMSEL",
        "area": "BANDUNG",
        "warehouses": [
            "TA SO CCAN AHMAD YANI WH",
            "TA SO CCAN BANDUNG CENTRUM WH",
            "TA SO CCAN CIANJUR WH",
            "TA SO CCAN CUAURA WH",
            "TA SO CCAN CIMAHI WH",
            "TA SO CCAN GEGERKALONG WH",
            "TA SO CCAN KOPO WH",
            "TA SO CCAN LEMBANG WH",
            "TA SO CCAN PADALARANG WH",
            "TA SO CCAN RAJAWALI WH",
            "TA SO CCAN SINDANGLAYA WH",
            "TA SO CCAN UJUNG BERUNG WH",
        ]
    },
    "TELKOMSEL - SOREANG": {
        "operator": "TELKOMSEL",
        "area": "SOREANG",
        "warehouses": [
            "TA SO CCAN SOREANG WH",
            "TA SO CCAN BANJARAN WH",
            "TA SO CCAN MAJALAYA WH",
            "TA SO CCAN SOREANG 2 WH",
            "TA SO CCAN CIWIDEY WH",
        ]
    },

    # ── TELKOM ────────────────────────────────────────────────────────────────
    "TELKOM - BANDUNG": {
        "operator": "TELKOM",
        "area": "BANDUNG",
        "warehouses": [
            "TA SO CCAN AHMAD YANI WH",
            "TA SO CCAN BANDUNG CENTRUM WH",
            "TA SO CCAN CIANJUR WH",
            "TA SO CCAN CUAURA WH",
            "TA SO CCAN CIMAHI WH",
            "TA SO CCAN GEGERKALONG WH",
            "TA SO CCAN KOPO WH",
            "TA SO CCAN LEMBANG WH",
            "TA SO CCAN PADALARANG WH",
            "TA SO CCAN RAJAWALI WH",
            "TA SO CCAN SINDANGLAYA WH",
            "TA SO CCAN UJUNG BERUNG WH",
        ]
    },
    "TELKOM - SOREANG": {
        "operator": "TELKOM",
        "area": "SOREANG",
        "warehouses": [
            "TA SO CCAN SOREANG WH",
            "TA SO CCAN BANJARAN WH",
            "TA SO CCAN MAJALAYA WH",
            "TA SO CCAN SOREANG 2 WH",
            "TA SO CCAN CIWIDEY WH",
        ]
    },

    # ── TIF ───────────────────────────────────────────────────────────────────
    "TIF - BANDUNG": {
        "operator": "TIF",
        "area": "BANDUNG",
        "warehouses": [
            "TA SO TIF BANDUNG CENTRIUM WH",
            "TA SO TIF CIJAURA WH",
            "TA SO TIF GEGERKALONG WH",
            "TA SO TIF UJUNGBERUNG WH",
        ]
    },
    "TIF - SOREANG": {
        "operator": "TIF",
        "area": "SOREANG",
        "warehouses": [
            "TA SO TIF KADIPATEN WH",
            "TA SO TIF MAJALENGKA WH",
            "TA SO TIF SUMEDANG WH",
        ]
    },
}

# ── Helper lookups ────────────────────────────────────────────────────────────
ALL_WAREHOUSES       = []
WAREHOUSE_TO_AREA_KEY = {}   # wh_name -> list of area_keys (WH bisa di >1 operator)

for area_key, config in AREA_CONFIG.items():
    for wh in config["warehouses"]:
        if wh not in ALL_WAREHOUSES:
            ALL_WAREHOUSES.append(wh)
        WAREHOUSE_TO_AREA_KEY.setdefault(wh, []).append(area_key)

ALL_OPERATORS = ["TELKOMSEL", "TELKOM", "TIF"]
ALL_AREAS     = ["BANDUNG", "SOREANG"]

def get_area_keys_by_operator(operator: str):
    return [k for k, v in AREA_CONFIG.items() if v["operator"] == operator]

def get_area_keys_by_area(area: str):
    return [k for k, v in AREA_CONFIG.items() if v["area"] == area]

# ── Status NTE ────────────────────────────────────────────────────────────────
NTE_STATUS = ["NTE BARU", "REFURBISH"]

# ── Katalog NTE ───────────────────────────────────────────────────────────────
NTE_CATALOG = {
    "AP": [
        "AP_CISCO_C9105AXI-F",
        "AP_CISCO_AIR-AP1832I-F-K9",
        "AP_CISCO_AIR-CAP1602E-C-K9",
        "AP_CISCO_AIR-CAP1602I-C-K9",
        "AP_CISCO_AIR-CAP3502E-C-K9",
        "AP_CISCO_AIR-CAP3502I-C-K9",
        "AP_HUAWEI_WA201DK-NE",
    ],
    "IP CAM": [
        "IP_Camera_Azustar_WM-03",
    ],
    "MESH WIFI": [
        "AP_MESH_ZTE_H196A_V9",
        "AP_MESH_FIBERHOME_SR1021E",
    ],
    "ONT DUAL BAND": [
        "ONT_FIBERHOME_HG6145D2",
        "ONT_HUAWEI_HG8145V5",
        "ONT_NOKIA_G-2425G-A",
        "ONT_ZTE_F672Y",
    ],
    "ONT ENTERPRISE": [
        "FH_AN_5261_DC_10G",
        "ONT_FIBERHOME_FH_AN_5231_AC_1G",
        "ONT_FIBERHOME_FH_AN_5261_DC_10G",
        "ONT_HUAWEI_MA_5822",
        "ONT_HUAWEI_MA5694_AC",
        "ONT_ZTE_F821AC",
        "ONT_ZTE_F939DC_DUAL_HOMING",
    ],
    "ONT PREMIUM": [
        "ONT_FIBERHOME_HG6145F1",
        "ONT_ZTE_F670_V2.0",
        "ONT_FIBERHOME_HG6245N",
    ],
    "ONT SINGLE BAND": [
        "ONT_FIBERHOME_AN5506-04-F",
        "ONT_FIBERHOME_AN5506-04-FS",
        "ONT_FIBERHOME_AN5506-07-B1",
        "ONT_FIBERHOME_HG6243C",
        "ONT_HUAWEI_HG8245",
        "ONT_HUAWEI_HG8245A",
        "ONT_HUAWEI_HG8245H",
        "ONT_HUAWEI_HG8245H5",
    ],
    "PLC": [
        "PLC_TL-PA7017_KIT",
        "PLC_TL-PA4010KIT",
    ],
    "SFP": [
        "SFP_10G_10KM",
        "SFP_10G_80KM",
        "SFP_1G_Electrical_RJ45",
    ],
    "STB": [
        "SetTopBox_ZTE_ZX10_B866F_V1.1",
        "SetTopBox_ZTE_B860H_V5.0",
        "SetTopBoxIPTV_ZTE_B860H",
        "SetTopBoxIPTV_ZTE_B860H_V2.1",
    ],
    "WIFI EXTENDER": [
        "WIFI_EXTENDER_EW-7438RPN",
    ],
}

ALL_NTE_TYPES     = []
NTE_TYPE_TO_JENIS = {}
for jenis, types in NTE_CATALOG.items():
    for t in types:
        ALL_NTE_TYPES.append(t)
        NTE_TYPE_TO_JENIS[t] = jenis

ALL_JENIS = list(NTE_CATALOG.keys())
