"""
Master data NTE Dashboard v3
Katalog NTE dipisah per operator karena setiap operator punya jenis/type berbeda
"""

# ══════════════════════════════════════════════════════════════════════════════
# AREA & WAREHOUSE CONFIG
# Key format: "OPERATOR - AREA"
# Edit nama WH di sini sesuai kebutuhan
# ══════════════════════════════════════════════════════════════════════════════
AREA_CONFIG = {

    # ── TELKOMSEL ─────────────────────────────────────────────────────────────
    "TELKOMSEL - BANDUNG": {
        "operator": "TELKOMSEL",
        "area": "BANDUNG",
        "warehouses": [
            "TA SO INV AHMAD YANI WH",
            "TA SO INV BANDUNG CENTRUM WH",
            "TA SO INV CIANJUR WH",
            "TA SO INV CUAURA WH",
            "TA SO INV CIMAHI WH",
            "TA SO INV GEGERKALONG WH",
            "TA SO INV KOPO WH",
            "TA SO INV LEMBANG WH",
            "TA SO INV PADALARANG WH",
            "TA SO INV RAJAWALI WH",
            "TA SO INV SINDANGLAYA WH",
            "TA SO INV UJUNG BERUNG WH",
             "TA WITEL INV JABAR TENGAH (BANDUNG) WH",
        ]
    },
    "TELKOMSEL - SOREANG": {
        "operator": "TELKOMSEL",
        "area": "SOREANG",
        "warehouses": [
            "TA SO INV KADIPATEN WH",
            "TA SO INV BANJARAN WH",
            "TA SO INV MAJALAYA WH",
            "TA SO INV SUMEDANG WH",
            "TA SO INV MAJALENGKA WH",
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
            "TA WITEL CCAN JABAR TENGAH (BANDUNG) WH",
        ]
    },
    "TELKOM - SOREANG": {
        "operator": "TELKOM",
        "area": "SOREANG",
        "warehouses": [
            "TA SO CCAN KADIPATEN WH",
            "TA SO CCAN BANJARAN WH",
            "TA SO CCAN MAJALAYA WH",
            "TA SO CCAN SUMEDANG WH",
            "TA SO CCAN MAJALENGKA WH",
            "TA WITEL CCAN BANDUNG BARAT WH"
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

# ── Helper lookups ─────────────────────────────────────────────────────────────
ALL_WAREHOUSES        = []
WAREHOUSE_TO_AREA_KEY = {}
for area_key, config in AREA_CONFIG.items():
    for wh in config["warehouses"]:
        if wh not in ALL_WAREHOUSES:
            ALL_WAREHOUSES.append(wh)
        WAREHOUSE_TO_AREA_KEY.setdefault(wh, []).append(area_key)

ALL_OPERATORS = ["TELKOMSEL", "TELKOM", "TIF"]
ALL_AREAS     = ["BANDUNG", "SOREANG"]

def get_area_keys_by_operator(operator):
    return [k for k, v in AREA_CONFIG.items() if v["operator"] == operator]

def get_area_keys_by_area(area):
    return [k for k, v in AREA_CONFIG.items() if v["area"] == area]


# ══════════════════════════════════════════════════════════════════════════════
# STATUS NTE
# ══════════════════════════════════════════════════════════════════════════════
NTE_STATUS = ["NTE BARU", "REFURBISH"]


# ══════════════════════════════════════════════════════════════════════════════
# KATALOG NTE — DIPISAH PER OPERATOR
# Setiap operator punya dict sendiri: { "JENIS": ["TYPE1", "TYPE2", ...] }
# Tambah/edit type NTE langsung di bagian operator yang sesuai
# ══════════════════════════════════════════════════════════════════════════════

# ── TELKOMSEL ─────────────────────────────────────────────────────────────────
# Sumber: laporan STOCK NTE TELKOMSEL BANDUNG (gambar)
NTE_CATALOG_TELKOMSEL = {
    "KARTU PERDANA": [
        "SIM_CARD_TELKOMSEL_SMOOA",
        "SIM_CARD_TELKOMSEL_ONE_REVAMP",
    ],
    "MESH WIFI": [
        "AP_MESH_ZTE_H196A_V9",
        "AP_MESH_FIBERHOME_SR1021E",
        "AP_MESH_HUAWEI_WA8021V5",
    ],
    "ONT DUAL BAND": [
        "ONT_FIBERHOME_HG6145D2",
        "ONT_HUAWEI_HG8145V5",
        "ONT_ZTE_F670L",
        "ONT_ZTE_F672Y",
    ],
    "ONT PREMIUM": [
        "ONT_FIBERHOME_HG6145F1",
        "ONT_HUAWEI_HG8145X6-10",
        "ONT_ZTE_F6600PV9.0",
        "ONT_FIBERHOME_HG6245N",   # REFURBISH
        "ONT_HUAWEI_HG8245U",      # REFURBISH
        "ONT_ZTE_F670_V2.0",       # REFURBISH
    ],
    "ONT SINGLE BAND": [
        "ONT_FIBERHOME_HG6243C",   # REFURBISH
        "ONT_HUAWEI_HG8245H5",     # REFURBISH
        "ONT_ZTE_F609_V5.3",       # REFURBISH
    ],
    "ORBIT": [
        "Orbit_IP_ZTE_MF920US",
        "ORBIT_SS_ex_ROUTER_HKM0128a",
        "ORBIT_SS_ZTE_K10_STAR_Z2",
        "ORBIT_SS_ZTE_K10_STAR_Z2_(EZNET)",
        "ORBIT_SS_ZTE_K10_STAR_Z2_(NON_REWORK)",
        "ORBIT_SS_ZTE_K10_STAR_Z2_(REWORK)",
    ],
    "REMOTE": [
        "REMOTE_ANDROID_ZTE_C3140_31KEY",
    ],
    "STB": [
        "SetTopBox_ZTE_B860H_V5.0",
        "SetTopBox_ZTE_ZX10_B866F_V1.1",
        "SetTopBox_ZTE_B860H_V5.0",    # REFURBISH
        "SetTopBox_ZTE_ZX10_B866F_V1.1", # REFURBISH
    ],
}
# Deduplikasi
for _j in NTE_CATALOG_TELKOMSEL:
    NTE_CATALOG_TELKOMSEL[_j] = list(dict.fromkeys(NTE_CATALOG_TELKOMSEL[_j]))


# ── TELKOM ────────────────────────────────────────────────────────────────────
# Edit sesuai laporan Telkom Anda
NTE_CATALOG_TELKOM = {
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


# ── TIF ───────────────────────────────────────────────────────────────────────
# Edit sesuai laporan TIF Anda
NTE_CATALOG_TIF = {
    "ONT DUAL BAND": [
        "ONT_FIBERHOME_HG6145D2",
        "ONT_HUAWEI_HG8145V5",
        "ONT_ZTE_F672Y",
    ],
    "ONT PREMIUM": [
        "ONT_FIBERHOME_HG6145F1",
        "ONT_ZTE_F670_V2.0",
    ],
    "ONT SINGLE BAND": [
        "ONT_FIBERHOME_AN5506-04-FS",
        "ONT_FIBERHOME_HG6243C",
        "ONT_HUAWEI_HG8245H5",
    ],
    "STB": [
        "SetTopBox_ZTE_B860H_V5.0",
        "SetTopBox_ZTE_ZX10_B866F_V1.1",
    ],
}


# ── Master router: operator -> catalog ────────────────────────────────────────
NTE_CATALOG_BY_OPERATOR = {
    "TELKOMSEL": NTE_CATALOG_TELKOMSEL,
    "TELKOM":    NTE_CATALOG_TELKOM,
    "TIF":       NTE_CATALOG_TIF,
}

# Flatten helpers per operator
def get_all_types(operator):
    return [t for types in NTE_CATALOG_BY_OPERATOR[operator].values() for t in types]

def get_type_to_jenis(operator):
    return {t: j
            for j, types in NTE_CATALOG_BY_OPERATOR[operator].items()
            for t in types}

def get_all_jenis(operator):
    return list(NTE_CATALOG_BY_OPERATOR[operator].keys())

# Backward compat — gabungan semua operator (untuk template Excel dll)
NTE_CATALOG = {}
for _op, _cat in NTE_CATALOG_BY_OPERATOR.items():
    for _j, _ts in _cat.items():
        NTE_CATALOG.setdefault(_j, [])
        for _t in _ts:
            if _t not in NTE_CATALOG[_j]:
                NTE_CATALOG[_j].append(_t)

ALL_NTE_TYPES = list({t for ts in NTE_CATALOG.values() for t in ts})

NTE_TYPE_TO_JENIS = {}
for _j, _ts in NTE_CATALOG.items():
    for _t in _ts:
        NTE_TYPE_TO_JENIS[_t] = _j
