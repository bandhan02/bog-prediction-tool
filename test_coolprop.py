import CoolProp.CoolProp as CP

# Saturation temperature of pure methane at atmospheric pressure
# Expected result: approximately 111.7 K (-161.5°C)
# This is the boiling point of LNG at 1 atm — a number every LNG engineer knows

T_sat = CP.PropsSI('T', 'P', 101325, 'Q', 0, 'Methane')
print(f"Methane saturation temperature at 1 atm: {T_sat:.2f} K ({T_sat - 273.15:.2f} °C)")

# Also get enthalpy of vaporization — you'll need this for BOG rate calculation
H_liq = CP.PropsSI('H', 'P', 101325, 'Q', 0, 'Methane')  # liquid
H_vap = CP.PropsSI('H', 'P', 101325, 'Q', 1, 'Methane')  # vapour
h_vap = H_vap - H_liq
print(f"Enthalpy of vaporization: {h_vap/1000:.2f} kJ/kg")
