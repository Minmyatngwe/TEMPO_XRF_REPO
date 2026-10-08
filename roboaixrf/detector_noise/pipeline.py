import pandas as pd 
import uproot
import math
from .noise_function import broaden_energy,calculate_channel_yield_and_se
import matplotlib.pyplot as plt
from .xray_tube import get_flu
import numpy as np 
import streamlit as st
import h5py
from pathlib import Path
import json
import tempfile
import os

# def apply_detectornoise(
#     root_path,
#     beam_on,
#     number_of_photon,
#     live_time,
#     pile_up_window,
#     fwhm,
#     fwhm_energy,
#     detector_zero_offset,
#     detector_gain,
#     fano_factor=0.115,
#     pair_creation_energy_ev=3.6,
#     mca_channels=2048,
#     chunk_size=3000000,
#     number_of_buckets=64,
# ):

#     offset_min_energy = detector_zero_offset
#     offset_max_energy = (
#         detector_zero_offset
#         + detector_gain * mca_channels
#     )

#     print("\n========== DETECTOR NOISE PIPELINE ==========")
#     print("Beam-on events:", beam_on)
#     print("Incident photons:", number_of_photon)
#     print("Live time:", live_time, "s")
#     print("Pile-up window:", pile_up_window, "us")
#     print("MCA energy minimum:", offset_min_energy, "keV")
#     print("MCA energy maximum:", offset_max_energy, "keV")

#     (
#         average_channel_wise_yield,
#         se_channel_wise_yield,
#         spectrum_yield_avg,
#         spectrum_se,
#     ) = calculate_channel_yield_and_se(
#         root_path=root_path,
#         beam_on=beam_on,
#         offset_min_energy=offset_min_energy,
#         offset_max_energy=offset_max_energy,
#         detector_gain=detector_gain,
#         mca_channel=mca_channels,
#         chunk_size=chunk_size,
#         number_of_buckets=number_of_buckets,
#     )

#     print("\n--- MONTE CARLO YIELD ---")
#     print("Spectrum yield per primary:", spectrum_yield_avg)
#     print("Spectrum yield SE:", spectrum_se)
#     print(
#         "Expected count before detector noise:",
#         spectrum_yield_avg * number_of_photon,
#     )

#     scaled_count = average_channel_wise_yield* number_of_photon

#     channel_center_energy = offset_min_energy+ (np.arange(mca_channels) + 0.5)* detector_gain

#     negative_mask = channel_center_energy < 0

#     print(
#         "Counts in negative-energy channels before removal:",
#         scaled_count[negative_mask].sum(),
#     )

#     scaled_count[negative_mask] = 0

#     expected_total_count = np.sum(scaled_count)

#     print("\n--- SCALED SPECTRUM ---")
#     print(
#         "Scaled spectrum total:",
#         expected_total_count,
#     )

#     detector_rate = expected_total_count / (live_time)
#     detector_rate_us=detector_rate/ 1_000_000

#     print(
#         "Detector rate:",
#         detector_rate,
#         "counts/s",
#     )

#     if detector_rate <= 0:
#         raise ValueError(
#             "Detector rate must be greater than zero."
#         )

#     current_time = 0.0
#     photon_arrival_time = []
    
#     tmp_file=tempfile.NamedTemporaryFile(delete=False,suffix=".bin")
#     filename=tmp_file.name
#     live_time_us=live_time*1_000_000

#     while current_time < live_time_us:
#         batch_time = np.random.exponential(
#             1.0 / detector_rate_us,
#             size=chunk_size,
#         ).astype(np.float32)
        
#         cumulative_batch_time = current_time+ np.cumsum(batch_time)
        
#         valid_time =cumulative_batch_time <= live_time_us

#         with open(filename,"ab") as tmp_file:
#             tmp_file.write(cumulative_batch_time[valid_time].tobytes())
#             tmp_file.flush()

#         # photon_arrival_time.append(
#         #     cumulative_batch_time[valid_time]
#         # )

#         current_time = cumulative_batch_time[-1]


