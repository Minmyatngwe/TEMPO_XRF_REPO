import streamlit as st 
import spekpy as sp
import pandas as pd 
import matplotlib.pyplot as plt 
import os 
import subprocess
from pathlib import Path
from helper.macrowriter import write_macro
from helper.xray_tube import get_flu
PROJECT_ROOT = Path(__file__).resolve().parents[3]
BUILD_DIR = PROJECT_ROOT / "build"
SIM_EXE = BUILD_DIR / "sim"
MACRO_FILE_VIS = BUILD_DIR / "vis.mac"
MACRO_FILE_RUN = BUILD_DIR / "run.mac"

ROOT_OUTPUT_DIR=Path(__file__).resolve().parents[2]/"root_output_file"


st.subheader("Tube parameter")
current=st.number_input("Current (MAs)",format="%.5f")
voltage=st.number_input("Tube Voltage")

anode_degree=st.number_input("Anode Angle degree")
exposure_time=st.number_input("Exposire time (s)")

anode_target_material=st.selectbox(
    "Select Anode Material",
 [
    ("W", "Tungsten"),
    ("Mo", "Molybdenum"),
    ("Rh", "Rhodium"),
    ("Cr", "Chromium"),
    ("Cu", "Copper"),
    ("Ag", "Silver"),
    ("Au", "Gold"),
 ]
)
df = pd.DataFrame(
    [
        {"filter": "", "thickness (mm)": 0.0}
    ]
)

edited_df = st.data_editor(
    df,
    num_rows="dynamic"
)

st.subheader("General paramter")
world_material=st.text_input("World Material")
sample_custom_or_not=st.toggle("IS material custom?")
sample_density=st.number_input("input sample density (gcm**3)")
source_to_sample=st.number_input("source To sample Distancte (mm)")
incident_angle=st.number_input("Source Incident Angle(deg)")
takeoff_angle=st.number_input("Detector take off angle(deg)")

detector_active_area=st.number_input("Detector active area(mm)")
detector_thickness=st.number_input("Detector thickness(mm)")
detector_to_sample_distance=st.number_input("Detector to sample distance(mm)")
source_to_tube_collimatory=st.number_input("Source to tube collimatory distance(mm)")
tube_collimatory_radius=st.number_input("Tube collimatory radius(mm)",format="%.5f")

focal_spot_diameter=st.number_input("Focal spot diameter(mm)",format="%.5f")

# detector collimatory configuration
detector_collimatory_is_enable=st.toggle("Is detector collimatory not activate")

detector_collimatory_composition_is_custom=st.toggle("Is detector collimatory mat is custom")
detector_collimatory_material=st.text_input("Detector collimatory mat")

sample_detector_collimatory_dsitance=st.number_input("Sample to detector collimatory distance (mm)")
sample_detector_collimatory_angle=st.number_input("Sample to Detector Collimatory deg(deg)")
sample_detector_collimatory_density=st.number_input("Detector collimatory density(g/cm**3)")
detector_collimatory_thickness=st.number_input("Detector collimatory Thickness(mm)")
detector_collimatory_outer_radius=st.number_input("Detector collimatory Outer Tube Radius(mm)")
detector_collimatory_inner_radius=st.number_input("Detector collimatory inner Tube Radius(mm)")



if sample_custom_or_not:
    sampleMaterialIsCustom="true"
else:
    sampleMaterialIsCustom="false"
if current and voltage and anode_degree and anode_target_material:
    if st.button("Generate tube spectrum distribution "):
        energy_bins, fluence_list = get_flu(current=current,voltage=voltage,anode_degree=anode_degree,exposure_time=exposure_time,anode_target_material=anode_target_material,filter=edited_df,source_to_tube_collimatory=source_to_tube_collimatory)
        fig,ax=plt.subplots()
        ax.plot(energy_bins,fluence_list)
        ax.set_xlabel("Tube Energy")
        ax.set_ylabel("Intensity")
        ax.set_title(f"""
                     
                     v {voltage},c {current},
                     anode deg and mat{anode_degree},{anode_target_material[1]}
                     filter{edited_df}
                     
                     """)
        
        st.pyplot(fig)


