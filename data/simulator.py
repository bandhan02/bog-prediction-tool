#--------------------------------
import numpy as np
import CoolProp.CoolProp as CP

def calculate_bog_rate(T_ambient, T_lng=-162.0, U=0.32, A=5000.0):
    """
    Calculate BOG rate from basic heat ingress.
    
    T_ambient : outside temperature in Celsius
    T_lng     : LNG temperature in Celsius (default -162°C)
    U         : heat transfer coefficient W/m2·K
                CORRECTED: 0.32 = realistic membrane carrier
                (was 0.20 — that was near-perfect lab insulation)
    A         : total tank surface area in m2 (typical large carrier)
    
    Returns BOG rate as % of cargo per day
    """

    T_amb_K = T_ambient + 273.15
    T_lng_K = T_lng + 273.15
    delta_T = T_amb_K - T_lng_K

    Q_watts = U * A * delta_T

    h_vap = CP.PropsSI('H', 'P', 101325, 'Q', 1, 'Methane') - \
            CP.PropsSI('H', 'P', 101325, 'Q', 0, 'Methane')

    m_bog_per_second = Q_watts / h_vap
    m_bog_per_day    = m_bog_per_second * 3600 * 24
    total_cargo_kg   = 70_000_000

    bog_rate_percent = (m_bog_per_day / total_cargo_kg) * 100

    return bog_rate_percent


if __name__ == "__main__":
    bog = calculate_bog_rate(T_ambient=25.0)
    print(f"BOG rate at 25°C ambient: {bog:.4f}% per day")
    print(f"Expected range: 0.08% to 0.15% per day")

    if 0.05 < bog < 0.20:
        print("PHYSICS CHECK PASSED — result is in realistic range")
    else:
        print("PHYSICS CHECK FAILED — something is wrong")

#---------------------------------------------------------
import numpy as np
import CoolProp.CoolProp as CP

# ====TANK GEOMETRY===============
TANK_AREA = {
    "bottom": 1200.0,
    "sides":  3200.0,
    "top":    1100.0,    # CORRECTED: was 600 m² — too small for 174k m³ vessel
                         # Real exposed dome area on large membrane carrier ~1100 m²
}

#======U VALUES PER ZONE (W/m²·K)================
# CORRECTED: previous values (0.18–0.25) were near-perfect lab insulation
# Real membrane carriers (GTT NO96 / Mark III): 0.25–0.40 W/m²·K effective
U_VALUES = {
    "bottom": 0.26,   # slightly better — seawater pressure improves insulation
    "sides":  0.32,   # standard real-world membrane insulation performance
    "top":    0.36,   # slightly worse — dome geometry more complex
}

# ===SOLAR ABSORPTIVITY=========================
# CORRECTED earlier was 0.15 (highly reflective new surface)
# Real painted or weathered ship surface: 0.35–0.55
# Using 0.40 as realistic operational value for assumption with the data and value 
SOLAR_ABSORPTIVITY = 0.40

def get_h_vaporization(composition="standard"):
    H_liq = CP.PropsSI('H', 'P', 101325, 'Q', 0, 'Methane')
    H_vap = CP.PropsSI('H', 'P', 101325, 'Q', 1, 'Methane')
    return H_vap - H_liq


def calculate_zone_heat(zone, T_outside, T_lng_C=-162.0, hull_condition=1.0):
    """
    Calculate heat ingress for a single tank zone.
    
    zone          : "bottom", "sides", or "top"
    T_outside     : temperature the zone sees, in Celsius
    T_lng_C       : LNG temperature in Celsius
    hull_condition: degradation multiplier 1.0 (new) to 1.15 (aged insulation)
                    NOT a sensor — set manually by Chief Officer from dry-dock records.
    
    Returns heat ingress Q in Watts for that zone
    """

    T_out_K = T_outside + 273.15
    T_lng_K = T_lng_C + 273.15
    delta_T  = T_out_K - T_lng_K

    U_effective = U_VALUES[zone] * hull_condition
    A = TANK_AREA[zone]

    Q = U_effective * A * delta_T
    return Q