#     # if photon_arrival_time:
#     #     photon_arrival_time_s = np.concatenate(
#     #         photon_arrival_time
#     #     )
#     # else:
#     #     photon_arrival_time_s = np.empty(
#     #         0,
#     #         dtype=np.float64,
#     #     )
#     photon_arrival_time_us=np.memmap(filename,dtype="float32",mode="r")
#     number_of_arrival_photon=photon_arrival_time_us.size
    
#     spectrum_probability=scaled_count/expected_total_count
#     sampled_channels=np.random.choice(
#         mca_channels,
#         size=number_of_arrival_photon,
#         p=spectrum_probability
#     )
    
#     group_start_time_us=None
#     for start in range(0,number_of_arrival_photon,chunk_size):
        
        
        
        
        
    
#     # photon_arrival_time_in_us = (
#     #     photon_arrival_time_s * 1_000_000
#     # )

#     # number_of_arrivals_photon = (
#     #     photon_arrival_time_in_us.shape[0]
#     # )
#     os.remove(filename)


#     if expected_total_count > 0:
#         print(
#             "Arrival ratio:",
#             number_of_arrivals_photon
#             / expected_total_count,
#         )

#     if number_of_arrivals_photon == 0:
#         print("No detector arrivals were generated.")

#         final_count = np.zeros(
#             mca_channels,
#             dtype=np.int64,
#         )

#         return (
#             final_count,
#             channel_center_energy,
#             scaled_count,
#             average_channel_wise_yield,
#             se_channel_wise_yield,
#             spectrum_yield_avg,
#             spectrum_se,
#         )

#     spectrum_probability = (
#         scaled_count / expected_total_count
#     )


#     sampled_channels = np.random.choice(
#         mca_channels,
#         size=number_of_arrivals_photon,
#         p=spectrum_probability,
#     )

#     incoming_energy = (
#         offset_min_energy
#         + (
#             sampled_channels
#             + np.random.random(
#                 number_of_arrivals_photon
#             )
#         )
#         * detector_gain
#     )

#     print("\n--- INCOMING ENERGY ---")
#     print(
#         "Minimum incoming energy:",
#         incoming_energy.min(),
#         "keV",
#     )
#     print(
#         "Maximum incoming energy:",
#         incoming_energy.max(),
#         "keV",
#     )
#     print(
#         "Mean incoming energy:",
#         incoming_energy.mean(),
#         "keV",
#     )

#     new_pulses = np.empty(
#         number_of_arrivals_photon,
#         dtype=np.bool_,
#     )

#     new_pulses[0] = True

#     new_pulses[1:] = (
#         np.diff(photon_arrival_time_in_us)
#         >= pile_up_window
#     )

#     pulse_group = np.cumsum(new_pulses) - 1

#     pile_up_energy = np.bincount(
#         pulse_group,
#         weights=incoming_energy,
#     )

#     print("\n--- PILE-UP ---")
#     print(
#         "Photons before pile-up:",
#         number_of_arrivals_photon,
#     )
#     print(
#         "Pulses after pile-up:",
#         pile_up_energy.size,
#     )
#     print(
#         "Photons merged by pile-up:",
#         number_of_arrivals_photon
#         - pile_up_energy.size,
#     )
#     print(
#         "Pulse survival fraction:",
#         pile_up_energy.size
#         / number_of_arrivals_photon,
#     )
#     print(
#         "Maximum pile-up energy:",
#         pile_up_energy.max(),
#         "keV",
#     )

#     smeared_pileup_energy = broaden_energy(
#         fwhm_ev=fwhm,
#         fwhm_energy_kev=fwhm_energy,
#         fano_factor=fano_factor,
#         pair_creation_energy_ev=pair_creation_energy_ev,
#         measured_energy_kev=pile_up_energy,
#     )

#     below_mca = np.sum(
#         smeared_pileup_energy
#         < offset_min_energy
#     )

#     above_mca = np.sum(
#         smeared_pileup_energy
#         >= offset_max_energy
#     )

