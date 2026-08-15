import numpy as np 
import uproot
import matplotlib.pyplot as plt 
import pandas as pd 
import uproot 
import tempfile
import os 


def calculate_channel_yield_and_se(
    root_path:str,
    beam_on:int,
    offset_min_energy:float,
    offset_max_energy:float,
    detector_gain:float,
    mca_channel:int,
    chunk_size:int=3000000,
    number_of_buckets:int=64):
    
    
    if beam_on < 2:
        raise ValueError("At least two primary events are required.")
    
    
    sum_x=np.zeros(mca_channel,dtype=np.float64)
    sum_x2=np.zeros(mca_channel,dtype=np.float64)
    
    record_dtype = np.dtype([
        ('event_id', np.int64),  
        ('channel', np.int32),   
        ('weight', np.float64)
    ])
    
    with tempfile.TemporaryDirectory() as temp_directory:
        
        bucket_paths=[
            os.path.join(temp_directory,f"bucket_{i}.bin")
            for i in range(number_of_buckets)
        ]
        
        try:
            bucket_files=[open(path,"wb")for path in bucket_paths ]
            
            
            with uproot.open(f"{root_path}:MyTree") as tree:
                for arrays in(
                    tree.iterate(
                    expressions=["EventId","Energy", "Weight"],
                    step_size=chunk_size,
                    library="np",
                    how=dict
                    ) ):
                    
                    event_id=arrays['EventId']
                    energy=arrays["Energy"]
                    weight=arrays['Weight']
                    
                    valid_mask=((energy>=offset_min_energy)&(energy<offset_max_energy))
                    filter_energy=energy[valid_mask]
                    filter_weight=weight[valid_mask]
                    filter_event_id=event_id[valid_mask]
                    
                    channel_position=((filter_energy-offset_min_energy)/detector_gain).astype(np.int32)
                    valid_channel = (
                        (channel_position >= 0)
                        & (channel_position < mca_channel)
                    )
                    channel_position = channel_position[valid_channel]
                    filter_weight = filter_weight[valid_channel]
                    filter_event_id = filter_event_id[valid_channel]
                    bucket_id=filter_event_id%number_of_buckets
                    
                    for bucket in range(number_of_buckets):
                        
                        mask=bucket_id==bucket 
                        if not np.any(mask):
                            continue
                    
                        records=np.empty(
                            np.count_nonzero(mask),
                            dtype=record_dtype
                        )
                        
                        records["event_id"]=filter_event_id[mask]
                        records["weight"]=filter_weight[mask]
                        records['channel']=channel_position[mask]
                        
                        records.tofile(bucket_files[bucket])
                        
                        
                        
        finally:
            
            for file in bucket_files:
                file.close()
        

        spectrum_sum_x = 0.0
        spectrum_sum_x2 = 0.0
        for path in bucket_paths:
            
            if os.path.getsize(path)==0:
                continue
            
            record_file=np.fromfile(
                path,dtype=record_dtype
            )
            
            df=pd.DataFrame(record_file)
            event_totals = (
                df.groupby("event_id")["weight"]
                .sum()
                .to_numpy()
            )

            spectrum_sum_x += np.sum(event_totals)
            spectrum_sum_x2 += np.sum(event_totals**2)            
            
            key=(record_file['event_id'].astype(np.int64)*mca_channel)+record_file["channel"].astype(np.int64)
            
            
            order=np.argsort(key)
            
            sorted_key=key[order]
            sorted_weight=record_file['weight'][order]
            
            
            group_start=np.concatenate(
                (
                    np.array([0],dtype=np.int64),
                    
                    np.flatnonzero(sorted_key[1:]!=sorted_key[:-1])+1
                )
            )
            
            event_channel_weight=np.add.reduceat(
                sorted_weight,
                group_start
            )
            
            group_channels=sorted_key[group_start]%mca_channel
            
            sum_x+=np.bincount(group_channels,event_channel_weight,minlength=mca_channel)

            sum_x2+=np.bincount(group_channels,event_channel_weight**2,minlength=mca_channel)

            
            
    
    channel_yield=sum_x/beam_on
    
    variance_numerator = (
        sum_x2
        - (sum_x**2 / beam_on)
    )

    variance_numerator = np.maximum(
        variance_numerator,
        0.0,
    )
    channel_se = np.sqrt(
        variance_numerator
        / (
            beam_on
            * (beam_on - 1.0)
        )
    )
    
    spectrum_yield = spectrum_sum_x / beam_on

    spectrum_variance_numerator = (
        spectrum_sum_x2
        - spectrum_sum_x**2 / beam_on
    )

    spectrum_variance_numerator = max(
        spectrum_variance_numerator,
        0.0,
    )

    spectrum_se = np.sqrt(
        spectrum_variance_numerator
        / (beam_on * (beam_on - 1.0))
    )
    return channel_yield,channel_se,spectrum_yield,spectrum_se

        
        
        
        
    

    




def calculate_electronic_noise_var(
    fwhm_ev,
    fwhm_energy_kev,
    fano_factor,
    pair_creation_energy_ev
):
    """
    Calculate electronic-noise variance in eV².

    Example detector specification:
        FWHM = 140 eV at 5.9 keV
    """

    reference_energy_ev = fwhm_energy_kev * 1000.0

    sigma_reference_ev = fwhm_ev / 2.35482

    fano_variance_ev2 = (
        fano_factor
        * pair_creation_energy_ev
        * reference_energy_ev
    )

    electronic_variance_ev2 = (
        sigma_reference_ev**2
        - fano_variance_ev2
    )

    if electronic_variance_ev2 < 0:
        raise ValueError(
            "Calculated electronic-noise variance is negative. "
            "Check FWHM, reference energy, Fano factor, and "
            "pair-creation energy."
        )

    return electronic_variance_ev2


def broaden_energy(
    measured_energy_kev,
    fwhm_ev,
    fwhm_energy_kev,
    fano_factor,
    pair_creation_energy_ev
):
    """
    Randomly broaden measured energies.

    Input energies: keV
    Output energies: keV
    """

    electronic_variance_ev2 = calculate_electronic_noise_var(
        fwhm_ev=fwhm_ev,
        fwhm_energy_kev=fwhm_energy_kev,
        fano_factor=fano_factor,
        pair_creation_energy_ev=pair_creation_energy_ev
    )

    energy_kev = np.asarray(measured_energy_kev, dtype=float)
    energy_ev = energy_kev * 1000.0

    fano_variance_ev2 = (
        fano_factor
        * pair_creation_energy_ev
        * energy_ev
    )

    sigma_total_ev = np.sqrt(
        electronic_variance_ev2
        + fano_variance_ev2
    )

    sigma_total_kev = sigma_total_ev / 1000.0

    broadened_energy_kev = np.random.normal(
        loc=energy_kev,
        scale=sigma_total_kev
    )

    return broadened_energy_kev
    
    

if __name__=="__main__":
    print(calculate_channel_yield_and_se(
        "/home/minmyatngwe/geant_4_xrf/XRF_ONLY/python_code/frontend/runs/roboai_xrf_fe_hitachi_0.1_10m/fe_hitachi_0.1_10m.root",
        10000000,
        -0.1,49.9,
        0.024,
        mca_channel=2048
    ))