def calculate_bog_rate(
    T_air,
    T_sea,
    T_lng=-162.0,
    hull_condition=1.0,
    composition="standard"
):
    Q_bottom = calculate_zone_heat("bottom", T_sea,               T_lng, hull_condition)
    Q_sides  = calculate_zone_heat("sides",  (T_air + T_sea) / 2, T_lng, hull_condition)
    Q_top    = calculate_zone_heat("top",    T_air,               T_lng, hull_condition)

    Q_total = Q_bottom + Q_sides + Q_top

    h_vap = get_h_vaporization(composition)

    m_bog_per_second = Q_total / h_vap
    m_bog_per_day    = m_bog_per_second * 3600 * 24
    total_cargo_kg   = 174_000 * 450

    bog_rate_percent = (m_bog_per_day / total_cargo_kg) * 100

    return bog_rate_percent, {
        "Q_bottom_kW": Q_bottom / 1000,
        "Q_sides_kW":  Q_sides  / 1000,
        "Q_top_kW":    Q_top    / 1000,
        "Q_total_kW":  Q_total  / 1000,
        "m_bog_kg_per_day": m_bog_per_day,
    }


if __name__ == "__main__":

    print("=" * 55)
    print("STAGE 2 — THREE-ZONE HEAT INGRESS TEST")
    print("=" * 55)

    bog, details = calculate_bog_rate(T_air=32.0, T_sea=28.0)
    print(f"\nTropical route (air=32°C, sea=28°C):")
    print(f"  Q_bottom : {details['Q_bottom_kW']:.1f} kW")
    print(f"  Q_sides  : {details['Q_sides_kW']:.1f} kW")
    print(f"  Q_top    : {details['Q_top_kW']:.1f} kW")
    print(f"  Q_total  : {details['Q_total_kW']:.1f} kW")
    print(f"  BOG rate : {bog:.4f}% per day")

    bog2, details2 = calculate_bog_rate(T_air=5.0, T_sea=8.0)
    print(f"\nNorth Atlantic winter (air=5°C, sea=8°C):")
    print(f"  Q_total  : {details2['Q_total_kW']:.1f} kW")
    print(f"  BOG rate : {bog2:.4f}% per day")

    bog3, _ = calculate_bog_rate(T_air=32.0, T_sea=28.0, hull_condition=1.15)
    print(f"\nTropical route WITH aged insulation (hull_condition=1.15):")
    print(f"  BOG rate : {bog3:.4f}% per day")
    print(f"  Increase vs new insulation: {((bog3-bog)/bog)*100:.1f}%")

    print(f"\n{'=' * 55}")
    print("PHYSICS VALIDATION:")
    print(f"  Tropical BOG: {bog:.4f}% — expected 0.10–0.15%")
    print(f"  Atlantic BOG: {bog2:.4f}% — expected 0.08–0.11%")
    print(f"  Tropical > Atlantic: {bog > bog2} — must be True")
    print(f"  Aged > New: {bog3 > bog} — must be True")

#-----------------------------
import numpy as np
import CoolProp.CoolProp as CP

#============TANK GEOMETRY==================
TANK_AREA = {
    "bottom": 1200.0,
    "sides":  3200.0,
    "top":    1100.0,    # CORRECTED: was 600 m²
}

U_VALUES = {
    "bottom": 0.26,
    "sides":  0.32,
    "top":    0.36,
}

# CORRECTED: was 0.15 (unrealistically reflective)
# Weathered painted steel surface on real vessel: 0.40
SOLAR_ABSORPTIVITY = 0.40

def get_h_vaporization():
    H_liq = CP.PropsSI('H', 'P', 101325, 'Q', 0, 'Methane')
    H_vap = CP.PropsSI('H', 'P', 101325, 'Q', 1, 'Methane')
    return H_vap - H_liq


def solar_radiation(hour_of_day):
    """
    Solar radiation W/m² as a function of hour of day.
    Zero at night, peak ~900 W/m² at solar noon.
    """
    if 6 <= hour_of_day <= 18:
        angle = np.pi * (hour_of_day - 6) / 12
        radiation = 900.0 * np.sin(angle)
    else:
        radiation = 0.0
    return radiation