output_file=st.text_input("output root file name")

numberofthread=st.number_input("Number Of thread")
beamon=st.number_input("BeamOn")
ROOT_OUTPUT_DIR=ROOT_OUTPUT_DIR/f"{output_file}.root"

view_macro=write_macro(
    incident_angle=incident_angle,
    source_to_sample=source_to_sample,
    detector_thickness=detector_thickness,
    detector_active_area=detector_active_area,
    detector_to_sample_distance=detector_to_sample_distance,
    takeoff_angle=takeoff_angle,
    beamon=beamon,
    numberofthread=int(numberofthread),
    filepath=ROOT_OUTPUT_DIR,
    isvirtual=True,
    world_material=world_material,sample_density=sample_density,sampleMaterialIsCustom=sampleMaterialIsCustom,
    focal_spot_diameter=focal_spot_diameter,
    detector_collimatory_is_enable=detector_collimatory_is_enable,
    detector_collimatory_composition_is_custom=detector_collimatory_composition_is_custom,
    sample_detector_collimatory_dsitance=sample_detector_collimatory_dsitance,
    detector_collimatory_material=detector_collimatory_material,
    sample_detector_collimatory_angle=sample_detector_collimatory_angle,
    sample_detector_collimatory_density=sample_detector_collimatory_density,
    detector_collimatory_thickness=detector_collimatory_thickness,
    detector_collimatory_outer_radius=detector_collimatory_outer_radius,
    detector_collimatory_inner_radius=detector_collimatory_inner_radius
    
    
    
    
)
if st.button("show geo in geant4"):
    with open(MACRO_FILE_VIS,"w") as f:
        f.write(view_macro)
    subprocess.run([str(SIM_EXE),], cwd=str(BUILD_DIR), check=True)

if st.button("start shooting"):
    energy_bins, fluence_list = get_flu(current=current,voltage=voltage,anode_degree=anode_degree,exposure_time=exposure_time,anode_target_material=anode_target_material,filter=edited_df,source_to_tube_collimatory=source_to_tube_collimatory)
    energy_bins/=1000
    run_macro=write_macro(
    incident_angle=incident_angle,
    source_to_sample=source_to_sample,
    detector_thickness=detector_thickness,
    detector_active_area=detector_active_area,
    detector_to_sample_distance=detector_to_sample_distance,
    takeoff_angle=takeoff_angle,
    beamon=int(beamon),
    numberofthread=int(numberofthread),
    filepath=ROOT_OUTPUT_DIR,
    isvirtual=False,
    world_material=world_material,sample_density=sample_density,sampleMaterialIsCustom=sampleMaterialIsCustom,
    focal_spot_diameter=focal_spot_diameter,
    detector_collimatory_is_enable=detector_collimatory_is_enable,
    detector_collimatory_composition_is_custom=detector_collimatory_composition_is_custom,
    sample_detector_collimatory_dsitance=sample_detector_collimatory_dsitance,
    detector_collimatory_material=detector_collimatory_material,
    sample_detector_collimatory_angle=sample_detector_collimatory_angle,
    sample_detector_collimatory_density=sample_detector_collimatory_density,
    detector_collimatory_thickness=detector_collimatory_thickness,
    detector_collimatory_outer_radius=detector_collimatory_outer_radius,
    detector_collimatory_inner_radius=detector_collimatory_inner_radius,
    energy_bins=energy_bins,
    
    fluence_list=fluence_list
    
    
    
)
    print(run_macro)
    with open(MACRO_FILE_RUN,"w") as f:
        f.write(run_macro)
    subprocess.run([str(SIM_EXE),"run.mac"], cwd=str(BUILD_DIR), check=True)





        

