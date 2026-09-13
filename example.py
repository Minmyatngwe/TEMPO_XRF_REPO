
from roboaixrf import XRFConfigure,Material,Placement,Geometry,XRayTube,Composition,Collimator,Filter,Sample,Detector,Housing,Internal_mask,TubeWindow,TubePlacement,RoboAiXrfSimulation
world = XRFConfigure(
    world_material=Material.geant4("G4_Galactic"),
    world_size_x_mm=300,
    world_size_y_mm=300,
    world_size_z_mm=300,
)


# ============================================================
# 2. SAMPLE
# ============================================================

sample_geometry = Geometry.rectangular(
    width_mm=10.0,
    height_mm=10.0,
    thickness_mm=0.1,
)

sample_material = Material.geant4("G4_Fe")

sample = Sample(
    name="sample",
    geometry=sample_geometry,
    material=sample_material,
)

world.add(sample)


# ============================================================
# 3. DETECTOR
# ============================================================

detector_geometry = Geometry.circular(
    radius_mm=4.0,
    thickness_mm=1,
)

detector_material = Material.geant4(
    "G4_Si"
)

detector_placement = Placement.face_sample(
    distance_mm=17.0,
    elevation_deg=90,
    azimuth_deg=50,
)

detector = Detector(
    name="detector",
    geometry=detector_geometry,
    material=detector_material,
    placement=detector_placement,
)

world.add(detector)


# ============================================================
# 4. X-RAY TUBE
# ============================================================

tube_placement = TubePlacement(
    focal_spot_to_sample_distance_mm=140.0,
    tube_window_to_sample_distance_mm=130.0,
    elevation_deg=90.0,
    azimuth_deg=90.0,
)

tube = XRayTube.create(
    name="xrftube",

    current_ma=1.0,
    voltage_kv=50.0,

    anode_angle_deg=15.0,   
    anode_symbol="W",

    focal_spot_diameter_mm=0.05,

    tube_collimator_radius_mm=0.15,

    tube_window_to_virtual_collimator_distance_mm=100,

    tube_placement=tube_placement,
)


# ============================================================
# 5. X-RAY TUBE WINDOW
# ============================================================

tube_window = TubeWindow(
    name="tube_window",

    material=Material.geant4(
        "G4_Be"
    ),

    thickness_mm=0.001,
)

tube.set_window(
    tube_window
)


# ============================================================
# 6. GEANT4 TUBE FILTER 1
#    5 mm in front of tube window
# ============================================================

tube_al_filter = Filter(
    name="tube_Al_filter",

    geometry=Geometry.circular(
        radius_mm=5.0,
        thickness_mm=0.5,
    ),

    material=Material.geant4(
        "G4_Al"
    ),

    placement=Placement.in_front_of_tube_window(
        distance_mm=5.0,
    ),
)


# ============================================================
# 7. GEANT4 TUBE FILTER 2
#    7 mm in front of tube window
# ============================================================

tube_cu_filter = Filter(
    name="tube_Cu_filter",

    geometry=Geometry.circular(
        radius_mm=5.0,
        thickness_mm=0.1,
    ),

    material=Material.geant4(
        "G4_Cu"
    ),

    placement=Placement.in_front_of_tube_window(
        distance_mm=7.0,
    ),
)

# tube.add_filter_geant4(
#     tube_cu_filter
# )
# tube.add_filter_geant4(
#     tube_al_filter
# )



# ============================================================
# 8. SPEKPY FILTERS
# ============================================================

tube.add_filter_spekpy(
    {
        "element": "Al",
        "thickness_mm": 0.5,
    }
)

# tube.add_filter_spekpy(
#     {
#         "element": "Cu",
#         "thickness_mm": 0.1,
#     }
# )


# ============================================================
# 9. ADD X-RAY TUBE
# ============================================================

world.add(tube)


# ============================================================
# 10. DETECTOR HOUSING
#
# detector
#    ↓
# 1 mm vacuum clearance
#    ↓
# 0.5 mm W cavity wall
#    ↓
# 1 mm Al housing wall
# ============================================================

housing_geometry = (
    Geometry.detector_housing_circular_aperture(
        aperture_radius_mm=5,

        detector_clearance_mm=2,

        housing_wall_thickness_mm=1.0,
        cavity_wall_thickness_mm=1,
    )
)

housing_material = Material.geant4(
    "G4_Al"
)

cavity_wall_material = Material.geant4(
    "G4_W"
)

housing = Housing.create(
    name="detector_housing",

    geometry=housing_geometry,

    housing_material=housing_material,

    cavity_material=cavity_wall_material,

    inner_cavity_medium_material=Material.geant4("G4_Galactic"),
    window_material=Material.geant4("G4_Be"),
    window_thickness_mm=0.01
)