def sloshing_factor(wave_height, fill_level):
    """
    Sloshing BOG amplification factor.
    
    CORRECTED: was 1.0 + (0.03 * ...) — maximum +3%, modelled as rounding error.
    Reality: sloshing can increase BOG by 10–40% in extreme conditions.
    
    New range:
      Calm conditions:          +2–5%
      Moderate (2m waves, 50%): +10–15%
      Extreme (4m waves, 50%):  +25–35%
    
    wave_height : significant wave height in metres
    fill_level  : fraction of tank filled (0.0 to 1.0)
    """
    if fill_level > 0.90 or fill_level < 0.10:
        fill_factor = 0.05   # minimal sloshing at near-full or near-empty
    elif 0.30 <= fill_level <= 0.70:
        fill_factor = 1.0    # maximum sloshing risk at partial fill
    else:
        fill_factor = 0.45   # moderate sloshing risk

    # Normalize wave height: 4m = maximum expected, maps to factor 1.0
    wave_factor = min(wave_height / 4.0, 1.0)

    # CORRECTED: maximum amplification raised from 0.03 to 0.35
    # Physically: up to +35% BOG in worst-case sloshing conditions
    sloshing_amplification = 1.0 + (0.35 * fill_factor * wave_factor)

    return sloshing_amplification


def calculate_zone_heat(zone, T_outside, T_lng_C, hull_condition,
                         solar_W=0.0):
    T_out_K = T_outside + 273.15
    T_lng_K = T_lng_C   + 273.15
    delta_T  = T_out_K - T_lng_K

    U_effective = U_VALUES[zone] * hull_condition
    A = TANK_AREA[zone]

    Q_convective = U_effective * A * delta_T

    Q_solar = 0.0
    if zone == "top" and solar_W > 0:
        Q_solar = SOLAR_ABSORPTIVITY * A * solar_W

    return Q_convective + Q_solar


def calculate_bog_rate(
    T_air,
    T_sea,
    T_lng=-162.0,
    hull_condition=1.0,
    hour_of_day=12.0,
    wave_height=1.5,
    fill_level=0.95,
    composition="standard"
):
    solar_W = solar_radiation(hour_of_day)

    Q_bottom = calculate_zone_heat("bottom", T_sea,               T_lng, hull_condition)
    Q_sides  = calculate_zone_heat("sides",  (T_air + T_sea) / 2, T_lng, hull_condition)
    Q_top    = calculate_zone_heat("top",    T_air,               T_lng, hull_condition,
                                   solar_W=solar_W)

    Q_total = Q_bottom + Q_sides + Q_top

    h_vap = get_h_vaporization()

    m_bog_per_second = Q_total / h_vap
    m_bog_per_day    = m_bog_per_second * 3600 * 24
    total_cargo_kg   = 174_000 * 450

    bog_base  = (m_bog_per_day / total_cargo_kg) * 100
    slosh     = sloshing_factor(wave_height, fill_level)
    bog_final = bog_base * slosh

    return bog_final, {
        "Q_bottom_kW":     Q_bottom / 1000,
        "Q_sides_kW":      Q_sides  / 1000,
        "Q_top_kW":        Q_top    / 1000,
        "Q_solar_W":       solar_W,
        "Q_total_kW":      Q_total  / 1000,
        "m_bog_kg_per_day": m_bog_per_day,
        "sloshing_factor": slosh,
        "bog_base_pct":    bog_base,
        "bog_final_pct":   bog_final,
    }


if __name__ == "__main__":

    print("=" * 60)
    print("STAGE 3 — ENVIRONMENTAL VARIABLES TEST")
    print("=" * 60)

    bog_noon,  d1 = calculate_bog_rate(T_air=30, T_sea=25,
                                        hour_of_day=12.0, wave_height=1.0)
    bog_night, d2 = calculate_bog_rate(T_air=28, T_sea=25,
                                        hour_of_day=2.0,  wave_height=1.0)
    print(f"\nSolar radiation effect:")
    print(f"  Midday   solar: {d1['Q_solar_W']:.0f} W/m²  BOG: {bog_noon:.4f}%/day")
    print(f"  Midnight solar: {d2['Q_solar_W']:.0f} W/m²  BOG: {bog_night:.4f}%/day")
    print(f"  Midday > Midnight: {bog_noon > bog_night} — must be True")

    bog_calm,  _ = calculate_bog_rate(T_air=25, T_sea=20,
                                       wave_height=0.5, fill_level=0.50)
    bog_rough, _ = calculate_bog_rate(T_air=25, T_sea=20,
                                       wave_height=4.0, fill_level=0.50)
    print(f"\nSloshing effect (50% fill level):")
    print(f"  Calm sea  (0.5m): {bog_calm:.4f}%/day")
    print(f"  Rough sea (4.0m): {bog_rough:.4f}%/day")
    print(f"  Sloshing amplification: {bog_rough/bog_calm:.2f}x — expect 1.30–1.35x")
    print(f"  Rough > Calm: {bog_rough > bog_calm} — must be True")

    bog_full,    _ = calculate_bog_rate(T_air=25, T_sea=20,
                                         wave_height=3.0, fill_level=0.95)
    bog_partial, _ = calculate_bog_rate(T_air=25, T_sea=20,
                                         wave_height=3.0, fill_level=0.50)
    print(f"\nFill level sloshing comparison (3m waves):")
    print(f"  Full cargo (95%):    {bog_full:.4f}%/day")
    print(f"  Partial cargo (50%): {bog_partial:.4f}%/day")
    print(f"  Partial > Full: {bog_partial > bog_full} — must be True")

    print(f"\n{'=' * 60}")
    print("All three must show True to pass Stage 3")

