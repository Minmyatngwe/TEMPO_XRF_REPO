import streamlit as st
import spekpy as sp


st.image(
    "views/images/xraytubepng.png",
    caption="X-ray tube components",
    width="stretch",
)

st.subheader("X-ray Tube Parameters")


current = st.number_input(
    "Current (mA)",
    min_value=0.0,
    step=0.1,
    key="xray_current_ma",
    format="%.6f"
)

voltage = st.number_input(
    "Tube voltage (kV)",
    min_value=1.0,
    step=1.0,
    key="xray_voltage_kv",
)


anode_angle_degree = st.number_input(
    "Anode angle (°)",
    min_value=0.0,
    step=1.0,
    key="xray_anode_angle_deg",
)


ANODE_MATERIALS = {
    "Tungsten (W)": "W",
    "Chromium (Cr)": "Cr",
    "Copper (Cu)": "Cu",
    "Molybdenum (Mo)": "Mo",
    "Rhodium (Rh)": "Rh",
    "Silver (Ag)": "Ag",
    "Gold (Au)": "Au",
}


st.caption(
    "See the [SpekPy documentation](https://pypi.org/project/spekpy/) "
    "for supported materials and spectrum calculations."
)

selected_anode = st.selectbox(
    "Anode target material",
    options=list(ANODE_MATERIALS.keys()),
    key="xray_selected_anode",
)

anode_symbol = ANODE_MATERIALS[selected_anode]



focal_spot = st.number_input(
    "Focal spot diameter (mm)",
    min_value=0.0,
    step=0.0001,
    format="%.8f",
    key="xray_focal_spot_mm",
)

sample_to_focal_spot=st.number_input(
    "Sample to focal spot  distance(mm)",
    min_value=0.0,
    step=0.00000001,
    format="%.8f",
    key="xray_sample_to_focal_spot_mm"
)

xraytube_window_mat = st.text_input(
    "X-ray tube window material",
    key="xray_window_material",
    value="G4_Be"
).strip()

xraytube_window_thickness = st.number_input(
    "Window thickness (mm)",
    min_value=0.0,
    step=0.001,
    format="%.6f",
    key="xray_window_thickness_mm",
)
current_xray_tube_config = {
    "current_ma": float(current),
    "voltage_kv": float(voltage),
    "anode_angle_deg": float(anode_angle_degree),
    "anode_symbol": anode_symbol,
    "focal_spot_mm": float(focal_spot),
    "window": {
        "material": xraytube_window_mat,
        "thickness_mm": float(xraytube_window_thickness),
    },
    "sample_to_focal_spot_mm":sample_to_focal_spot,
}


xray_tube_inputs_valid = all(
    [
        current > 0,
        voltage > 0,
        anode_angle_degree > 0,
        bool(anode_symbol),
        focal_spot > 0,
        bool(xraytube_window_mat),
        xraytube_window_thickness > 0,
        sample_to_focal_spot>0,
    ]
)

current_xray_tube_config["is_valid"] = xray_tube_inputs_valid


saved_xray_config = st.session_state.get(
    "xray_tube_config"
)

st.session_state["xray_tube_ready"] = bool(
    xray_tube_inputs_valid
    and saved_xray_config == current_xray_tube_config
)


if xray_tube_inputs_valid:

    if st.button(
        "Save parameters",
        type="primary",
        width="stretch",
        key="save_xray_tube_parameters",
    ):
        st.session_state["xray_tube_config"] = (
            current_xray_tube_config
        )

        st.session_state["xray_tube_ready"] = True

        st.session_state.current = current
        st.session_state.voltage = voltage
        st.session_state.anode_angle_degree = (
            anode_angle_degree
        )
        st.session_state.anode_symbol = anode_symbol
        st.session_state.xraytube_window_mat = (
            xraytube_window_mat
        )
        st.session_state.xraytube_window_thickness = (
            xraytube_window_thickness
        )
        st.session_state.focal_spot = focal_spot
        
        st.session_state.sample_to_focal_spot=sample_to_focal_spot

        st.success("X-ray tube parameters saved successfully.")

else:
    st.info(
        "Complete all required X-ray tube parameters "
        "to enable the Save button."
    )


if st.session_state.get("xray_tube_ready", False):
    st.success("X-ray tube configuration is ready.")