# ============================================================
# 11. INTERNAL MASK 1
#
# Inside detector housing
# Closest mask to detector
# ============================================================

ti_mask = Internal_mask(
    name="Ti_mask",

    geometry=Geometry.circular_aperture(
        aperture_radius_mm=3.09,
        outer_radius_mm=4,
        length_mm=0.025,
    ),

    material=Material.geant4(
        "G4_Ti"
    ),

    placement=Placement.in_front_detector(
        distance_mm=0.10,
    ),
)



# ============================================================
# 12. INTERNAL MASK 2
# ============================================================

al_mask = Internal_mask(
    name="Al_mask",

    geometry=Geometry.circular_aperture(
        aperture_radius_mm=3.09,
        outer_radius_mm=4.0,
        length_mm=0.075,
    ),

    material=Material.geant4(
        "G4_Al"
    ),

    placement=Placement.in_front_detector(
        distance_mm=0.30,
    ),
)


# ============================================================
# 13. INTERNAL MASK 3
# ============================================================

w_mask = Internal_mask(
    name="W_mask",

    geometry=Geometry.circular_aperture(
        aperture_radius_mm=3.09,
        outer_radius_mm=4.0,
        length_mm=0.10,
    ),

    material=Material.geant4(
        "G4_W"
    ),

    placement=Placement.in_front_detector(
        distance_mm=0.50,
    ),
)
detector.add_housing(
    housing
)
detector.add_internal_mask(
    w_mask
)

detector.add_internal_mask(
    al_mask
)

detector.add_internal_mask(
    ti_mask
)


# ============================================================
# 14. DETECTOR FILTER
#
# Housing reaches approximately:
#
# detector surface
# + 1.0 mm clearance
# + 0.5 mm cavity wall
# + 1.0 mm housing wall
#
# = 2.5 mm
#
# Therefore start external components after that.
# ============================================================

detector_filter = Filter(
    name="detector_Al_filter",

    geometry=Geometry.circular(
        radius_mm=5.0,
        thickness_mm=0.05,
    ),

    material=Material.geant4(
        "G4_Al"
    ),

    placement=Placement.in_front_detector(
        distance_mm=3.0,
    ),
)



# ============================================================
# 15. DETECTOR COLLIMATOR 1
#    Circular aperture
# ============================================================

detector_collimator = Collimator(
    name="detector_collimator",

    geometry=Geometry.circular_aperture(
        aperture_radius_mm=3.0,
        outer_radius_mm=5.0,
        length_mm=1.0,
    ),

    material=Material.geant4(
        "G4_W"
    ),

    placement=Placement.in_front_detector(
        distance_mm=4.0,
    ),
)



# ============================================================
# 16. CUSTOM MATERIAL FOR SECOND COLLIMATOR
# ============================================================

collimator_material = Material.custom_mat(
    density_g_cm3=9.0,

    compositions=[
        Composition(
            element="Cu",
            mass_fraction=0.50,
        ),
        Composition(
            element="W",
            mass_fraction=0.50,
        ),
    ],

    material_name="CuWCollimator",
)


# ============================================================
# 17. DETECTOR COLLIMATOR 2
#    Rectangular aperture
# ============================================================

detector_collimator_2 = Collimator(
    name="detector_collimator_2",

    geometry=Geometry.rectangular_aperture(
        aperture_width_mm=5.0,
        aperture_height_mm=5.0,

        outer_width_mm=8.0,
        outer_height_mm=8.0,

        length_mm=0.5,
    ),

    material=collimator_material,

    placement=Placement.in_front_detector(
        distance_mm=6.0,
    ),
)

# detector.add_collimator(
#     collimator=detector_collimator_2
# )


# detector.add_collimator(
#     collimator=detector_collimator
# )
# detector.add_filter(
#     detector_filter
# )
# ============================================================
# 18. CREATE SIMULATION
# ============================================================

simulation = RoboAiXrfSimulation(
    config=world,
    config_path="./runs/full_xrf_example",
)


# ============================================================
# 19. COMPILE CONFIG
# ============================================================

simulation.compile()


# ============================================================
# 20. OPTIONAL BROWSER VISUALIZATION
# ============================================================

simulation.show_vis(
    beam_on=100,
    number_of_thread=1,
)


# # ============================================================
# # 21. OPTIONAL FULL RUN
# # ============================================================

simulation.run(
    beam_on=10000000,
    number_of_thread=15,
    print_display=100_000,
)

simulation.detector_noise(
    current=1,
    live_time=30,
    fwhm=140,
    fwhm_energy_kev=5.9,
    pile_up_window_us=0.1,
    detector_gain_kev=0.025,
    detector_zero_offset=0
)