#-----------------------------------------
import numpy as np
import CoolProp.CoolProp as CP

# ── TANK GEOMETRY=================
TANK_AREA_BASE = {
    "bottom": 1200.0,
    "sides":  3200.0,
    "top":    1100.0,    # CORRECTED: was 600 m²
}

# CORRECTED: realistic membrane carrier U values
U_VALUES_BASE = {
    "bottom": 0.26,
    "sides":  0.32,
    "top":    0.36,
}

# CORRECTED: realistic weathered painted surface
SOLAR_ABSORPTIVITY = 0.40

DESIGN_DRAFT    = 11.5
SHIP_LENGTH     = 295.0
SHIP_BEAM       = 46.0


def get_h_vaporization():
    H_liq = CP.PropsSI('H', 'P', 101325, 'Q', 0, 'Methane')
    H_vap = CP.PropsSI('H', 'P', 101325, 'Q', 1, 'Methane')
    return H_vap - H_liq


def speed_convection_factor(speed_knots):
    """
    Speed increases forced convection on hull surface.
    Factor: 1.0 at rest → ~1.12 at 19 knots.
    """
    v_ms = speed_knots * 0.5144
    factor = 1.0 + 0.006 * v_ms
    return factor


def draft_area_adjustment(draft_m):
    """
    Draft determines submerged vs air-exposed hull area.
    """
    submerged_fraction = min(draft_m / DESIGN_DRAFT, 1.0)
    sides_submerged    = TANK_AREA_BASE["sides"] * submerged_fraction
    sides_exposed      = TANK_AREA_BASE["sides"] * (1 - submerged_fraction)
    return {
        "bottom":          TANK_AREA_BASE["bottom"],
        "sides_submerged": sides_submerged,
        "sides_exposed":   sides_exposed,
        "top":             TANK_AREA_BASE["top"],
    }


def solar_radiation(hour_of_day):
    if 6 <= hour_of_day <= 18:
        return 900.0 * np.sin(np.pi * (hour_of_day - 6) / 12)
    return 0.0


def sloshing_factor(wave_height, fill_level):
    """
    CORRECTED: max amplification raised from 0.03 to 0.35.
    Reflects real sloshing BOG increase of 10–40% in extreme conditions.
    """
    if fill_level > 0.90 or fill_level < 0.10:
        fill_factor = 0.05
    elif 0.30 <= fill_level <= 0.70:
        fill_factor = 1.0
    else:
        fill_factor = 0.45
    wave_factor = min(wave_height / 4.0, 1.0)
    return 1.0 + (0.35 * fill_factor * wave_factor)


