import streamlit as st


PHYSICS_DEFAULTS = {
    "physics_fluorescence": True,
    "physics_auger": False,
    "physics_pixe": False,
    "physics_ignore_deexcitation_cut": True,

    "physics_secondary_splitting_on": True,
    "physics_phot_splitting": 100,
    "physics_compt_splitting": 100,
    "physics_rayl_splitting": 100,
    "physics_splitting_max_energy_kev": 1000.0,

    "physics_interaction_bias_on": True,

    "physics_sample_gamma_cut_mm": 0.001,
    "physics_sample_electron_cut_mm": 0.01,
    "physics_sample_positron_cut_mm": 0.01,
    "physics_sample_proton_cut_mm": 0.01,
    "physics_flu_dataset":"ANSTO"
}


def build_physics_config() -> dict:
    """Build the JSON-ready physics configuration."""

    return {
        "atomic_deexcitation": {
            "fluorescence": st.session_state[
                "physics_fluorescence"
            ],
            "auger": st.session_state[
                "physics_auger"
            ],
            "pixe": st.session_state[
                "physics_pixe"
            ],
            "ignore_deexcitation_cut": st.session_state[
                "physics_ignore_deexcitation_cut"
            ],
        },

        "secondary_splitting": {
            "enabled": st.session_state[
                "physics_secondary_splitting_on"
            ],
            "region": "SampleRegion",
            "photoelectric_split_factor": st.session_state[
                "physics_phot_splitting"
            ],
            "compton_split_factor": st.session_state[
                "physics_compt_splitting"
            ],
            "rayleigh_split_factor": st.session_state[
                "physics_rayl_splitting"
            ],
            "maximum_energy_keV": st.session_state[
                "physics_splitting_max_energy_kev"
            ],
        },

        "interaction_biasing": {
            "enabled": st.session_state[
                "physics_interaction_bias_on"
            ],
        },

        "sample_region_cuts_mm": {
            "gamma": st.session_state[
                "physics_sample_gamma_cut_mm"
            ],
            "electron": st.session_state[
                "physics_sample_electron_cut_mm"
            ],
            "positron": st.session_state[
                "physics_sample_positron_cut_mm"
            ],
            "proton": st.session_state[
                "physics_sample_proton_cut_mm"
            ],
        },
        "flu_dataset":{
            "flu_dataset":st.session_state["physics_flu_dataset"]
        }
    }


def sync_physics_config() -> None:
    """Update physics_config using the current physics values."""

    st.session_state["physics_config"] = (
        build_physics_config()
    )


def initialize_physics_state() -> None:
    """Create defaults and physics_config when missing."""

    for key, default_value in PHYSICS_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

    sync_physics_config()


def reset_physics_defaults() -> None:
    """Restore all physics values to defaults."""

    for key, default_value in PHYSICS_DEFAULTS.items():
        st.session_state[key] = default_value

    sync_physics_config()