#     inside_mca = np.sum(
#         (
#             smeared_pileup_energy
#             >= offset_min_energy
#         )
#         & (
#             smeared_pileup_energy
#             < offset_max_energy
#         )
#     )

#     print("\n--- MCA RANGE ---")
#     print("Pulses below MCA range:", below_mca)
#     print("Pulses inside MCA range:", inside_mca)
#     print("Pulses above MCA range:", above_mca)

#     final_count, final_edges = np.histogram(
#         smeared_pileup_energy,
#         bins=mca_channels,
#         range=(
#             offset_min_energy,
#             offset_max_energy,
#         ),
#     )

#     # final_energy_centers = (
#     #     final_edges[:-1]
#     #     + final_edges[1:]
#     # ) / 2
    
#     final_energy_start=final_edges[:-1]

#     print("\n--- FINAL RESULT ---")
#     print(
#         "Expected count before noise:",
#         expected_total_count,
#     )
#     print(
#         "Count after pile-up:",
#         pile_up_energy.size,
#     )
#     print(
#         "Final histogram count:",
#         final_count.sum(),
#     )

#     print(
#         "Total count loss:",
#         expected_total_count
#         - final_count.sum(),
#     )

#     if expected_total_count > 0:
#         print(
#             "Final count fraction:",
#             final_count.sum()
#             / expected_total_count,
#         )

#     print("============================================\n")

#     return (
#         final_count,
#         final_energy_start,
#         scaled_count,
#         average_channel_wise_yield,
#         se_channel_wise_yield,
#         spectrum_yield_avg,
#         spectrum_se,
#     )
import pandas as pd 
import uproot
import math
from .noise_function import broaden_energy,calculate_channel_yield_and_se
import matplotlib.pyplot as plt
# from .xray_tube import get_flu
import numpy as np 
import streamlit as st
import h5py
from pathlib import Path
import json
import tempfile
import os
from numba import njit

@njit
def generate_sample_photon_chunk(
    current_time,
    live_time,
    chunk_size,
    detecotr_rate,
    spectrum_probability,
    mca_channels,
    offset_min_energy,
    detector_gain,
):
    if chunk_size <= 0 or detecotr_rate <= 0:
        raise ValueError("chunk_size and detector rate must be positive")

    # Generate arrival times BEFORE filtering.
    all_times = current_time + np.cumsum(
        np.random.exponential(
            1.0 / detecotr_rate,
            size=chunk_size,
        )
    )

    if all_times[-1] >= live_time:
        next_time = live_time
    else:
        next_time = all_times[-1]

    time_chunk = all_times[all_times <= live_time]

    spectrum_cdf = np.cumsum(spectrum_probability)
    spectrum_cdf /= spectrum_cdf[-1]

    sampled_channels = np.searchsorted(
        spectrum_cdf,
        np.random.random(len(time_chunk)),
        side="right",
    )

    sampled_energy = (
        offset_min_energy
        + (
            sampled_channels
            + np.random.random(len(time_chunk))
        ) * detector_gain
    ).astype(np.float32)

    return next_time, time_chunk, sampled_channels, sampled_energy
@njit
def pile_up_chunk(photon_times_chunk,photon_energies_chunk,pile_up_window,pulse_is_active,current_pulse_time,current_pulse_energy):
    
    number_of_photons=len(photon_times_chunk)
    
    if len(photon_times_chunk)!=len(photon_energies_chunk):
        raise ValueError("Photon_time_chunk and photon energies chunk must have same length")
    
    finished_energy=np.empty(number_of_photons)
    
    finished_time=np.empty(number_of_photons)
    
    number_of_finished_photons=0
    
    for photon_index in range(number_of_photons):
        
        photon_time=photon_times_chunk[photon_index]
        
        photon_energy=photon_energies_chunk[photon_index]
        
        if not pulse_is_active:
        
            pulse_is_active=True
        
            current_pulse_energy=photon_energy
        
            current_pulse_time=photon_time
        
            continue

        if (photon_time-current_pulse_time)<pile_up_window:
        
            current_pulse_energy+=photon_energy
        
            continue
        
        output_index=number_of_finished_photons
        
        finished_energy[output_index]=current_pulse_energy
        
        finished_time[output_index]=current_pulse_time
        
        number_of_finished_photons+=1
        
        current_pulse_time=photon_time
        
        current_pulse_energy=photon_energy
        
    finished_time=finished_time[:number_of_finished_photons]
    
    finished_energy=finished_energy[:number_of_finished_photons]
    
        
    return finished_time,finished_energy,pulse_is_active,current_pulse_time,current_pulse_energy
        
            