def calculate_bog_rate(
    T_air,
    T_sea,
    T_lng=-162.0,
    hull_condition=1.0,
    hour_of_day=12.0,
    wave_height=1.5,
    fill_level=0.95,
    speed_knots=15.0,
    draft_m=11.5,
    composition="standard"
):
    solar_W  = solar_radiation(hour_of_day)
    areas    = draft_area_adjustment(draft_m)
    spd_fac  = speed_convection_factor(speed_knots)

    dT_sea = (T_sea + 273.15) - (T_lng + 273.15)
    dT_air = (T_air + 273.15) - (T_lng + 273.15)

    U_bot   = U_VALUES_BASE["bottom"] * hull_condition
    U_sides = U_VALUES_BASE["sides"]  * hull_condition * spd_fac
    U_top   = U_VALUES_BASE["top"]    * hull_condition * spd_fac

    Q_bottom    = U_bot   * areas["bottom"]          * dT_sea
    Q_sides_sub = U_sides * areas["sides_submerged"] * dT_sea
    Q_sides_exp = U_sides * areas["sides_exposed"]   * dT_air
    Q_top       = (U_top  * areas["top"]             * dT_air) + \
                  (SOLAR_ABSORPTIVITY * areas["top"]  * solar_W)

    Q_total = Q_bottom + Q_sides_sub + Q_sides_exp + Q_top

    h_vap            = get_h_vaporization()
    m_bog_per_second = Q_total / h_vap
    m_bog_per_day    = m_bog_per_second * 3600 * 24
    total_cargo_kg   = 174_000 * 450

    bog_base  = (m_bog_per_day / total_cargo_kg) * 100
    slosh     = sloshing_factor(wave_height, fill_level)
    bog_final = bog_base * slosh

    return bog_final, {
        "Q_bottom_kW":      Q_bottom / 1000,
        "Q_sides_kW":       (Q_sides_sub + Q_sides_exp) / 1000,
        "Q_top_kW":         Q_top    / 1000,
        "Q_total_kW":       Q_total  / 1000,
        "speed_factor":     spd_fac,
        "sloshing_factor":  slosh,
        "m_bog_kg_per_day": m_bog_per_day,
        "bog_base_pct":     bog_base,
        "bog_final_pct":    bog_final,
    }


if __name__ == "__main__":

    print("=" * 60)
    print("STAGE 4 — SHIP PARAMETERS TEST")
    print("=" * 60)

    bog_slow, d1 = calculate_bog_rate(T_air=25, T_sea=20,
                                       speed_knots=5.0,  draft_m=11.5)
    bog_fast, d2 = calculate_bog_rate(T_air=25, T_sea=20,
                                       speed_knots=19.0, draft_m=11.5)
    print(f"\nSpeed effect (same weather, same draft):")
    print(f"  Slow steam 5kn:  BOG={bog_slow:.4f}%  speed_factor={d1['speed_factor']:.3f}")
    print(f"  Full speed 19kn: BOG={bog_fast:.4f}%  speed_factor={d2['speed_factor']:.3f}")
    print(f"  Full speed > Slow steam: {bog_fast > bog_slow} — must be True")

    bog_light, _ = calculate_bog_rate(T_air=25, T_sea=15,
                                       speed_knots=15.0, draft_m=7.0)
    bog_laden, _ = calculate_bog_rate(T_air=25, T_sea=15,
                                       speed_knots=15.0, draft_m=11.5)
    print(f"\nDraft effect (light ballast vs full load):")
    print(f"  Light draft 7.0m:  BOG={bog_light:.4f}%/day")
    print(f"  Full draft 11.5m:  BOG={bog_laden:.4f}%/day")
    print(f"  Light > Laden: {bog_light > bog_laden} — must be True")

    bog_worst, dw = calculate_bog_rate(
        T_air=35, T_sea=30, hour_of_day=12,
        wave_height=3.5, fill_level=0.50,
        speed_knots=18.0, draft_m=9.0,
        hull_condition=1.15
    )
    print(f"\nWorst-case scenario (hot/rough/fast/partial/aged):")
    print(f"  BOG rate: {bog_worst:.4f}%/day")
    print(f"  Q_total:  {dw['Q_total_kW']:.1f} kW")
    print(f"  BOG below 0.30%: {bog_worst < 0.30} — must be True (sanity check)")

#-------------------------------
import numpy as np
import pandas as pd
import CoolProp.CoolProp as CP

# ── TANK GEOMETRY ==========
TANK_AREA_BASE = {
    "bottom": 1200.0,
    "sides":  3200.0,
    "top":    1100.0,    # CORRECTED: was 600 m²
}

# CORRECTED: realistic membrane carrier U values
U_VALUES_BASE = {
    "bottom": 0.26,
    "sides":  0.32,
    "top":    0.36,
}

# CORRECTED: weathered painted steel surface
SOLAR_ABSORPTIVITY = 0.40

DESIGN_DRAFT   = 11.5
TANK_VOLUME_M3 = 174_000          # m³ total tank volume
LNG_DENSITY    = 450.0            # kg/m³ average LNG density

