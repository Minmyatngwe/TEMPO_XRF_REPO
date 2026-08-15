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
    detector_collimatory_elevation_angle,detector_elevation_angle,source_to_tube_collimatory,tube_collimatory_radius,
    energy_bins=None,fluence_list=None,):
    
    if detector_collimatory_composition_is_custom:
        detector_collimatory_composition_is_custom="true"
    else:
        detector_collimatory_composition_is_custom="false"
    if detector_collimatory_is_enable:
        detector_collimatory_is_enable='true'
    else:
        detector_collimatory_is_enable='false'
    
    
    
    macro_file=f"""
    /xrf/sampleMaterial G4_Zn
    /xrf/sampleSize 5 5 0.005 mm
    /xrf/fileName {filepath}
    /xrf/incidentAngle {incident_angle}
    /xrf/sourceDistance {source_to_sample}
    /xrf/detectorthickness {detector_thickness}
    /xrf/detectorArea {detector_active_area}
    /xrf/detectorDistance {detector_to_sample_distance}
    /xrf/takeoffAngle {takeoff_angle}
    /xrf/detectorElevationAngle {detector_elevation_angle}
    /xrf/worldmat {world_material}
    /xrf/sampleMaterialDensity {sample_density}
    /xrf/sampleMaterialIsCustom {sampleMaterialIsCustom}
    /xrf/focalspotdiameter {focal_spot_diameter}
/xrf/sampleMaterialDensity 8.49
/xrf/addSampleElement Cu 0.615
/xrf/addSampleElement Zn 0.353
/xrf/addSampleElement Pb 0.0271
/xrf/addSampleElement Fe 0.0017
/xrf/addSampleElement Sn 0.0015
/xrf/addSampleElement Ni 0.00059
/xrf/addSampleElement Mn 0.00001
/xrf/tubeToCollimatoryDistance {source_to_tube_collimatory}
/xrf/sourceCollimatoryDiameter {tube_collimatory_radius*2}
/xrf/detectorCollimatorIsEnabled {detector_collimatory_is_enable}
/xrf/detectorCollimatorIsCustom {detector_collimatory_composition_is_custom}
/xrf/detectorCollimatorMaterial {detector_collimatory_material}
/xrf/sampleToDetectorCollimatorDistance {sample_detector_collimatory_dsitance}
/xrf/detectorCollimatoryAngleFromSample {sample_detector_collimatory_angle}
/xrf/detectorCollimatorDensity {sample_detector_collimatory_density}
/xrf/detectorCollimatorThickness {detector_collimatory_thickness}
/xrf/detectorCollimatorOuterRadius {detector_collimatory_outer_radius}
/xrf/detectorCollimatorInnerRadius {detector_collimatory_inner_radius}
/xrf/detectorCollimatorElevationAngle  {detector_collimatory_elevation_angle}

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
/run/printProgress 10000

/run/beamOn {beamon}
        """
    
    return final_macro
        

        
    