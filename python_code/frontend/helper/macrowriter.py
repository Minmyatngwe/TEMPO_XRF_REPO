def write_macro(incident_angle,source_to_sample,
    detector_thickness,
    detector_active_area,
    detector_to_sample_distance,
    takeoff_angle,beamon,numberofthread,filepath,isvirtual,world_material,sample_density
    ,sampleMaterialIsCustom,focal_spot_diameter,
    detector_collimatory_is_enable,
    detector_collimatory_composition_is_custom,
    sample_detector_collimatory_dsitance,
    detector_collimatory_material,
    sample_detector_collimatory_angle,sample_detector_collimatory_density,
    detector_collimatory_thickness,
    detector_collimatory_outer_radius,
    detector_collimatory_inner_radius,
    energy_bins=None,fluence_list=None,):
    
    
    macro_file=f"""
    /xrf/sampleMaterial G4_Fe
    /xrf/sampleMaterialDensity 7.874 g/cm3
    /xrf/sampleSize 5 5 0.005 mm
    /xrf/fileName {filepath}
    /xrf/incidentAngle {incident_angle}
    /xrf/sourceDistance {source_to_sample}
    /xrf/detectorthickness {detector_thickness}
    /xrf/detectorArea {detector_active_area}
    /xrf/detectorDistance {detector_to_sample_distance}
    /xrf/takeoffAngle {takeoff_angle}
    /xrf/worldmat {world_material}
    /xrf/sampleMaterialDensity {sample_density}
    /xrf/sampleMaterialIsCustom {sampleMaterialIsCustom}
    /xrf/focalspotdiameter {focal_spot_diameter}
/xrf/addSampleElement Ni 0.61

/xrf/addSampleElement Cr 0.215

/xrf/addSampleElement Mo 0.09

/xrf/addSampleElement Fe 0.05

/xrf/addSampleElement Nb 0.035
/xrf/sampleToCollimatorDistance 10
/xrf/sourceCollimatoryDiameter 0.5
/xrf/detectorCollimatorIsEnabled {detector_collimatory_is_enable}
/xrf/detectorCollimatorIsCustom {detector_collimatory_composition_is_custom}
/xrf/detectorCollimatorMaterial {detector_collimatory_material}
/xrf/sampleToDetectorCollimatorDistance {sample_detector_collimatory_dsitance}
/xrf/detectorCollimatoryAngleFromSample {sample_detector_collimatory_angle}
/xrf/detectorCollimatorDensity {sample_detector_collimatory_density}
/xrf/detectorCollimatorThickness {detector_collimatory_thickness}
/xrf/detectorCollimatorOuterRadius {detector_collimatory_outer_radius}
/xrf/detectorCollimatorInnerRadius {detector_collimatory_inner_radius}

/run/numberOfThreads {numberofthread}
    
    /run/initialize
    /gps/particle gamma

    """

    
    if isvirtual:
        final_macro=macro_file+'\n'+"""  
        
        /gps/energy 50 keV
        /vis/open OGLSQt
                                        /vis/drawVolume

                                        /vis/scene/add/axes 0 0 0 30 mm
                                        /tracking/storeTrajectory 1
                                        /vis/scene/add/trajectories smooth
                                        /vis/scene/endOfEventAction accumulate 10
                                        /run/beamOn 100"""
    else:
        macro_file+="""

/gps/ene/type User
/gps/hist/type energy

        """
        for e,f in zip(energy_bins,fluence_list):
            macro_file+=f"\n/gps/hist/point {e} {f}"
        final_macro=macro_file+f"""
        \n
/run/beamOn {beamon}
        """
    
    return final_macro
        

        
