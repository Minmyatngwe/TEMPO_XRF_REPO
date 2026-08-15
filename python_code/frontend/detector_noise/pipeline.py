import pandas as pd 
import uproot
import math
from detector_noise.noise_function import broaden_energy,calculate_channel_yield_and_se
import matplotlib.pyplot as plt
from helper.xray_tube import get_flu
import numpy as np 
import streamlit as st
import h5py
from pathlib import Path
import json

def apply_detectornoise(
    root_path,
    beam_on,
    number_of_photon,
    live_time,
    pile_up_window,
    fwhm,
    fwhm_energy,
    detector_zero_offset,
    detector_gain,
    fano_factor=0.115,
    pair_creation_energy_ev=3.6,
    mca_channels=2048,
    chunk_size=3000000,
    number_of_buckets=64,
):

    offset_min_energy = detector_zero_offset
    offset_max_energy = (
        detector_zero_offset
        + detector_gain * mca_channels
    )

    print("\n========== DETECTOR NOISE PIPELINE ==========")
    print("Beam-on events:", beam_on)
    print("Incident photons:", number_of_photon)
    print("Live time:", live_time, "s")
    print("Pile-up window:", pile_up_window, "us")
    print("MCA energy minimum:", offset_min_energy, "keV")
    print("MCA energy maximum:", offset_max_energy, "keV")

    (
        average_channel_wise_yield,
        se_channel_wise_yield,
        spectrum_yield_avg,
        spectrum_se,
    ) = calculate_channel_yield_and_se(
        root_path=root_path,
        beam_on=beam_on,
        offset_min_energy=offset_min_energy,
        offset_max_energy=offset_max_energy,
        detector_gain=detector_gain,
        mca_channel=mca_channels,
        chunk_size=chunk_size,
        number_of_buckets=number_of_buckets,
    )

    print("\n--- MONTE CARLO YIELD ---")
    print("Spectrum yield per primary:", spectrum_yield_avg)
    print("Spectrum yield SE:", spectrum_se)
    print(
        "Expected count before detector noise:",
        spectrum_yield_avg * number_of_photon,
    )

    scaled_count = (
        average_channel_wise_yield
        * number_of_photon
    )
    channel_center_energy = (
        offset_min_energy
        + (np.arange(mca_channels) + 0.5)
        * detector_gain
    )

    negative_mask = channel_center_energy < 0

    print(
        "Counts in negative-energy channels before removal:",
        scaled_count[negative_mask].sum(),
    )

    scaled_count[negative_mask] = 0

    expected_total_count = np.sum(scaled_count)

    print("\n--- SCALED SPECTRUM ---")
    print(
        "Scaled spectrum total:",
        expected_total_count,
    )

    detector_rate = expected_total_count / live_time

    print(
        "Detector rate:",
        detector_rate,
        "counts/s",
    )

    if detector_rate <= 0:
        raise ValueError(
            "Detector rate must be greater than zero."
        )

    current_time = 0.0
    photon_arrival_time = []

    while current_time < live_time:
        batch_time = np.random.exponential(
            1.0 / detector_rate,
            size=chunk_size,
        )

        cumulative_batch_time = (
            current_time
            + np.cumsum(batch_time)
        )

        valid_time = (
            cumulative_batch_time <= live_time
        )

        photon_arrival_time.append(
            cumulative_batch_time[valid_time]
        )

        current_time = cumulative_batch_time[-1]

    if photon_arrival_time:
        photon_arrival_time_s = np.concatenate(
            photon_arrival_time
        )
    else:
        photon_arrival_time_s = np.empty(
            0,
            dtype=np.float64,
        )

    photon_arrival_time_in_us = (
        photon_arrival_time_s * 1_000_000
    )

    number_of_arrivals_photon = (
        photon_arrival_time_in_us.shape[0]
    )

    print("\n--- ARRIVAL SIMULATION ---")
    print(
        "Expected number of arrivals:",
        expected_total_count,
    )
    print(
        "Actually sampled arrivals:",
        number_of_arrivals_photon,
    )

    if expected_total_count > 0:
        print(
            "Arrival ratio:",
            number_of_arrivals_photon
            / expected_total_count,
        )

    if number_of_arrivals_photon == 0:
        print("No detector arrivals were generated.")

        final_count = np.zeros(
            mca_channels,
            dtype=np.int64,
        )

        return (
            final_count,
            channel_center_energy,
            scaled_count,
            average_channel_wise_yield,
            se_channel_wise_yield,
            spectrum_yield_avg,
            spectrum_se,
        )

    spectrum_probability = (
        scaled_count / expected_total_count
    )

    print("\n--- SPECTRUM PROBABILITY ---")
    print(
        "Probability sum:",
        spectrum_probability.sum(),
    )
    print(
        "Minimum probability:",
        spectrum_probability.min(),
    )
    print(
        "Maximum probability:",
        spectrum_probability.max(),
    )
    print(
        "Contains NaN:",
        np.isnan(spectrum_probability).any(),
    )

    sampled_channels = np.random.choice(
        mca_channels,
        size=number_of_arrivals_photon,
        p=spectrum_probability,
    )

    incoming_energy = (
        offset_min_energy
        + (
            sampled_channels
            + np.random.random(
                number_of_arrivals_photon
            )
        )
        * detector_gain
    )

    print("\n--- INCOMING ENERGY ---")
    print(
        "Minimum incoming energy:",
        incoming_energy.min(),
        "keV",
    )
    print(
        "Maximum incoming energy:",
        incoming_energy.max(),
        "keV",
    )
    print(
        "Mean incoming energy:",
        incoming_energy.mean(),
        "keV",
    )

    new_pulses = np.empty(
        number_of_arrivals_photon,
        dtype=np.bool_,
    )

    new_pulses[0] = True

    new_pulses[1:] = (
        np.diff(photon_arrival_time_in_us)
        >= pile_up_window
    )

    pulse_group = np.cumsum(new_pulses) - 1

    pile_up_energy = np.bincount(
        pulse_group,
        weights=incoming_energy,
    )

    print("\n--- PILE-UP ---")
    print(
        "Photons before pile-up:",
        number_of_arrivals_photon,
    )
    print(
        "Pulses after pile-up:",
        pile_up_energy.size,
    )
    print(
        "Photons merged by pile-up:",
        number_of_arrivals_photon
        - pile_up_energy.size,
    )
    print(
        "Pulse survival fraction:",
        pile_up_energy.size
        / number_of_arrivals_photon,
    )
    print(
        "Maximum pile-up energy:",
        pile_up_energy.max(),
        "keV",
    )

    smeared_pileup_energy = broaden_energy(
        fwhm_ev=fwhm,
        fwhm_energy_kev=fwhm_energy,
        fano_factor=fano_factor,
        pair_creation_energy_ev=pair_creation_energy_ev,
        measured_energy_kev=pile_up_energy,
    )

    below_mca = np.sum(
        smeared_pileup_energy
        < offset_min_energy
    )

    above_mca = np.sum(
        smeared_pileup_energy
        >= offset_max_energy
    )

    inside_mca = np.sum(
        (
            smeared_pileup_energy
            >= offset_min_energy
        )
        & (
            smeared_pileup_energy
            < offset_max_energy
        )
    )

    print("\n--- MCA RANGE ---")
    print("Pulses below MCA range:", below_mca)
    print("Pulses inside MCA range:", inside_mca)
    print("Pulses above MCA range:", above_mca)

    final_count, final_edges = np.histogram(
        smeared_pileup_energy,
        bins=mca_channels,
        range=(
            offset_min_energy,
            offset_max_energy,
        ),
    )

    final_energy_centers = (
        final_edges[:-1]
        + final_edges[1:]
    ) / 2

    print("\n--- FINAL RESULT ---")
    print(
        "Expected count before noise:",
        expected_total_count,
    )
    print(
        "Count after pile-up:",
        pile_up_energy.size,
    )
    print(
        "Final histogram count:",
        final_count.sum(),
    )

    print(
        "Total count loss:",
        expected_total_count
        - final_count.sum(),
    )

    if expected_total_count > 0:
        print(
            "Final count fraction:",
            final_count.sum()
            / expected_total_count,
        )

    print("============================================\n")

    return (
        final_count,
        final_energy_centers,
        scaled_count,
        average_channel_wise_yield,
        se_channel_wise_yield,
        spectrum_yield_avg,
        spectrum_se,
    )

