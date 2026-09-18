from __future__ import annotations

import streamlit as st

from components.common import page_header


# ==========================================================
# DOCUMENTATION HELPERS
# ==========================================================

def _parameter(
    name: str,
    meaning: str,
    when: str | None = None,
):
    st.markdown(f"#### {name}")

    c1, c2 = st.columns([1, 3])

    with c1:
        st.markdown(
            '<span class="doc-label">What it means</span>',
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(meaning)

    if when:
        c1, c2 = st.columns([1, 3])

        with c1:
            st.markdown(
                '<span class="doc-label">When to change</span>',
                unsafe_allow_html=True,
            )

        with c2:
            st.markdown(when)

    st.markdown(
        '<div class="doc-parameter-divider"></div>',
        unsafe_allow_html=True,
    )


def _group(title: str):
    st.markdown(
        f'<div class="doc-group-title">{title}</div>',
        unsafe_allow_html=True,
    )


# ==========================================================
# DOCUMENTATION PAGE
# ==========================================================

def render_docs_page():

    page_header(
        "Parameter Guide",
        "Explanation of every configurable parameter in the RoboAI XRF simulation.",
    )

    tab_setup, tab_tube, tab_detector, tab_physics, tab_run, tab_response = st.tabs(
        [
            "Setup",
            "X-ray tube",
            "Detector",
            "Physics",
            "Build & run",
            "Detector response",
        ]
    )

    # ======================================================
    # SETUP
    # ======================================================

    with tab_setup:

        st.header("Setup")

        # ------------------------------------------------------
        # WORLD
        # ------------------------------------------------------

        _group("WORLD")

        _parameter(
            "World material",
            "The material filling the simulation world outside the explicitly "
            "defined XRF components. For example, `G4_AIR` represents air and "
            "`G4_Galactic` represents an extremely low-density vacuum.",
            "Use `G4_AIR` when the experiment is performed in air. Use "
            "`G4_Galactic` when modelling a vacuum environment.",
        )

        _parameter(
            "World X (mm)",
            "The total size of the Geant4 world along the X axis.",
            "Increase it if any geometry extends outside the current world.",
        )

        _parameter(
            "World Y (mm)",
            "The total size of the Geant4 world along the Y axis.",
            "Increase it if any geometry extends outside the current world.",
        )

        _parameter(
            "World Z (mm)",
            "The total size of the Geant4 world along the Z axis.",
            "Increase it if any geometry extends outside the current world.",
        )

        # ------------------------------------------------------
        # CUSTOM MATERIALS
        # ------------------------------------------------------

        _group("CUSTOM MATERIALS")

        _parameter(
            "Material name",
            "The name used to identify a user-defined material inside the "
            "simulation.",
            "Create a custom material when the required material is not available "
            "as a standard Geant4 material.",
        )

        _parameter(
            "Density (g/cm³)",
            "The physical density of the custom material.",
            "Set it to the density of the material or alloy being modelled.",
        )

        _parameter(
            "Composition",
            "The elemental mass fractions of the material. The frontend uses the "
            "format `Element:fraction`, for example `Cu:0.5,W:0.5`. "
            "The fractions must add up to 1.0.",
            "Change it to represent the composition of the real alloy or material.",
        )

        # ------------------------------------------------------
        # SAMPLE
        # ------------------------------------------------------

        _group("SAMPLE")

        _parameter(
            "Sample name",
            "A descriptive name used to identify the sample in the simulation.",
        )

        _parameter(
            "Material",
            "The material assigned to the sample. It may be a Geant4 material "
            "such as `G4_Fe` or one of the custom materials defined in Setup.",
            "Change it to match the material being measured.",
        )

        _parameter(
            "Shape",
            "The geometry of the sample. The frontend currently supports "
            "`Rectangular` and `Circular` samples.",
        )

        _parameter(
            "Width (mm)",
            "The X-direction size of a rectangular sample.",
            "Used only when the sample shape is Rectangular.",
        )

        _parameter(
            "Height (mm)",
            "The Y-direction size of a rectangular sample.",
            "Used only when the sample shape is Rectangular.",
        )

        _parameter(
            "Radius (mm)",
            "The radius of a circular sample.",
            "Used only when the sample shape is Circular.",
        )

        _parameter(
            "Thickness (mm)",
            "The physical thickness of the sample through which photons and "
            "secondary radiation can interact.",
            "Set it to the actual sample thickness. Thickness can affect both "
            "X-ray production and self-absorption.",
        )

    # ======================================================
    # X-RAY TUBE
    # ======================================================

    with tab_tube:

        st.header("X-ray tube")

        _group("TUBE")

        _parameter(
            "Tube name",
            "A descriptive identifier for the X-ray tube object.",
        )

        _parameter(
            "Voltage (kV)",
            "The accelerating voltage of the X-ray tube. It controls the maximum "
            "energy available in the generated X-ray spectrum.",
            "Set it to the operating voltage of the real XRF instrument.",
        )

        _parameter(
            "Current (mA)",
            "The electrical current driving the X-ray tube. It controls the "
            "photon production rate used when scaling the simulation.",
            "Set it to the current used by the real instrument.",
        )

        _parameter(
            "Anode",
            "The element used as the X-ray tube target, for example W, Rh, Ag, "
            "Mo, Cu, or Cr. It determines the characteristic lines emitted by "
            "the tube.",
            "Set it to the target material of the physical X-ray tube.",
        )

        _parameter(
            "Anode angle (deg)",
            "The angle of the target surface inside a reflection-type X-ray tube.",
            "Set it according to the tube manufacturer's geometry.",
        )

        _parameter(
            "Focal spot diameter (mm)",
            "The diameter of the region from which primary X-rays are generated.",
            "Use the focal-spot specification of the real tube. A smaller focal "
            "spot represents a more localized source.",
        )

        _parameter(
            "Focal spot → sample (mm)",
            "Distance from the X-ray focal spot to the sample reference point.",
            "Set it to the source-to-sample distance of the instrument.",
        )

        _parameter(
            "Window → sample (mm)",
            "Distance from the X-ray tube window to the sample.",
            "Set it from the physical tube and instrument geometry.",
        )

        _parameter(
            "Window → virtual collimator (mm)",
            "Distance from the tube window to the virtual source collimator used "
            "to restrict the primary X-ray beam.",
            "Change it when reproducing the source collimation geometry of a "
            "specific instrument.",
        )

        _parameter(
            "Virtual collimator radius (mm)",
            "Radius of the virtual aperture used to restrict the primary beam "
            "direction.",
            "Use a smaller radius for a narrower beam and a larger radius for a "
            "wider beam.",
        )

        _parameter(
            "Elevation (deg)",
            "The elevation angle used to position the tube relative to the sample.",
            "Set it to reproduce the source orientation of the real instrument.",
        )

        _parameter(
            "Azimuth (deg)",
            "The rotation of the X-ray tube around the sample reference axis.",
            "Set it to reproduce the source position around the sample.",
        )

        _parameter(
            "Tube type",
            "Specifies whether the X-ray tube operates using reflection or "
            "transmission target geometry.",
            "Choose the type corresponding to the physical X-ray tube.",
        )

        _parameter(
            "Target thickness (µm)",
            "Thickness of the X-ray tube target used when a finite target "
            "thickness is required by the selected tube model.",
            "Set it according to the target construction of the tube.",
        )

        # ------------------------------------------------------
        # TUBE WINDOW
        # ------------------------------------------------------

        _group("TUBE WINDOW")

        _parameter(
            "Window name",
            "Identifier for the X-ray tube window.",
        )

        _parameter(
            "Window material",
            "Material separating the inside of the tube from the external "
            "environment. Beryllium (`G4_Be`) is commonly used for X-ray windows.",
            "Set it to the window material specified for the real tube.",
        )

        _parameter(
            "Window thickness (mm)",
            "Physical thickness of the tube window. Low-energy X-rays may be "
            "strongly attenuated by this layer.",
            "Use the actual tube-window thickness when known.",
        )

        # ------------------------------------------------------
        # SPEKPY FILTERS
        # ------------------------------------------------------

        _group("SPEKPY FILTERS")

        _parameter(
            "Element",
            "Element used as a filter in the SpekPy source-spectrum calculation.",
            "Add filters that are physically present in the tube or instrument "
            "and are already intended to be included in source-spectrum generation.",
        )

        _parameter(
            "Thickness (mm)",
            "Thickness of the corresponding SpekPy filter.",
            "Use the real filter thickness.",
        )

        # ------------------------------------------------------
        # GEANT4 TUBE FILTERS
        # ------------------------------------------------------

        _group("GEANT4 TUBE FILTERS")

        _parameter(
            "Enabled",
            "Controls whether the physical filter is included in the Geant4 "
            "geometry.",
        )

        _parameter(
            "Name",
            "Identifier for the physical tube filter.",
        )

        _parameter(
            "Shape",
            "Geometry of the filter: Circular or Rectangular.",
        )

        _parameter(
            "Material",
            "Physical material through which photons are transported.",
        )

        _parameter(
            "Radius (mm)",
            "Radius of a circular filter.",
            "Used only for Circular filters.",
        )

        _parameter(
            "Width / Height (mm)",
            "Dimensions of a rectangular filter.",
            "Used only for Rectangular filters.",
        )

        _parameter(
            "Thickness (mm)",
            "Thickness of the physical filter along the beam direction.",
        )

        _parameter(
            "Distance from window (mm)",
            "Distance between the tube window and the physical filter.",
            "Use it to reproduce the real order and spacing of filters.",
        )

    # ======================================================
    # DETECTOR
    # ======================================================

    with tab_detector:

        st.header("Detector")

        _group("ACTIVE DETECTOR")

        _parameter(
            "Detector name",
            "Identifier for the active detector volume.",
        )

        _parameter(
            "Detector material",
            "Material of the active detector volume. For an SDD this is normally "
            "silicon, represented by `G4_Si`.",
        )

        _parameter(
            "Shape",
            "Geometry of the active detector volume: Circular or Rectangular.",
        )

        _parameter(
            "Radius (mm)",
            "Radius of the active detector area for a circular detector.",
        )

        _parameter(
            "Width / Height (mm)",
            "Dimensions of the active area for a rectangular detector.",
        )

        _parameter(
            "Thickness (mm)",
            "Thickness of the active detector volume. It influences the "
            "probability that an incoming photon deposits energy in the detector.",
        )

        _parameter(
            "Sample → detector (mm)",
            "Distance from the sample reference point to the detector.",
            "Set it to the sample-to-detector distance of the real instrument.",
        )

        _parameter(
            "Elevation (deg)",
            "Elevation angle of the detector relative to the sample.",
        )

        _parameter(
            "Azimuth (deg)",
            "Angular position of the detector around the sample.",
        )

        # ------------------------------------------------------
        # HOUSING
        # ------------------------------------------------------

        _group("DETECTOR HOUSING")

        _parameter(
            "Enable detector housing",
            "Controls whether the detector housing is included in the Geant4 "
            "geometry.",
        )

        _parameter(
            "Housing name",
            "Identifier for the detector housing.",
        )

        _parameter(
            "Aperture shape",
            "Shape of the opening through which X-rays enter the detector housing.",
        )

        _parameter(
            "Aperture radius (mm)",
            "Radius of the housing opening when a Circular aperture is selected.",
        )

        _parameter(
            "Aperture width / height (mm)",
            "Dimensions of the opening when a Rectangular aperture is selected.",
        )

        _parameter(
            "Detector clearance (mm)",
            "Gap between the active detector and surrounding housing geometry.",
            "Set it according to the mechanical construction of the detector.",
        )

        _parameter(
            "Housing wall (mm)",
            "Thickness of the outer detector housing wall.",
        )

        _parameter(
            "Cavity wall (mm)",
            "Thickness of the internal cavity wall around the detector.",
        )

        _parameter(
            "Housing material",
            "Material used for the outer detector housing.",
        )

        _parameter(
            "Cavity wall material",
            "Material used for the internal cavity wall.",
        )

        _parameter(
            "Inner cavity medium",
            "Material or medium filling the empty space inside the housing around "
            "the active detector.",
            "Use air for an air-filled cavity or `G4_Galactic` when modelling "
            "vacuum.",
        )

        _parameter(
            "Housing window material",
            "Material of the entrance window in front of the detector.",
        )

        _parameter(
            "Housing window thickness (mm)",
            "Thickness of the detector entrance window. It is especially "
            "important for low-energy X-rays because attenuation increases "
            "strongly at low energies.",
        )

        # ------------------------------------------------------
        # INTERNAL MASKS
        # ------------------------------------------------------

        _group("INTERNAL MASKS")

        _parameter(
            "Name",
            "Identifier for an internal detector mask.",
        )

        _parameter(
            "Aperture",
            "Shape of the open region in the mask.",
        )

        _parameter(
            "Material",
            "Material from which the mask is constructed.",
        )

        _parameter(
            "Aperture radius",
            "Radius of the open central region for a Circular mask.",
        )

        _parameter(
            "Outer radius",
            "Outer radius of a Circular mask.",
        )

        _parameter(
            "Aperture width / height",
            "Size of the opening for a Rectangular mask.",
        )

        _parameter(
            "Outer width / height",
            "Overall dimensions of a Rectangular mask.",
        )

        _parameter(
            "Length (mm)",
            "Thickness of the mask along the direction toward the detector.",
        )

        _parameter(
            "Distance (mm)",
            "Distance of the mask in front of the detector.",
            "Use it to reproduce the ordering and spacing of layers inside the "
            "detector assembly.",
        )

        # ------------------------------------------------------
        # DETECTOR FILTERS
        # ------------------------------------------------------

        _group("DETECTOR FILTERS")

        _parameter(
            "Enabled",
            "Controls whether the detector filter is included.",
        )

        _parameter(
            "Name",
            "Identifier for the detector filter.",
        )

        _parameter(
            "Shape",
            "Circular or Rectangular physical filter geometry.",
        )

        _parameter(
            "Material",
            "Material used for the filter.",
        )

        _parameter(
            "Radius / Width / Height",
            "Physical size of the filter. Radius is used for Circular filters; "
            "width and height are used for Rectangular filters.",
        )

        _parameter(
            "Thickness (mm)",
            "Thickness through which photons must travel.",
        )

        _parameter(
            "Distance (mm)",
            "Distance of the filter in front of the detector.",
        )

        # ------------------------------------------------------
        # COLLIMATORS
        # ------------------------------------------------------

        _group("DETECTOR COLLIMATORS")

        _parameter(
            "Enabled",
            "Controls whether the detector collimator is present.",
        )

        _parameter(
            "Name",
            "Identifier for the collimator.",
        )

        _parameter(
            "Aperture",
            "Shape of the opening through which photons can reach the detector.",
        )

        _parameter(
            "Material",
            "Material used to absorb photons outside the accepted aperture.",
        )

        _parameter(
            "Aperture radius / width / height",
            "Dimensions of the open region of the collimator.",
        )

        _parameter(
            "Outer radius / width / height",
            "External dimensions of the collimator body.",
        )

        _parameter(
            "Length (mm)",
            "Depth of the collimator along the photon travel direction.",
        )

        _parameter(
            "Distance (mm)",
            "Distance between the collimator and the detector.",
        )

    # ======================================================
    # PHYSICS
    # ======================================================

    with tab_physics:

        st.header("Physics")

        _group("PHYSICS ENGINE")

        _parameter(
            "Interaction biasing",
            "Enables variance-reduction biasing for selected photon interactions. "
            "The purpose is to obtain useful XRF statistics with fewer simulated "
            "primary events.",
            "Normally enable it for large quantitative XRF simulations. Disable "
            "it when comparing directly against an unbiased transport run.",
        )

        _parameter(
            "Secondary splitting",
            "Creates multiple statistically weighted secondary histories from "
            "selected interactions to improve detector statistics.",
            "Enable it when fluorescence photons reaching the detector are rare.",
        )

        _parameter(
            "Fluorescence",
            "Enables atomic fluorescence following creation of an atomic-shell "
            "vacancy.",
            "Normally keep this enabled for XRF simulations.",
        )

        _parameter(
            "Auger",
            "Enables Auger-electron emission during atomic relaxation.",
            "Enable it when Auger electrons or their secondary effects are relevant.",
        )

        _parameter(
            "PIXE",
            "Enables particle-induced X-ray emission processes.",
            "Enable it when charged particles are expected to produce relevant "
            "atomic vacancies.",
        )

        _parameter(
            "Ignore cuts",
            "Allows atomic de-excitation products to be generated without being "
            "suppressed by the normal production-cut treatment.",
            "For XRF work this is commonly useful when low-energy fluorescence "
            "photons must be retained.",
        )

        _parameter(
            "Fluorescence dataset",
            "Selects the atomic fluorescence transition dataset used by the "
            "simulation. Your frontend currently provides ANSTO, Bearden, "
            "XDB_EADL and ROBOAI options.",
            "Change it when comparing the effect of different atomic-data sources.",
        )

        _parameter(
            "Maximum energy",
            "Upper energy setting passed to the physics configuration.",
            "Normally leave it above the energy range required by the X-ray source "
            "and simulation.",
        )

        _parameter(
            "Photoelectric factor",
            "Biasing factor applied to photoelectric interactions when interaction "
            "biasing is enabled.",
            "Larger factors can increase sampling of photoelectric interactions "
            "but also change statistical weights.",
        )

        _parameter(
            "Compton factor",
            "Biasing factor applied to Compton scattering.",
        )

        _parameter(
            "Rayleigh factor",
            "Biasing factor applied to Rayleigh scattering.",
        )

        _parameter(
            "Electron cut",
            "Geant4 production-cut setting for electrons.",
            "Lower values allow finer secondary production but can increase "
            "simulation time.",
        )

        _parameter(
            "Gamma cut",
            "Geant4 production-cut setting for photons.",
            "Lower values allow lower-range secondary photon production at the "
            "cost of additional computation.",
        )

        _parameter(
            "Positron cut",
            "Geant4 production-cut setting for positrons.",
        )

        _parameter(
            "Proton cut",
            "Geant4 production-cut setting for protons.",
        )

    # ======================================================
    # BUILD & RUN
    # ======================================================

    with tab_run:

        st.header("Build & run")

        _group("RUN SETTINGS")

        _parameter(
            "Run name",
            "Name of the simulation run. It is also used to create the output "
            "directory under `runs/`.",
            "Use a unique descriptive name when you want to preserve multiple runs.",
        )

        _parameter(
            "Threads",
            "Number of CPU worker threads used by the Geant4 simulation.",
            "Increase it on machines with more available CPU cores. Avoid using "
            "more threads than the system can efficiently support.",
        )

        _parameter(
            "Beam-on events",
            "Number of primary source histories simulated in the quantitative "
            "Geant4 run.",
            "Increase it to reduce Monte Carlo statistical uncertainty. More "
            "events require more computation time.",
        )

        _parameter(
            "Print progress every",
            "Controls how frequently Geant4 prints progress information.",
            "Increase the value for long simulations to reduce console output.",
        )

        _parameter(
            "Visualization events",
            "Number of events generated when opening the 3D visualization.",
            "Keep this much smaller than a quantitative run because visualization "
            "is intended for checking geometry and tracks.",
        )

        _parameter(
            "Visualization threads",
            "Number of threads used by the visualization run.",
            "A small value is usually sufficient because visualization is not "
            "used for quantitative statistics.",
        )

    # ======================================================
    # DETECTOR RESPONSE
    # ======================================================

    with tab_response:

        st.header("Detector response")

        _group("ACQUISITION AND ELECTRONICS")

        _parameter(
            "Current (mA)",
            "Tube current used when scaling the Monte Carlo yield to the expected "
            "number of incident photons in a physical acquisition.",
            "Normally set it to the current used by the instrument for the "
            "measurement being reproduced.",
        )

        _parameter(
            "Live time (s)",
            "Effective detector acquisition time.",
            "Set it to the live time of the real XRF measurement.",
        )

        _parameter(
            "FWHM (eV)",
            "Detector energy resolution expressed as full width at half maximum "
            "at the specified reference energy.",
            "Use the detector manufacturer's specification or a measured "
            "calibration value.",
        )

        _parameter(
            "FWHM reference energy (keV)",
            "Energy at which the specified FWHM value is defined. A common SDD "
            "specification is given near the Mn Kα energy around 5.9 keV.",
        )

        _parameter(
            "Pile-up window (µs)",
            "Time interval within which closely arriving detector pulses may be "
            "combined as pile-up.",
            "Set it according to the pulse-pair resolution or processing time of "
            "the detector electronics.",
        )

        _parameter(
            "Gain (keV/channel)",
            "Energy represented by one MCA channel.",
            "Set it to match the energy calibration of the real spectrum.",
        )

        _parameter(
            "Zero offset (keV)",
            "Energy-axis offset applied to the MCA spectrum.",
            "Adjust it when the calibrated energy axis does not begin exactly at "
            "0 keV.",
        )

        _parameter(
            "Fano factor",
            "Statistical factor describing fluctuations in the number of "
            "electron-hole pairs generated by deposited energy in the detector.",
            "Change it only when modelling a detector material or response with a "
            "different known Fano factor.",
        )

        _parameter(
            "Pair creation energy (eV)",
            "Average energy required to generate one electron-hole pair in the "
            "detector material. Silicon is commonly modelled at approximately "
            "3.6 eV per pair.",
            "Change it when using a different detector material.",
        )

        _group("ADVANCED DETECTOR RESPONSE")

        _parameter(
            "MCA channels",
            "Number of channels in the generated multichannel-analyzer spectrum.",
            "Set it to match the channel count of the target instrument.",
        )

        _parameter(
            "Chunk size",
            "Number of simulation entries processed at one time during detector "
            "response calculations.",
            "Reduce it if memory usage is too high. Increase it when sufficient "
            "memory is available and larger batches improve processing speed.",
        )

        _parameter(
            "Number of buckets",
            "Internal subdivision used by the detector-response processing "
            "pipeline.",
            "Normally leave this at the validated default unless tuning the "
            "post-processing implementation.",
        )