# ========LNG COMPOSITION PROFILES=============
LNG_COMPOSITIONS = {
    "lean":     {"CH4": 0.98, "C2H6": 0.01, "C3H8": 0.01},
    "standard": {"CH4": 0.91, "C2H6": 0.07, "C3H8": 0.02},
    "rich":     {"CH4": 0.85, "C2H6": 0.12, "C3H8": 0.03},
}

# =========VOYAGE SCENARIOS=================
SCENARIOS = {
    "full_cargo_open_sea": {
        "fill_level_range":  (0.88, 0.98),
        "speed_range":       (14.0, 19.0),
        "wave_height_range": (0.5,  3.0),
        "draft_range":       (10.5, 11.5),
    },
    "partial_cargo_open_sea": {
        "fill_level_range":  (0.35, 0.65),
        "speed_range":       (12.0, 17.0),
        "wave_height_range": (0.5,  4.5),
        "draft_range":       (7.0,  9.5),
    },
    "slow_steaming": {
        "fill_level_range":  (0.70, 0.95),
        "speed_range":       (5.0,  12.0),
        "wave_height_range": (0.5,  2.5),
        "draft_range":       (9.0,  11.5),
    },
    "port_approach": {
        "fill_level_range":  (0.10, 0.95),
        "speed_range":       (2.0,  8.0),
        "wave_height_range": (0.0,  1.0),
        "draft_range":       (6.0,  11.5),
    },
}

# ==========ROUTE PROFILES===========
ROUTES = {
    "middle_east":    {"T_air": (28, 42), "T_sea": (22, 32)},
    "north_atlantic": {"T_air": (2,  18), "T_sea": (5,  16)},
    "pacific":        {"T_air": (15, 28), "T_sea": (12, 26)},
    "arctic":         {"T_air": (-10, 8), "T_sea": (-2,  6)},
}


def get_h_vaporization(composition_name="standard"):
    """
    Enthalpy of vaporization for LNG mixture.

    CORRECTED: uses mole-fraction weighted average of per-component h_vap.
    Previously only used pure methane for all compositions — 
    that made lean/standard/rich differences nearly invisible (~0.001%).
    
    Rich LNG has more C2H6 and C3H8. These components have lower latent
    heat per kg than methane, meaning less energy is needed to vaporize
    the same mass → more BOG produced per unit heat ingress.
    
    This correction makes composition differences visible: ~5–10% spread
    between lean and rich, which matches industry observations.
    """
    comp = LNG_COMPOSITIONS[composition_name]

    components = {
        "CH4":  "Methane",
        "C2H6": "Ethane",
        "C3H8": "Propane",
    }

    h_vap_total = 0.0
    for symbol, coolprop_name in components.items():
        mole_frac = comp[symbol]
        try:
            H_liq = CP.PropsSI('H', 'P', 101325, 'Q', 0, coolprop_name)
            H_vap = CP.PropsSI('H', 'P', 101325, 'Q', 1, coolprop_name)
            h_vap_component = H_vap - H_liq
        except Exception:
            H_liq = CP.PropsSI('H', 'P', 101325, 'Q', 0, 'Methane')
            H_vap = CP.PropsSI('H', 'P', 101325, 'Q', 1, 'Methane')
            h_vap_component = H_vap - H_liq

        h_vap_total += mole_frac * h_vap_component

    return h_vap_total


def solar_radiation(hour_of_day):
    if 6 <= hour_of_day <= 18:
        return 900.0 * np.sin(np.pi * (hour_of_day - 6) / 12)
    return 0.0


def sloshing_factor(wave_height, fill_level):
    """
    CORRECTED: max amplification 0.35 (was 0.03).
    Reflects real 10–40% BOG increase from sloshing in extreme conditions.
    """
    if fill_level > 0.90 or fill_level < 0.10:
        fill_factor = 0.05
    elif 0.30 <= fill_level <= 0.70:
        fill_factor = 1.0
    else:
        fill_factor = 0.45
    wave_factor = min(wave_height / 4.0, 1.0)
    return 1.0 + (0.35 * fill_factor * wave_factor)


def speed_convection_factor(speed_knots):
    v_ms = speed_knots * 0.5144
    return 1.0 + 0.006 * v_ms


def draft_area_adjustment(draft_m):
    submerged_fraction = min(draft_m / DESIGN_DRAFT, 1.0)
    sides_submerged    = TANK_AREA_BASE["sides"] * submerged_fraction
    sides_exposed      = TANK_AREA_BASE["sides"] * (1 - submerged_fraction)
    return {
        "bottom":          TANK_AREA_BASE["bottom"],
        "sides_submerged": sides_submerged,
        "sides_exposed":   sides_exposed,
        "top":             TANK_AREA_BASE["top"],
    }


