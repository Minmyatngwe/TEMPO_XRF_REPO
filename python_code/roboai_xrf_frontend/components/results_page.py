from __future__ import annotations
import pandas as pd
import io
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from components.common import page_header


def _spectrum_figure(
    energy,
    before,
    after,
    comparison_energy=None,
    comparison_counts=None,
    comparison_name="Uploaded spectrum",
):
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

    if comparison_energy is not None and comparison_counts is not None:
        fig.add_trace(
            go.Scatter(
                x=comparison_energy,
                y=comparison_counts,
                mode="lines",
                name=comparison_name,
                line=dict(dash="dash"),
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
def _read_comparison_spectrum(uploaded_file):
    uploaded_file.seek(0)

    df = pd.read_csv(
        io.BytesIO(uploaded_file.getvalue()),
        sep=r"[\s,;]+",
        engine="python",
        comment="#",
        header=None,
    )

    df = (
        df.dropna(axis=0, how="all")
        .dropna(axis=1, how="all")
    )

    if df.shape[1] < 2:
        raise ValueError(
            "Comparison spectrum must contain at least two columns: "
            "energy and counts."
        )

    # Only first two columns are needed
    df = df.iloc[:, :2].copy()

    # Convert to numbers.
    # If the file contains a header like:
    # energy_kev,counts
    # it will automatically be removed here.
    df[0] = pd.to_numeric(df[0], errors="coerce")
    df[1] = pd.to_numeric(df[1], errors="coerce")

    df = df.dropna()

    if df.empty:
        raise ValueError(
            "No valid numerical energy/count data found in the uploaded file."
        )

    energy = df[0].to_numpy(dtype=float)
    counts = df[1].to_numpy(dtype=float)

    order = np.argsort(energy)

    return energy[order], counts[order]
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

    st.subheader("Spectrum comparison")

    comparison_file = st.file_uploader(
        "Upload a spectrum to compare",
        type=["csv", "txt", "dat"],
        key="comparison_spectrum_upload",
        help="The first column should contain energy in keV and the second column counts.",
    )

    comparison_energy = None
    comparison_counts = None
    comparison_name = "Uploaded spectrum"

    if comparison_file is not None:
        try:
            comparison_energy, comparison_counts = _read_comparison_spectrum(
                comparison_file
            )

            comparison_name = comparison_file.name

            st.success(
                f"Loaded comparison spectrum: "
                f"{len(comparison_energy):,} points"
            )

        except Exception as exc:
            st.error(f"Could not read comparison spectrum: {exc}")

    normalize_comparison = st.checkbox(
        "Scale uploaded spectrum to simulation",
        value=False,
        help="Scales the uploaded spectrum so its maximum matches the simulated spectrum.",
    )

    if (
        normalize_comparison
        and comparison_counts is not None
        and np.max(comparison_counts) > 0
        and np.max(final_count) > 0
    ):
        comparison_counts = (
            comparison_counts
            / np.max(comparison_counts)
            * np.max(final_count)
        )
    st.plotly_chart(
        _spectrum_figure(
            final_energy_centers,
            scaled_count,
            final_count,
            comparison_energy=comparison_energy,
            comparison_counts=comparison_counts,
            comparison_name=comparison_name,
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
