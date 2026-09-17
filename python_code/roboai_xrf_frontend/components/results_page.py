from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from components.common import page_header


def _spectrum_figure(energy, before, after):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=energy,
            y=before,
            mode="lines",
            name="Before detector noise",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=energy,
            y=after,
            mode="lines",
            name="After detector noise",
        )
    )
    fig.update_layout(
        template="plotly_dark",
        height=560,
        margin=dict(l=40, r=20, t=30, b=40),
        xaxis_title="Energy (keV)",
        yaxis_title="Counts",
        legend_title_text="Spectrum",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
    )
    return fig


def render_results_page():
    cfg = st.session_state.ui_config
    noise = cfg["noise"]

    page_header(
        "Detector response",
        "Scale the completed Geant4 response to a physical acquisition and apply detector broadening / pile-up.",
    )

    if not st.session_state.run_complete or st.session_state.simulation is None:
        st.info("Run a quantitative Geant4 simulation first.")
        return

    with st.form("noise_form"):
        c1, c2, c3 = st.columns(3)
        current = c1.number_input(
            "Current (mA)",
            min_value=0.000001,
            value=float(noise["current_ma"]),
        )
        live_time = c2.number_input(
            "Live time (s)",
            min_value=0.000001,
            value=float(noise["live_time_s"]),
        )
        fwhm = c3.number_input(
            "FWHM (eV)",
            min_value=0.000001,
            value=float(noise["fwhm_ev"]),
        )

        c1, c2, c3 = st.columns(3)
        fwhm_energy = c1.number_input(
            "FWHM reference energy (keV)",
            min_value=0.000001,
            value=float(noise["fwhm_energy_kev"]),
        )
        pile_up = c2.number_input(
            "Pile-up window (µs)",
            min_value=0.0,
            value=float(noise["pile_up_window_us"]),
        )
        gain = c3.number_input(
            "Gain (keV/channel)",
            min_value=0.000001,
            value=float(noise["detector_gain_kev"]),
            format="%.6f",
        )

        c1, c2, c3 = st.columns(3)
        zero = c1.number_input(
            "Zero offset (keV)",
            value=float(noise["detector_zero_offset"]),
            format="%.6f",
        )
        fano = c2.number_input(
            "Fano factor",
            min_value=0.0,
            value=float(noise["fano_factor"]),
            format="%.6f",
        )
        pair_energy = c3.number_input(
            "Pair creation energy (eV)",
            min_value=0.000001,
            value=float(noise["pair_creation_energy_ev"]),
        )

        with st.expander("Advanced detector-noise settings"):
            c1, c2, c3 = st.columns(3)
            channels = c1.number_input(
                "MCA channels",
                min_value=1,
                value=int(noise["mca_channels"]),
                step=1,
            )
            chunk_size = c2.number_input(
                "Chunk size",
                min_value=1,
                value=int(noise["chunk_size"]),
                step=1000,
            )
            buckets = c3.number_input(
                "Number of buckets",
                min_value=1,
                value=int(noise["number_of_buckets"]),
                step=1,
            )

        submitted = st.form_submit_button(
            "Apply detector response",
            type="primary",
        )

    if submitted:
        noise.update(
            {
                "current_ma": current,
                "live_time_s": live_time,
                "fwhm_ev": fwhm,
                "fwhm_energy_kev": fwhm_energy,
                "pile_up_window_us": pile_up,
                "detector_gain_kev": gain,
                "detector_zero_offset": zero,
                "fano_factor": fano,
                "pair_creation_energy_ev": pair_energy,
                "mca_channels": int(channels),
                "chunk_size": int(chunk_size),
                "number_of_buckets": int(buckets),
            }
        )

        try:
            with st.spinner("Applying detector response..."):
                result = st.session_state.simulation.detector_noise(
                    current=current,
                    live_time=live_time,
                    fwhm=fwhm,
                    fwhm_energy_kev=fwhm_energy,
                    pile_up_window_us=pile_up,
                    detector_gain_kev=gain,
                    detector_zero_offset=zero,
                    fano_factor=fano,
                    pair_creation_energy_ev=pair_energy,
                    mca_channels=int(channels),
                    chunk_size=int(chunk_size),
                    number_of_buckets=int(buckets),
                )
            st.session_state.noise_result = result
            st.success("Detector response complete.")
        except Exception as exc:
            st.exception(exc)

    result = st.session_state.noise_result
    if result is None:
        return

    (
        final_count,
        final_energy_centers,
        scaled_count,
        average_channel_wise_yield,
        se_channel_wise_yield,
        spectrum_yield_avg,
        spectrum_se,
    ) = result

    sim = st.session_state.simulation
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Beam-on", f"{sim.beam_on:,}")
    c2.metric("Exposure", f"{sim.last_mas:,.3f} mAs")
    c3.metric(
        "Incident photons",
        f"{sim.last_incident_photons:,.3e}"
        if sim.last_incident_photons is not None
        else "—",
    )
    c4.metric("Total counts", f"{np.sum(final_count):,.0f}")

    st.plotly_chart(
        _spectrum_figure(
            final_energy_centers,
            scaled_count,
            final_count,
        ),
        use_container_width=True,
    )

    csv = "energy_kev,before_noise,after_noise\n" + "\n".join(
        f"{float(e)},{float(b)},{float(a)}"
        for e, b, a in zip(final_energy_centers, scaled_count, final_count)
    )
    st.download_button(
        "Download spectrum CSV",
        data=csv,
        file_name="xrf_spectrum.csv",
        mime="text/csv",
    )

    with st.expander("Yield statistics"):
        st.write(
            {
                "spectrum_yield_avg": float(spectrum_yield_avg),
                "spectrum_se": float(spectrum_se),
            }
        )