def calculate_bog_rate(
    T_air, T_sea, T_lng=-162.0,
    hull_condition=1.0, hour_of_day=12.0,
    wave_height=1.5, fill_level=0.95,
    speed_knots=15.0, draft_m=11.5,
    composition="standard"
):
    """
    Complete BOG rate calculation — all corrections applied.

    CORRECTED: cargo mass now scales with fill_level.
    Previously divided by full cargo mass even at 40% fill —
    that artificially suppressed BOG% at partial load.
    
    A half-empty tank still produces nearly the same absolute kg/day of BOG
    (same tank surface area, same heat ingress) but the % rises because
    there is less cargo to express it against. This is physically correct
    and consistent with how operators report BOR at partial load.
    """

    solar_W = solar_radiation(hour_of_day)
    areas   = draft_area_adjustment(draft_m)
    spd_fac = speed_convection_factor(speed_knots)

    dT_sea = (T_sea + 273.15) - (T_lng + 273.15)
    dT_air = (T_air + 273.15) - (T_lng + 273.15)

    U_bot   = U_VALUES_BASE["bottom"] * hull_condition
    U_sides = U_VALUES_BASE["sides"]  * hull_condition * spd_fac
    U_top   = U_VALUES_BASE["top"]    * hull_condition * spd_fac

    Q_bottom    = U_bot   * areas["bottom"]          * dT_sea
    Q_sides_sub = U_sides * areas["sides_submerged"] * dT_sea
    Q_sides_exp = U_sides * areas["sides_exposed"]   * dT_air
    Q_top       = (U_top  * areas["top"]             * dT_air) + \
                  (SOLAR_ABSORPTIVITY * areas["top"]  * solar_W)

    Q_total = Q_bottom + Q_sides_sub + Q_sides_exp + Q_top

    h_vap            = get_h_vaporization(composition)
    m_bog_per_second = Q_total / h_vap
    m_bog_per_day    = m_bog_per_second * 3600 * 24

    # CORRECTED: cargo mass scales with actual fill level
    # was: fixed 174_000 * 450 regardless of fill level
    actual_cargo_kg = TANK_VOLUME_M3 * fill_level * LNG_DENSITY

    bog_base  = (m_bog_per_day / actual_cargo_kg) * 100
    slosh     = sloshing_factor(wave_height, fill_level)
    bog_final = bog_base * slosh

    return bog_final


def add_measurement_noise(bog_rate, noise_level=0.008):
    """
    CORRECTED: noise_level raised from 0.003 to 0.008.
    Real sensor noise on LNG carriers is messier than lab conditions.
    Temperature sensor accuracy ±0.1°C → ~0.8% noise on BOG rate.
    """
    noise = np.random.normal(0, noise_level)
    return max(bog_rate + noise, 0.001)