def save_file(path:str,energy:np.ndarray,preprocessing_count:np.ndarray,original_scaled_count:np.ndarray):
    directory=Path(path)
    
    with open(directory/"updated_config.json","r",encoding="utf-8") as f:
        config=json.load(f)
        
    json_text=json.dumps(config,indent=4)
    with h5py.File(directory/"simulation.h5","w") as h5_file:
        string_dtype=h5py.string_dtype(encoding="utf-8")
        h5_file.create_dataset("meta_data",data=json_text,dtype=string_dtype)
        spectrum_group=h5_file.create_group("spectrum")
        
        spectrum_group.create_dataset(
            "energy_kev",
            data=energy
        )
        
        spectrum_group.create_dataset("preprocessing_count",data=preprocessing_count)
        
        spectrum_group.create_dataset("original_scaled_count",data=original_scaled_count)
        
    
    return path
        
        
        
        
        

        
        
if __name__=="__main__":
    
    d1=130-30
    d2=30
    radius=((0.15*(d1+d2)/d2))/10
    
    area=np.pi*(radius**2)
    
    energy,flu,photo=get_flu(
        current=0.5,
        voltage=50,
        exposure_time=1,
        anode_degree=15,
        anode_target_material="W",
        filter=pd.DataFrame({"filter":["Be"],"thickness (mm)":[0.000001]}),
        source_to_sample=130
    )
    total_photon=photo*30*area 
    print(total_photon)
        
    count, energy_center, scaled_count, avg_channel, se_channel,spectrum_se = apply_detectornoise(
        root_path=r"/home/minmyatngwe/geant_4_xrf/XRF_ONLY/python_code/frontend/runs/roboai_xrf_fe_hitachi_0.1_10m/fe_hitachi_0.1_10m.root",
        beam_on=10000000,
        number_of_photon=total_photon,
        fwhm=140,
        fwhm_energy=5.9,
        live_time=30,
        pile_up_window=0.1,
        detector_zero_offset=0,
        detector_gain=0.024
    )

    average_count_un=((spectrum_se/np.sum(avg_channel))*1)
    # 1. Scale standard error to match scaled_count!
    scaled_se = se_channel * total_photon

    fig, ax = plt.subplots(1, 2, figsize=(14, 6))

    # Left Plot: Raw Scaled Count
    ax[0].step(energy_center, scaled_count, where="mid")
    ax[0].set_title("Scaled Counts")

    # Right Plot: Spectrum + Scaled Standard Error Band
    ax[1].step(energy_center, scaled_count, where="mid", color='blue', label='Scaled Count')
    ax[1].fill_between(
        energy_center,
        scaled_count - scaled_se,
        scaled_count + scaled_se,
        step="mid",
        alpha=0.3,
        color='green',
        label='±1 Standard Error'
    )
    ax[1].set_title(f"Scaled Counts with Uncertainty {np.sum(avg_channel)}+-{average_count_un}")
    ax[1].legend()

    plt.tight_layout()
    plt.show()