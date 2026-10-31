import math

# ---- Constants ----
F = 96485
n = 2
D_25C = 7.0e-6
M_Cu = 63.546
M_CuSO4_5H2O = 249.68
Cp_water = 4186
density_solution = 1.15
density_copper = 8.96  # g/cm3
viscosity_water = 0.01  # g/(cm·s)
conductivity_base = 0.08

def copper_calc_v11():

    print("\n" + "="*100)
    print("🧪 COPPER ELECTRODEPOSITION ANALYZER V11 — NANO INSTABILITY ENGINE")
    print("="*100)

    try:
        current = float(input("\n1. Average Current (A): "))
        voltage = float(input("2. Applied Voltage (V): "))
        hours = float(input("3. Run Time (hours): "))

        width = float(input("\n4. Plate Width (cm): "))
        height = float(input("5. Plate Height (cm): "))
        sides = int(input("6. Active Sides (1 or 2): "))
        sub = float(input("7. Submersion %: "))
        spacing = float(input("8. Spacing (cm): "))

        cuso4_g = float(input("\n9. Initial CuSO4·5H2O grams: "))
        volume_L = float(input("10. Volume (L): "))
        acid_ml_37 = float(input("11. 37% Battery Acid (mL): "))
        temp_C = float(input("12. Starting Temp (°C): "))

        print("\nHydrodynamics: 1=Static 2=Natural 3=Mild 4=Strong")
        mode = int(input("Select mode: "))

        nano_mode = input("Activate Nano Mode (<1 µm)? (y/n): ")
        copper_anode = input("Using Copper Anode? (y/n): ")
        psu_voltage_limit = float(input("PSU Max Voltage (V): "))

    except:
        print("Invalid input.")
        return

    total_seconds = hours * 3600

    # ---- Area ----
    area = width * height * sides * (sub/100)
    perimeter = 2*(width+height)
    edge_factor = 1 + (0.15*(perimeter/(width*height)))
    eff_area = area * edge_factor
    current_density = (current*1000)/eff_area

    # ---- Chemistry ----
    cuso4_gL = cuso4_g/volume_L
    Cu_mol_L = cuso4_gL/M_CuSO4_5H2O
    Cu_mol_cm3 = Cu_mol_L/1000

    pure_H2SO4_g = acid_ml_37 * 1.28 * 0.37
    acid_gL = pure_H2SO4_g/volume_L

    # ---- Conductivity ----
    conductivity = conductivity_base + (acid_gL * 0.002)
    conductivity *= (1 + (temp_C-25)*0.02)

    cell_resistance = spacing/(conductivity * eff_area)
    max_possible_current = psu_voltage_limit / cell_resistance

    clipping = False
    if current > max_possible_current:
        clipping = True
        current = max_possible_current

    # ---- Diffusion Limit ----
    D = D_25C*((temp_C+273.15)/298.15)
    delta_lookup = {1:0.05,2:0.035,3:0.02,4:0.01}
    delta = delta_lookup.get(mode,0.05)

    i_lim = (n*F*D*Cu_mol_cm3)/delta
    i_lim_mA = i_lim*1000
    ratio = current_density/i_lim_mA

    # ---- Hydrogen ----
    if ratio < 1:
        H_frac = 0.05*ratio
    else:
        H_frac = min(0.05 + (ratio-1)*0.5, 0.9)

    efficiency = 1 - H_frac

    # ---- Particle Size Estimate ----
    if current_density < 30:
        particle_um = 40
    elif current_density < 60:
        particle_um = 10
    elif current_density < 90:
        particle_um = 3
    else:
        particle_um = 0.8

    # ---- Settling Time (Stokes Law) ----
    r_cm = (particle_um*1e-4)/2
    settling_velocity = (2/9)*(density_copper-density_solution)*980*(r_cm**2)/viscosity_water
    settling_time = 10/settling_velocity if settling_velocity>0 else 0  # 10 cm fall

    # ---- Surface Area of Powder ----
    grams_per_sec = (current*M_Cu)/(n*F) * efficiency
    copper_mass = grams_per_sec*total_seconds
    volume_cu = copper_mass/density_copper
    particle_volume = (4/3)*math.pi*(r_cm**3)
    particle_count = volume_cu/particle_volume if particle_volume>0 else 0
    particle_area = 4*math.pi*(r_cm**2)
    total_surface_area = particle_count*particle_area

    # ---- Thermal ----
    power = current*voltage
    heat = power*total_seconds
    mass_solution = volume_L*density_solution
    delta_T = heat/(mass_solution*Cp_water)
    final_temp = temp_C+delta_T

    thermal_warning = ""
    if delta_T > 15:
        thermal_warning = "⚠ Risk of thermal runaway"

    # ---- Acid Optimization ----
    optimal_acid_ml = (150/2)*(volume_L)  # scaled from 150 ml per 2L
    acid_suggestion = ""
    if acid_ml_37 < optimal_acid_ml*0.8:
        acid_suggestion = "Increase acid for ultrafine regime"
    elif acid_ml_37 > optimal_acid_ml*1.5:
        acid_suggestion = "Acid high — may cause clumping"

    # ---- Instability Detection ----
    instability = "Stable"
    if ratio > 1.3 and current_density > 70:
        instability = "⚡ Instability Zone (Ultrafine Likely)"
    elif ratio > 1:
        instability = "Hydrogen Turbulent Zone"

    # ---- Output ----
    print("\n"+"-"*100)
    print("Effective Area:",round(eff_area,1),"cm²")
    print("Current Density:",round(current_density,1),"mA/cm²")
    print("Limiting Current Density:",round(i_lim_mA,1),"mA/cm²")
    print("Applied/Limiting Ratio:",round(ratio,2))
    print("Instability State:",instability)

    print("\nPredicted Particle Size:",particle_um,"µm")
    print("Settling Time (10cm fall):",round(settling_time/60,2),"minutes")

    print("\nTotal Surface Area Produced:",round(total_surface_area/10000,2),"m²")

    print("\nCell Resistance:",round(cell_resistance,3),"Ω")
    print("Max Possible Current:",round(max_possible_current,2),"A")
    if clipping:
        print("⚠ PSU CLIPPING OCCURRED")

    print("\nHydrogen Fraction:",round(H_frac*100,1),"%")
    print("Efficiency:",round(efficiency*100,1),"%")

    print("\nCopper Produced:",round(copper_mass,2),"g")

    print("\nTemp Rise:",round(delta_T,2),"°C")
    print("Final Temp:",round(final_temp,2),"°C")
    if thermal_warning:
        print(thermal_warning)

    print("\nAcid Optimization:",acid_suggestion)

    if nano_mode.lower()=="y":
        target_density = 90
        optimal_current = (target_density*eff_area)/1000
        print("\nNano Mode Target Current:",round(optimal_current,2),"A")
        print("Reduce spacing to 3–4 cm for true <1 µm regime")

    print("\n"+"="*100)


if __name__=="__main__":
    copper_calc_v11()