def generate_dataset(n_samples=12000, random_seed=42):
    """
    Generate full synthetic BOG dataset.
    Output: data/bog_dataset.parquet — 12,000 synthetic voyage-hours.
    """

    np.random.seed(random_seed)

    scenario_names    = list(SCENARIOS.keys())
    composition_names = list(LNG_COMPOSITIONS.keys())
    route_names       = list(ROUTES.keys())

    records = []

    print(f"Generating {n_samples} synthetic voyage-hours...")

    for i in range(n_samples):
        scenario_name    = np.random.choice(scenario_names)
        composition_name = np.random.choice(composition_names)
        route_name       = np.random.choice(route_names)

        scenario = SCENARIOS[scenario_name]
        route    = ROUTES[route_name]

        fill_level   = np.random.uniform(*scenario["fill_level_range"])
        speed_knots  = np.random.uniform(*scenario["speed_range"])
        wave_height  = np.random.uniform(*scenario["wave_height_range"])
        draft_m      = np.random.uniform(*scenario["draft_range"])
        T_air        = np.random.uniform(*route["T_air"])
        T_sea        = np.random.uniform(*route["T_sea"])
        hour_of_day  = np.random.uniform(0, 24)
        hull_condition = np.random.uniform(1.0, 1.12)
        T_lng        = np.random.uniform(-163.0, -161.0)

        bog_clean = calculate_bog_rate(
            T_air=T_air, T_sea=T_sea, T_lng=T_lng,
            hull_condition=hull_condition,
            hour_of_day=hour_of_day,
            wave_height=wave_height,
            fill_level=fill_level,
            speed_knots=speed_knots,
            draft_m=draft_m,
            composition=composition_name,
        )

        bog_noisy = add_measurement_noise(bog_clean)

        # Actual cargo mass for this sample — used as PINN feature
        actual_cargo_kg = TANK_VOLUME_M3 * fill_level * LNG_DENSITY

        records.append({
            "T_air":            T_air,
            "T_sea":            T_sea,
            "T_lng":            T_lng,
            "hull_condition":   hull_condition,
            "hour_of_day":      hour_of_day,
            "wave_height":      wave_height,
            "fill_level":       fill_level,
            "speed_knots":      speed_knots,
            "draft_m":          draft_m,
            "composition":      composition_name,
            "scenario":         scenario_name,
            "route":            route_name,
            "actual_cargo_kg":  actual_cargo_kg,   # NEW: explicit for traceability
            "dT_air":           T_air - (-162.0),
            "dT_sea":           T_sea - (-162.0),
            "bog_rate_clean":   bog_clean,
            "bog_rate_noisy":   bog_noisy,
        })

        if (i + 1) % 2000 == 0:
            print(f"  {i+1}/{n_samples} samples generated...")

    df = pd.DataFrame(records)
    return df


if __name__ == "__main__":

    print("=" * 60)
    print("STAGE 5 — CORRECTED DATASET GENERATION")
    print("=" * 60)

    df = generate_dataset(n_samples=12000)

    print(f"\nDataset shape: {df.shape}")
    print(f"\nBOG rate statistics (% per day):")
    print(f"  Min:    {df['bog_rate_clean'].min():.4f}%")
    print(f"  Max:    {df['bog_rate_clean'].max():.4f}%")
    print(f"  Mean:   {df['bog_rate_clean'].mean():.4f}%")
    print(f"  Std:    {df['bog_rate_clean'].std():.4f}%")

    print(f"\nBOG rate by scenario:")
    for scenario in df['scenario'].unique():
        subset = df[df['scenario'] == scenario]['bog_rate_clean']
        print(f"  {scenario:<25}: mean={subset.mean():.4f}%  std={subset.std():.4f}%")

    print(f"\nBOG rate by composition:")
    for comp in ['lean', 'standard', 'rich']:
        subset = df[df['composition'] == comp]['bog_rate_clean']
        print(f"  {comp:<12}: mean={subset.mean():.4f}%  std={subset.std():.4f}%")

    # =========PHYSICS VALIDATION===========================
    print(f"\nPHYSICS VALIDATION:")

    all_in_range = ((df['bog_rate_clean'] > 0.05) &
                    (df['bog_rate_clean'] < 0.35)).all()
    print(f"  All BOG rates in 0.05–0.35% range: {all_in_range} — must be True")

    me_bog     = df[df['route'] == 'middle_east']['bog_rate_clean'].mean()
    arctic_bog = df[df['route'] == 'arctic']['bog_rate_clean'].mean()
    print(f"  Middle East BOG > Arctic BOG: {me_bog > arctic_bog} — must be True")

    rich_bog   = df[df['composition'] == 'rich']['bog_rate_clean'].mean()
    lean_bog   = df[df['composition'] == 'lean']['bog_rate_clean'].mean()
    comp_diff  = ((rich_bog - lean_bog) / lean_bog) * 100
    print(f"  Rich BOG > Lean BOG: {rich_bog > lean_bog} — must be True")
    print(f"  Composition spread: {comp_diff:.1f}% — expect 5–10%")

    partial = df[df['scenario'] == 'partial_cargo_open_sea']['bog_rate_clean'].mean()
    full    = df[df['scenario'] == 'full_cargo_open_sea']['bog_rate_clean'].mean()
    print(f"  Partial cargo BOG% > Full cargo BOG%: {partial > full} — must be True")
    print(f"  (Same heat ingress, less cargo = higher % — physically correct)")

    df.to_parquet("data/bog_dataset.parquet", index=False)
    print(f"\nDataset saved to: data/bog_dataset.parquet")
    print(f"Stage 5 COMPLETE. Layer 1 done. Ready for PINN.")