@njit    
def apply_pileup(pile_up_array,sampling_channel_array,number_of_arrival_photon,chunk_size,pile_up_window,mca_channel,
                 offset_min_energy,offset_max_energy,fwhm,fwhm_energy,fano_factor,pair_creation_energy_ev):
    final_bin_count=np.zeros(mca_channel,dtype=np.int64)
    final_bin_energy = np.linspace(
        offset_min_energy,
        offset_max_energy,
        mca_channel + 1,
    )

    # pile_up_array=np.memmap(pile_up_file,dtype=np.float64,mode="r")
    
    # sampling_channel_array=np.memmap(sampling_channel_file,dtype=np.float32,shape=(number_of_arrival_photon,2),mode="r")

    full_no_chunk=int(number_of_arrival_photon//chunk_size)
    start_index=0
    pulse_is_active=False
    current_pulse_energy=0
    current_pulse_time=0
    for start_index in range(0, number_of_arrival_photon, chunk_size):
        end_index = min(
            start_index + chunk_size,
            number_of_arrival_photon,
        )
        tempo_pile_up=pile_up_array[start_index:end_index]
        tempo_sample_channel=sampling_channel_array[start_index:end_index]
        tempo_energy=tempo_sample_channel[:,1]
        (finished_time,finished_energy,
         pulse_is_active,current_pulse_time,current_pulse_energy)=pile_up_chunk(tempo_pile_up,tempo_energy,pile_up_window=pile_up_window,pulse_is_active=pulse_is_active,current_pulse_energy=current_pulse_energy,current_pulse_time=current_pulse_time)
        
        smeared_pileup_energy=broaden_energy(
            fwhm_ev=fwhm,
            fwhm_energy_kev=fwhm_energy,
            fano_factor=fano_factor,
            pair_creation_energy_ev=pair_creation_energy_ev,
            measured_energy_kev=finished_energy
        )
        count, _ = np.histogram(
            smeared_pileup_energy,
            bins=mca_channel,
            range=(offset_min_energy, offset_max_energy),
        )
        for channel in range(mca_channel):
            final_bin_count[channel]+=count[channel]    
    return final_bin_count,final_bin_energy        


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
    offset_min_energy=detector_zero_offset
    offset_max_energy=offset_min_energy+(mca_channels*detector_gain)
    print("Starting ROOT reduction", flush=True)
   
    (channel_wise_detector_yield,
    se_channel_wise_detector,
    spectrum_detector_yield,
    se_spectrum_detector)=calculate_channel_yield_and_se(
        root_path=root_path,
        beam_on=beam_on,
        offset_min_energy=offset_min_energy,
        offset_max_energy=offset_max_energy,
        detector_gain=detector_gain,
        mca_channel=mca_channels,
        chunk_size=chunk_size,
        number_of_buckets=number_of_buckets
    )
    print("ROOT reduction finished", flush=True)

    scaled_spectrum=channel_wise_detector_yield*number_of_photon
    
    channel_center_energy=offset_min_energy+(np.arange(mca_channels)+0.5)*detector_gain
    negative_mask=channel_center_energy<0
    scaled_spectrum[negative_mask]=0
    
    excepted_total_photon_count=np.sum(scaled_spectrum)
    detector_rate_s=excepted_total_photon_count/live_time
    detector_rate_us=detector_rate_s/1_000_000
    
    if detector_rate_s<=0:
        raise ValueError("Detector rate must be greater than zeros")

    if not np.isfinite(live_time) or live_time <= 0:
        raise ValueError("live_time must be finite and positive.")
    if not np.all(np.isfinite(scaled_spectrum)) or np.any(scaled_spectrum < 0):
        raise ValueError("Spectrum values must be finite and nonnegative.")
    
    if not np.isfinite(excepted_total_photon_count) or excepted_total_photon_count <= 0:
        raise ValueError("Expected photon count must be finite and positive.")
    
    pile_up_temp_file=tempfile.NamedTemporaryFile(delete=False,suffix=".bin")
    pile_up_file_name=pile_up_temp_file.name 
    
    live_time_us=live_time*1_000_000
    print("Generating arrival times", flush=True)
    print(
        f"Expected detector photons: {excepted_total_photon_count:,.0f}",
        flush=True,
    )
    print(
        f"Arrival-time file: approximately "
        f"{excepted_total_photon_count * 8 / 1e9:.2f} GB",
        flush=True,
    )
    current_time=0
    batch_number = 0
    scaled_spectrum_probability=scaled_spectrum/excepted_total_photon_count

    # with open(pile_up_file_name,"ab") as f:
    #     while current_time<=live_time_us:
    #         batch_time=np.random.exponential(
    #             1/detector_rate_us,
    #             size=chunk_size
    #         ).astype(np.float64)
            
    #         cumulative_batch_time=current_time+np.cumsum(batch_time)
            
    #         current_time=cumulative_batch_time[-1]  
            
    #         valid_time=cumulative_batch_time<=live_time_us
        
    #         f.write(cumulative_batch_time[valid_time].tobytes())
    #         f.flush()    
    #         batch_number += 1
    #         if batch_number % 10 == 0:
    #             progress = min(current_time / live_time_us, 1.0)
    #             print(
    #                 f"Arrival generation: {progress:.2%}",
    #                 flush=True,
    #             )
    
    current_time=0
    pulse_is_active=False
    current_pulse_time=0
    current_pulse_energy=0
    final_bin_count=np.zeros(mca_channels,dtype=np.int64)
    final_bin_energy = np.linspace(
        offset_min_energy,
        offset_max_energy,
        mca_channels + 1,
    )
    batch=0
    while current_time<live_time_us:
        
        current_time,time_chunk,sampled_channels_chunk,sampled_energy_chunk=generate_sample_photon_chunk(current_time=current_time,live_time=live_time_us,chunk_size=chunk_size,
                                     detecotr_rate=detector_rate_us,
                                     spectrum_probability=scaled_spectrum_probability,
                                     mca_channels=mca_channels,
                                     offset_min_energy=offset_min_energy,
                                     detector_gain=detector_gain)
        
        (finished_time,finished_energy,
         pulse_is_active,current_pulse_time,
         current_pulse_energy)=pile_up_chunk(time_chunk,sampled_energy_chunk,pile_up_window=pile_up_window,pulse_is_active=pulse_is_active,
                      current_pulse_time=current_pulse_time,current_pulse_energy=current_pulse_energy)
         
        smeared_energy=broaden_energy(
             fwhm_energy_kev=fwhm_energy,
             fwhm_ev=fwhm,
             fano_factor=fano_factor,
             pair_creation_energy_ev=pair_creation_energy_ev,
             measured_energy_kev=finished_energy
         )
        count,_=np.histogram(
            smeared_energy,
            bins=mca_channels,
            range=(offset_min_energy,offset_max_energy)
        )
        for channel in range(mca_channels):
            final_bin_count[channel]+=count[channel]
        
        batch+=1
        
        if batch % 10 == 0:
            progress = 100.0 * current_time / live_time_us
            print(f"Generation progress: {progress:.1f}%")        
                
    # print("Arrival generation finished", flush=True)

    
    # pile_up_us_array=np.memmap(pile_up_file_name,dtype=np.float64,mode="r")
    
    # number_of_arrival_photon=pile_up_us_array.size

    # full_no_chunk=int(number_of_arrival_photon/chunk_size)
    
    # left_over_photon=number_of_arrival_photon-(full_no_chunk*chunk_size)
    
    # channel_sampling_file=tempfile.NamedTemporaryFile(delete=False,suffix=".npy")
    
    # channel_sampling_file_name=channel_sampling_file.name
    
    # sampling_file_array=np.lib.format.open_memmap(
    #     channel_sampling_file_name,
    #     mode="w+",
    #     dtype=np.float32,
    #     shape=(number_of_arrival_photon,2)
    # )
    # start=0
    # for i in range(full_no_chunk):
        
    #     sampled_channels=np.random.choice(
    #         mca_channels,
    #         size=int(chunk_size),
    #         p=scaled_spectrum_probability
    #     ).astype(np.float32)
        
    #     sampled_energy=offset_min_energy+((sampled_channels+np.random.random(int(sampled_channels.shape[0])))*detector_gain).astype(np.float32).reshape(-1,1)
        
    #     sampling_file_array[start:start+int(chunk_size)]=np.concatenate([sampled_channels.reshape(-1,1),sampled_energy],axis=1)
    #     start+=int(chunk_size)

    # if left_over_photon>0:

    #     sampled_channels=np.random.choice(
    #         mca_channels,
    #         size=left_over_photon,
    #         p=scaled_spectrum_probability
    #     ).astype(np.float32)
    #     sampled_energy=offset_min_energy+((sampled_channels+np.random.random(int(sampled_channels.shape[0])))*detector_gain).astype(np.float32).reshape(-1,1)

    #     sampling_file_array[start:start+left_over_photon]=np.concatenate([sampled_channels.reshape(-1,1),sampled_energy],axis=1)
    # count,energy=apply_pileup(pile_up_array=pile_up_us_array,sampling_channel_array=sampling_file_array,
    #             number_of_arrival_photon=number_of_arrival_photon,
    #             chunk_size=chunk_size,
    #             pile_up_window=pile_up_window,
    #             mca_channel=mca_channels,
    #             offset_max_energy=offset_max_energy,
    #             offset_min_energy=offset_min_energy,
    #             fwhm=fwhm,
    #             fwhm_energy=fwhm_energy,
    #             fano_factor=fano_factor,
    #             pair_creation_energy_ev=pair_creation_energy_ev)
    # # with open(channel_sampling_file_name,"ab") as f:
        
    # #     for i in range(full_no_chunk):
    # #         sampled_channels=np.random.choice(
    # #             mca_channels,
    # #             size=int(chunk_size/2),
    # #             p=scaled_spectrum_probability
    # #         )
    # #         sampled_energy=offset_min_energy+(sampled_channels*(np.random.random(int(chunk_size/2))*detector_gain))
            
    # #         f.write(sampled_channels.tobytes())
    # #         f.flush()
    # #     left_over_sampled_channels=np.random.choice(
    # #         mca_channels,
    # #         size=left_over_photon,
    # #         p=scaled_spectrum_probability
    # #     )

    # #     f.write(left_over_sampled_channels.tobytes())
    # #     f.flush()
    
    # os.remove(pile_up_file_name)
    # os.remove(channel_sampling_file_name)
    # print(count)
    # print(energy)
    return (
        final_bin_count,
        final_bin_energy[:-1],
        scaled_spectrum,
        channel_wise_detector_yield,
        se_channel_wise_detector,
        spectrum_detector_yield,
        se_spectrum_detector,
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
        voltage=50,
        anode_degree=15,
        anode_target_material="W",

        mas=0.5,
        filters=[{"element":"Al","thickness_mm":0.001}],
        source_to_tube_collimator_mm=1,
        tube_type="reflection",
        target_thickness_um=0
    )
    total_photon=photo*area 
    print(total_photon)
        
    count, energy_center, scaled_count, avg_channel, se_channel,spectrum_se = apply_detectornoise(
        root_path=r"/home/minmyatngwe/xrf_pip/runs/full_xrf_example/simulation.root",
        beam_on=10000000,
        number_of_photon=total_photon,
        fwhm=140,
        fwhm_energy=5.9,
        live_time=30,
        pile_up_window=0.1,
        detector_zero_offset=0,
        detector_gain=0.025
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