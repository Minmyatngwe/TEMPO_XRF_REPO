#include "simulationConfig.hh"
namespace
{
    struct ParsedGeometry
    {
        G4String shape;

        G4double width = 0.0 * mm;
        G4double height = 0.0 * mm;
        G4double thickness = 0.0 * mm;

        G4double innerRadius = 0.0 * mm;
        G4double outerRadius = 0.0 * mm;
        G4double radius = 0.0 * mm;


        G4double outerWidth = 0.0 * mm;
        G4double outerHeight = 0.0 * mm;
        G4double apertureWidth = 0.0 * mm;
        G4double apertureHeight = 0.0 * mm;
        G4double apertureRadius = 0.0 * mm;
        G4double length = 0.0 * mm;
    };

    struct ParsedMaterial
    {
        G4String type;
        G4String name;

        G4double density = 0.0 * g / cm3;

        std::vector<MaterialComponent> components;
    };
    struct ParsedPlacement
    {
        G4double distanceFromSample = 0.0 * mm;
        G4double elevationAngle = 0.0 * deg;
        G4double azimuthAngle = 0.0 * deg;

        G4String orientationType;

        G4double xRotation = 0.0 * deg;
        G4double yRotation = 0.0 * deg;
        G4double zRotation = 0.0 * deg;
    };
    ParsedGeometry ParseGeometry(
        const json & geometryJson
    ){
        ParsedGeometry geometry ;
        geometry.shape=geometryJson.at("shape").get<G4String>();
            geometry.width =
            geometryJson.value(
                "width_mm",
                0.0
            ) * mm;

        geometry.height =
            geometryJson.value(
                "height_mm",
                0.0
            ) * mm;
        geometry.thickness =
            geometryJson.value(
                "thickness_mm",
                0.0
            ) * mm;

        geometry.innerRadius =
            geometryJson.value(
                "inner_radius_mm",
                0.0
            ) * mm;

        geometry.outerRadius =
            geometryJson.value(
                "outer_radius_mm",
                0.0
            ) * mm;

        geometry.radius =
            geometryJson.value(
                "radius_mm",
                0.0
            ) * mm;
        geometry.outerWidth =
            geometryJson.value("outer_width_mm", 0.0) * mm;

        geometry.outerHeight =
            geometryJson.value("outer_height_mm", 0.0) * mm;

        geometry.apertureWidth =
            geometryJson.value("aperture_width_mm", 0.0) * mm;

        geometry.apertureHeight =
            geometryJson.value("aperture_height_mm", 0.0) * mm;

        geometry.apertureRadius =
            geometryJson.value("aperture_radius_mm", 0.0) * mm;

        geometry.length =
            geometryJson.value("length_mm", 0.0) * mm;

        return geometry;
    }

    ParsedMaterial ParseMaterial(
        const json & materialJson
    ){
        ParsedMaterial material;
        material.type=materialJson.at("material_type").get<G4String>();
        material.name=materialJson.at("material_name").get<G4String>();

        if (material.type=="custom"){
            material.density=materialJson.at("density_g_cm3").get<G4double>()*g/cm3;

            for(const auto & composition: materialJson.at("composition")){

                MaterialComponent materialComposition(
                    composition.at("element").get<G4String>(),
                composition.at("mass_fraction").get<G4double>()
                ) ;
                
                material.components.push_back(materialComposition);
            }
        }
        return material;

    }

    ParsedPlacement ParsePlacement(
        const json & placementJson,
        G4String componentType="COMPONENT"
    ){
        ParsedPlacement placement ;
        const auto& positionJson =placementJson.at("position");

        placement.distanceFromSample=positionJson.at("distance_mm").get<G4double>()*mm;
        if(componentType!="internal mask"){
            placement.elevationAngle=positionJson.at("elevation_deg").get<G4double>()*deg;
            placement.azimuthAngle=positionJson.at("azimuth_deg").get<G4double>()*deg;


            const auto & orientationJson=placementJson.at("orientation");

            placement.orientationType=orientationJson.at("mode").get<G4String>();

            const auto & rotationJson=orientationJson.at("rotation_deg");
            placement.xRotation=rotationJson.at("x").get<G4double>()*deg;
            placement.yRotation=rotationJson.at("y").get<G4double>()*deg;
            placement.zRotation=rotationJson.at("z").get<G4double>()*deg;

        }
        return placement;
    }
    void ApplyGeometry(
        ComponentConfig& component,
        const ParsedGeometry& geometry
    )
    {
        component.shape = geometry.shape;

        component.width = geometry.width;
        component.height = geometry.height;
        component.thickness = geometry.thickness;

        component.innerRadius = geometry.innerRadius;
        component.outerRadius = geometry.outerRadius;

        component.radius = geometry.radius;
        component.apertureRadius = geometry.apertureRadius;
        component.length = geometry.length;
        component.outerWidth = geometry.outerWidth;
        component.outerHeight = geometry.outerHeight;

        component.apertureWidth = geometry.apertureWidth;
        component.apertureHeight = geometry.apertureHeight;
    }


    void ApplyMaterial(
        ComponentConfig& component,
        ParsedMaterial material
    )
    {
        component.materialType = material.type;
        component.materialName = material.name;
        component.density = material.density;

        component.material = std::move(
            material.components
        );
    }


    void ApplyPlacement(
        ComponentConfig& component,
        const ParsedPlacement& placement
    )
    {
        component.distanceFromSample =
            placement.distanceFromSample;

        component.elevationAngle =
            placement.elevationAngle;

        component.azimuthAngle =
            placement.azimuthAngle;

        component.orientationType =
            placement.orientationType;

        component.xRotation =
            placement.xRotation;

        component.yRotation =
            placement.yRotation;

        component.zRotation =
            placement.zRotation;
    }

}
void SimulationConfig::LoadFromJson(const nlohmann::json& jsonConfig){

    //xray tube
try{
    const auto &xrayTube=jsonConfig.at("xray_tube");

    focalspotdiameter=xrayTube.at("focal_spot_mm").get<G4double>()*mm;
    sampleToFocalSpot=xrayTube.at("sample_to_focal_spot_mm").get<G4double>()*mm;
    xrayTubeInternalMedium=xrayTube.at("internal_medium").get<G4String>();
    const auto & windowJson=xrayTube.at("window");
    xrayTubeBeWindowMat=windowJson.at("material").get<G4String>();
    xrayTubeWindowThickness=windowJson.at("thickness_mm").get<G4double>()*mm;


    const auto& geometryConfig = jsonConfig.at("geometry");


    //world

    const auto & worldJson=geometryConfig.at("world");
    worldMaterial=worldJson.at("material").get<G4String>();

    worldLength.setX(
        worldJson.at("world_x_axis_length_mm").get<G4double>() * mm
    );

    worldLength.setY(
        worldJson.at("world_y_axis_length_mm").get<G4double>() * mm
    );

    worldLength.setZ(
        worldJson.at("world_z_axis_length_mm").get<G4double>() * mm
    );    



    const auto& tube = geometryConfig.at("tube");
    const auto &tubeFilter=tube.at("filters");
    tubeFilterEngine=tubeFilter.at("filter_engine").get<G4String>();
    isTubeFilterUse=tubeFilter.at("enabled").get<G4bool>();

    if (isTubeFilterUse &&tubeFilterEngine=="geant4"){
        
        const auto & tubeFilterJson=tubeFilter.at("filters");
        ParseComponentConfig(tubeFilterJson,tubeFilters);
    }

        //sample

    const auto & sampleJson=geometryConfig.at("sample");
    auto samplegeometry=ParseGeometry(
        sampleJson.at("geometry")
    );
    sampleMaterialShape=samplegeometry.shape;
    sampleWidth=samplegeometry.width;
    sampleHeight=samplegeometry.height;
    sampleThickness=samplegeometry.thickness;
    sampleInnerRadius=samplegeometry.innerRadius;
    sampleOuterRadius=samplegeometry.outerRadius;
    sampleRadius=samplegeometry.radius;


    const auto & sampleMaterialJson=sampleJson.at("material");

    auto  sampleMaterial=ParseMaterial(
        sampleMaterialJson
    );
    sampleMaterialType=sampleMaterial.type;
    sampleMaterialName=sampleMaterial.name;
    sampleMaterialDensity=sampleMaterial.density;
    sampleMaterialComponents=std::move(sampleMaterial.components);

    sampleToTubeExitDistance=sampleJson.at("sample_to_tube_distance_mm").get<G4double>()*mm;
    
    sourceIncidentAzimuthDeg=sampleJson.at("source_incident_azimuth_deg").get<G4double>()*deg;
    sourceElevationDeg=sampleJson.at("source_elevation_deg").get<G4double>()*deg;
    sampleToTubeCollimatorDistance=sampleJson.at("sample_to_tube_collimator_distance_mm").get<G4double>()*mm;
    sourceCollimatorRadius=sampleJson.at("tube_collimator_radius_mm").get<G4double>()*mm;

    const auto & sampleRotationJson=sampleJson.at("sample_rotation_deg");

    sampleRotationX=sampleRotationJson.at("x").get<G4double>()*deg;
    sampleRotationY=sampleRotationJson.at("y").get<G4double>()*deg;
    sampleRotationZ=sampleRotationJson.at("z").get<G4double>()*deg;


    //detector

    const auto & detectorJson=geometryConfig.at("detector");

    const auto & detectorActiveVolumeJson=detectorJson.at("active_volume");

    auto activeVolumeGeometry=ParseGeometry(
        detectorActiveVolumeJson.at("geometry")
    );

    detectorActiveVolumeShape=activeVolumeGeometry.shape;
    detectorWidth=activeVolumeGeometry.width;
    detectorHeight=activeVolumeGeometry.height;
    detectorThickness=activeVolumeGeometry.thickness;
    detectorInnerRadius=activeVolumeGeometry.innerRadius;
    detectorOuterRadius=activeVolumeGeometry.outerRadius;
    detectorRadius=activeVolumeGeometry.radius;

    auto activeVolumeMaterial=ParseMaterial(
        detectorActiveVolumeJson.at("material")
    );

    detectorMaterialType=activeVolumeMaterial.type;
    detectorMaterialName=activeVolumeMaterial.name;
    detectorDensity=activeVolumeMaterial.density;
    detectorMaterialComposition=std::move(activeVolumeMaterial.components);

    auto activeVolumePlacement=ParsePlacement(
        detectorActiveVolumeJson.at("placement")
    );
    
    detectorDistanceFromSample=activeVolumePlacement.distanceFromSample;
    detectorelevationAngle=activeVolumePlacement.elevationAngle;
    detectorazimuthAngle=activeVolumePlacement.azimuthAngle;

    detectorOrientationType=activeVolumePlacement.orientationType;

    detectorXRotation=activeVolumePlacement.xRotation;
    detectorYRotation=activeVolumePlacement.yRotation;
    detectorZRotation=activeVolumePlacement.zRotation;

    //detector housing

    const auto& detectorHousingJson =
        detectorJson.at("housing");

    isDetectorHousingUse =
        detectorHousingJson.value(
            "enabled",
            false
        );


    if (isDetectorHousingUse) {

        const auto& detectorHousingGeometryJson =detectorHousingJson.at("geometry");
        detectorHousingShape =detectorHousingGeometryJson.value("housing_shape","Rectangular housing");

        detectorHousingSideGap =
            detectorHousingGeometryJson
                .at("side_gap_mm")
                .get<G4double>() * mm;


        detectorHousingFrontGap =
            detectorHousingGeometryJson
                .at("front_gap_mm")
                .get<G4double>() * mm;

        detectorHousingBackGap =
            detectorHousingGeometryJson
                .at("back_gap_mm")
                .get<G4double>() * mm;

        detectorHousingWallThickness =
            detectorHousingGeometryJson
                .at("wall_thickness_mm")
                .get<G4double>() * mm;

        detectorHousingApertureShape =
            detectorHousingGeometryJson
                .at("aperture_shape")
                .get<G4String>();

        if (detectorHousingApertureShape =="circular") {
            detectorHousingApertureRadius =
                detectorHousingGeometryJson
                    .at("aperture_radius_mm")
                    .get<G4double>() * mm;
        }

        else if (
            detectorHousingApertureShape ==
            "rectangular"
        ) {
            detectorHousingApertureWidth =
                detectorHousingGeometryJson
                    .at("aperture_width_mm")
                    .get<G4double>() * mm;

                detectorHousingApertureHeight =
                detectorHousingGeometryJson
                    .at("aperture_height_mm")
                    .get<G4double>() * mm;
        }
        else {
            G4Exception(
                "SimulationConfig::LoadFromJson",
                "InvalidHousingAperture",
                FatalException,
                (
                    "Unsupported detector housing aperture: " +
                    detectorHousingApertureShape
                ).c_str()
            );

    }

        //housing material 
        const auto& detectorHousingMaterialJson =detectorHousingJson.at("material");
        auto detectorHousingMaterial=ParseMaterial(detectorHousingMaterialJson);
        detectorHousingMaterialType=detectorHousingMaterial.type;
        detectorHousingMaterialName=detectorHousingMaterial.name;
        detectorHousingDensity=detectorHousingMaterial.density;
        detectorHousingMaterialComposition=std::move(detectorHousingMaterial.components);

        //housing cavity

        const auto& detectorHousingCavityJson =detectorHousingJson.at("cavity");

        detectorHousingCavityInternalMaterialName =detectorHousingCavityJson.value("medium_material","G4_Galactic");
        detectorHousingCavityWallThickness=detectorHousingCavityJson.at("cavity_wall_thickness_mm").get<G4double>()*mm;


        auto detectorHousingCavityMaterial=ParseMaterial(detectorHousingCavityJson.at("material"));
        detectorHousingCavityMaterialType=detectorHousingCavityMaterial.type;
        detectorHousingCavityMaterialName=detectorHousingCavityMaterial.name;
        detectorHousingCavityDensity=detectorHousingCavityMaterial.density;
        detectorHousingCavityMaterialComposition=std::move(detectorHousingCavityMaterial.components);
        


        //housing entrance window

        const auto& detectorHousingWindowJson =detectorHousingJson.at("window");


        detectorHousingWindowThickness =detectorHousingWindowJson.at("thickness_mm").get<G4double>() * mm;
        const auto& detectorHousingWindowMaterialJson =detectorHousingWindowJson.at("material");

        auto detectorHousingWindowMaterial=ParseMaterial(
            detectorHousingWindowMaterialJson
        );
        detectorHousingWindowMaterialType=detectorHousingWindowMaterial.type;
        detectorHousingWindowMaterialName=detectorHousingWindowMaterial.name;
        detectorHousingWindowDensity=detectorHousingWindowMaterial.density;
        detectorHousingWindowComposition=std::move(detectorHousingWindowMaterial.components); 
    }




    //detector collimator


    const auto & detectorApetureJson=detectorJson.at("aperture");
    isDetectorApertureUse=detectorApetureJson.at("enabled").get<G4bool>();

    if (isDetectorApertureUse){

        const auto &detectorCollimatorJson=detectorApetureJson.at("collimator");
        isDetectorCollimatorUse=detectorCollimatorJson.at("enabled").get<G4bool>();
        if(isDetectorCollimatorUse){
            ParseComponentConfig(
                detectorCollimatorJson.at("components"),
                detectorCollimators

            );
        }

        const auto &detectirInternalMaskJson=detectorApetureJson.at("internal_mask");
        isDetectorInternalMaskUse=detectirInternalMaskJson.at("enabled").get<G4bool>();
        if(isDetectorInternalMaskUse){
            ParseComponentConfig(
                detectirInternalMaskJson.at("components"),
                detectorInternalMasks,
                "internal mask"
                
            );

        }


    }


    //detector filter
    const auto & detectorFilterJson=detectorJson.at("detector_layers");

    isDetectorFilterUse=detectorFilterJson.at("enabled").get<G4bool>();

    if (isDetectorFilterUse){

        ParseComponentConfig(
            detectorFilterJson.at("detector_filters"),
            detectorFilters

        );
    }

    // Physics

    const auto& physicsJson =
        jsonConfig.at("physics");


    // Atomic de-excitation
    const auto& atomicDeexcitationJson =
        physicsJson.at("atomic_deexcitation");

    isFluorescenceUse =
        atomicDeexcitationJson
            .at("fluorescence")
            .get<G4bool>();

    isAugerUse =
        atomicDeexcitationJson
            .at("auger")
            .get<G4bool>();

    isPixeUse =
        atomicDeexcitationJson
            .at("pixe")
            .get<G4bool>();

    isIgnoreCutUse =
        atomicDeexcitationJson
            .at("ignore_deexcitation_cut")
            .get<G4bool>();


    // Secondary splitting
    const auto& secondarySplittingJson =
        physicsJson.at("secondary_splitting");

    isSecondarySplittingUse =
        secondarySplittingJson
            .at("enabled")
            .get<G4bool>();


    photoelectricFactor =
        secondarySplittingJson
            .at("photoelectric_split_factor")
            .get<G4int>();

    comptFactor =
        secondarySplittingJson
            .at("compton_split_factor")
            .get<G4int>();

    rayleighFactor =
        secondarySplittingJson
            .at("rayleigh_split_factor")
            .get<G4int>();

    maximumEnergy =
        secondarySplittingJson
            .at("maximum_energy_keV")
            .get<G4double>() * keV;


    // Interaction biasing
    const auto& interactionBiasingJson =
        physicsJson.at("interaction_biasing");

    isInteractionBiasingUse =
        interactionBiasingJson
            .at("enabled")
            .get<G4bool>();


    // SampleRegion production cuts
    const auto& sampleRegionCutsJson =
        physicsJson.at("sample_region_cuts_mm");

    gammaCut =
        sampleRegionCutsJson
            .at("gamma")
            .get<G4double>() * mm;

    electronCut =
        sampleRegionCutsJson
            .at("electron")
            .get<G4double>() * mm;

    positronCut =
        sampleRegionCutsJson
            .at("positron")
            .get<G4double>() * mm;

    protonCut =
        sampleRegionCutsJson
            .at("proton")
            .get<G4double>() * mm;
    
    fluDatasetName=physicsJson.at("flu_dataset").at("flu_dataset").get<G4String>();



}

catch (const nlohmann::json::exception& e) {
        G4String errorMsg = "JSON parsing failed! Check your Streamlit config.\n";
        errorMsg += "Nlohmann Error: ";
        errorMsg += e.what();
        
        G4Exception(
            "SimulationConfig::LoadFromJson",
            "ConfigParseError",
            FatalException,
            errorMsg.c_str()
        );
    }







}



void SimulationConfig::ParseComponentConfig(
    const nlohmann::json& componentJson,
    std::vector<ComponentConfig>& componentVector,
    G4String componentType
)
{
        for(const auto & componentJsonItem : componentJson){
            ComponentConfig component;
            component.name=componentJsonItem.at("name").get<G4String>();
            const auto & geometryJson=componentJsonItem.at("geometry");
            ApplyGeometry(component,ParseGeometry(geometryJson));

            const auto & materialJson=componentJsonItem.at("material");
            ApplyMaterial(component,ParseMaterial(materialJson));

            const auto & placementJson=componentJsonItem.at("placement");
            
            ApplyPlacement(component,ParsePlacement(placementJson,componentType));

    
            componentVector.push_back(component);
    
        }
}


void SimulationConfig::Print() const
{
    // ============================================================
    // Helper functions
    // ============================================================

    const auto BoolText = [](G4bool value) -> const char*
    {
        return value ? "true" : "false";
    };


    const auto PrintSeparator = []()
    {
        G4cout
            << "============================================================"
            << G4endl;
    };


    const auto PrintSection = [](const G4String& title)
    {
        G4cout << G4endl;
        G4cout << title << G4endl;
        G4cout
            << "------------------------------------------------------------"
            << G4endl;
    };


    const auto PrintComposition =
        [](
            const std::vector<MaterialComponent>& components
        )
    {
        G4cout
            << "Number of material components: "
            << components.size()
            << G4endl;

        if (components.empty()) {
            G4cout << "Composition: none" << G4endl;
            return;
        }

        G4cout << "Composition:" << G4endl;

        for (
            std::size_t i = 0;
            i < components.size();
            ++i
        ) {
            G4cout
                << "  [" << i << "] "
                << components[i].elementName
                << " = "
                << components[i].fraction
                << G4endl;
        }
    };


    const auto PrintMaterial =
        [&PrintComposition](
            const G4String& materialType,
            const G4String& materialName,
            G4double density,
            const std::vector<MaterialComponent>& composition
        )
    {
        G4cout
            << "Material type: "
            << materialType
            << G4endl;

        G4cout
            << "Material name: "
            << materialName
            << G4endl;

        G4cout
            << "Density: "
            << density / (g / cm3)
            << " g/cm3"
            << G4endl;

        PrintComposition(composition);
    };


    const auto PrintVector =
        [](
            const G4String& label,
            const G4ThreeVector& vector
        )
    {
        G4cout
            << label
            << ": ("
            << vector.x() / mm
            << ", "
            << vector.y() / mm
            << ", "
            << vector.z() / mm
            << ") mm"
            << G4endl;
    };


    const auto PrintComponent =
        [&PrintMaterial](
            const ComponentConfig& component,
            std::size_t index
        )
    {
        G4cout << G4endl;

        G4cout
            << "Component [" << index << "]"
            << G4endl;

        G4cout
            << ".............................."
            << G4endl;

        G4cout
            << "Name: "
            << component.name
            << G4endl;

        G4cout
            << "Shape: "
            << component.shape
            << G4endl;


        // Geometry
        G4cout << "Geometry:" << G4endl;

        G4cout
            << "  Width: "
            << component.width / mm
            << " mm"
            << G4endl;

        G4cout
            << "  Height: "
            << component.height / mm
            << " mm"
            << G4endl;

        G4cout
            << "  Thickness: "
            << component.thickness / mm
            << " mm"
            << G4endl;

        G4cout
            << "  Radius: "
            << component.radius / mm
            << " mm"
            << G4endl;

        G4cout
            << "  Inner radius: "
            << component.innerRadius / mm
            << " mm"
            << G4endl;

        G4cout
            << "  Outer radius: "
            << component.outerRadius / mm
            << " mm"
            << G4endl;

G4cout
    << "  Aperture radius: "
    << component.apertureRadius / mm
    << " mm" << G4endl;

G4cout
    << "  Length: "
    << component.length / mm
    << " mm" << G4endl;
        // Material
        G4cout << "Material:" << G4endl;

        PrintMaterial(
            component.materialType,
            component.materialName,
            component.density,
            component.material
        );


        // Placement
        G4cout << "Placement:" << G4endl;

        G4cout
            << "  Distance from sample: "
            << component.distanceFromSample / mm
            << " mm"
            << G4endl;

        G4cout
            << "  Elevation angle: "
            << component.elevationAngle / deg
            << " deg"
            << G4endl;

        G4cout
            << "  Azimuth angle: "
            << component.azimuthAngle / deg
            << " deg"
            << G4endl;


        // Orientation
        G4cout << "Orientation:" << G4endl;

        G4cout
            << "  Orientation type: "
            << component.orientationType
            << G4endl;

        G4cout
            << "  X rotation: "
            << component.xRotation / deg
            << " deg"
            << G4endl;

        G4cout
            << "  Y rotation: "
            << component.yRotation / deg
            << " deg"
            << G4endl;

        G4cout
            << "  Z rotation: "
            << component.zRotation / deg
            << " deg"
            << G4endl;
    };


    const auto PrintComponentCollection =
        [&PrintComponent](
            const G4String& title,
            G4bool enabled,
            const std::vector<ComponentConfig>& components
        )
    {
        G4cout << G4endl;
        G4cout << title << G4endl;

        G4cout
            << "------------------------------------------------------------"
            << G4endl;

        G4cout
            << "Enabled: "
            << (enabled ? "true" : "false")
            << G4endl;

        G4cout
            << "Number of components: "
            << components.size()
            << G4endl;

        for (
            std::size_t i = 0;
            i < components.size();
            ++i
        ) {
            PrintComponent(
                components[i],
                i
            );
        }
    };


    // ============================================================
    // Header
    // ============================================================

    G4cout << G4endl;

    PrintSeparator();

    G4cout
        << "                 SIMULATION CONFIGURATION"
        << G4endl;

    PrintSeparator();


    // ============================================================
    // WORLD / GENERAL
    // ============================================================

    PrintSection("WORLD / GENERAL");

    G4cout
        << "World material: "
        << worldMaterial
        << G4endl;

    PrintVector(
        "World length",
        worldLength
    );

    G4cout
        << "Output file name: "
        << outputFileName
        << G4endl;


    // ============================================================
    // X-RAY TUBE
    // ============================================================

    PrintSection("X-RAY TUBE");

    G4cout
        << "Focal spot diameter: "
        << focalspotdiameter / mm
        << " mm"
        << G4endl;

    G4cout
        << "Sample to focal spot distance: "
        << sampleToFocalSpot / mm
        << " mm"
        << G4endl;

    G4cout
        << "X-ray tube internal medium: "
        << xrayTubeInternalMedium
        << G4endl;

    PrintVector(
        "Source position",
        sourcePosition
    );

    G4cout
        << "X-ray tube window material: "
        << xrayTubeBeWindowMat
        << G4endl;

    G4cout
        << "X-ray tube window thickness: "
        << xrayTubeWindowThickness / mm
        << " mm"
        << G4endl;


    // ============================================================
    // X-RAY TUBE FILTERS
    // ============================================================

    G4cout << G4endl;

    G4cout
        << "Tube filter enabled: "
        << BoolText(isTubeFilterUse)
        << G4endl;

    G4cout
        << "Tube filter engine: "
        << tubeFilterEngine
        << G4endl;

    PrintComponentCollection(
        "X-RAY TUBE FILTER COMPONENTS",
        isTubeFilterUse,
        tubeFilters
    );


    // ============================================================
    // SAMPLE
    // ============================================================

    PrintSection("SAMPLE");

    G4cout
        << "Shape: "
        << sampleMaterialShape
        << G4endl;


    // Geometry
    G4cout << "Geometry:" << G4endl;

    G4cout
        << "  Width: "
        << sampleWidth / mm
        << " mm"
        << G4endl;

    G4cout
        << "  Height: "
        << sampleHeight / mm
        << " mm"
        << G4endl;

    G4cout
        << "  Thickness: "
        << sampleThickness / mm
        << " mm"
        << G4endl;

    G4cout
        << "  Inner radius: "
        << sampleInnerRadius / mm
        << " mm"
        << G4endl;

    G4cout
        << "  Outer radius: "
        << sampleOuterRadius / mm
        << " mm"
        << G4endl;

    G4cout
        << "  Radius: "
        << sampleRadius / mm
        << " mm"
        << G4endl;


    // Material
    G4cout << "Material:" << G4endl;

    PrintMaterial(
        sampleMaterialType,
        sampleMaterialName,
        sampleMaterialDensity,
        sampleMaterialComponents
    );


    G4cout
        << "G4Material pointer set: "
        << BoolText(sampleMat != nullptr)
        << G4endl;

    if (sampleMat != nullptr) {
        G4cout
            << "G4Material resolved name: "
            << sampleMat->GetName()
            << G4endl;
    }


    // Rotation
    G4cout << "Sample rotation:" << G4endl;

    G4cout
        << "  X: "
        << sampleRotationX / deg
        << " deg"
        << G4endl;

    G4cout
        << "  Y: "
        << sampleRotationY / deg
        << " deg"
        << G4endl;

    G4cout
        << "  Z: "
        << sampleRotationZ / deg
        << " deg"
        << G4endl;


    // SOURCE / TUBE COLLIMATOR

    PrintSection("SOURCE / TUBE COLLIMATOR");

    G4cout
        << "Sample to tube exit distance: "
        << sampleToTubeExitDistance / mm
        << " mm"
        << G4endl;

    G4cout
        << "Source incident azimuth: "
        << sourceIncidentAzimuthDeg / deg
        << " deg"
        << G4endl;

    G4cout
        << "Source elevation: "
        << sourceElevationDeg / deg
        << " deg"
        << G4endl;

    G4cout
        << "Sample to tube collimator distance: "
        << sampleToTubeCollimatorDistance / mm
        << " mm"
        << G4endl;

    G4cout
        << "Source collimator radius: "
        << sourceCollimatorRadius / mm
        << " mm"
        << G4endl;

    G4cout
        << "Calculated sample beam diameter: "
        << sampleBeamDiameter / mm
        << " mm"
        << G4endl;


    // DETECTOR ACTIVE VOLUME

    PrintSection("DETECTOR ACTIVE VOLUME");

    G4cout
        << "Shape: "
        << detectorActiveVolumeShape
        << G4endl;


    G4cout << "Geometry:" << G4endl;

    G4cout
        << "  Width: "
        << detectorWidth / mm
        << " mm"
        << G4endl;

    G4cout
        << "  Height: "
        << detectorHeight / mm
        << " mm"
        << G4endl;

    G4cout
        << "  Thickness: "
        << detectorThickness / mm
        << " mm"
        << G4endl;

    G4cout
        << "  Inner radius: "
        << detectorInnerRadius / mm
        << " mm"
        << G4endl;

    G4cout
        << "  Outer radius: "
        << detectorOuterRadius / mm
        << " mm"
        << G4endl;

    G4cout
        << "  Radius: "
        << detectorRadius / mm
        << " mm"
        << G4endl;


    G4cout << "Material:" << G4endl;

    PrintMaterial(
        detectorMaterialType,
        detectorMaterialName,
        detectorDensity,
        detectorMaterialComposition
    );


    G4cout << "Placement:" << G4endl;

    G4cout
        << "  Distance from sample: "
        << detectorDistanceFromSample / mm
        << " mm"
        << G4endl;

    G4cout
        << "  Elevation angle: "
        << detectorelevationAngle / deg
        << " deg"
        << G4endl;

    G4cout
        << "  Azimuth angle: "
        << detectorazimuthAngle / deg
        << " deg"
        << G4endl;


    G4cout << "Orientation:" << G4endl;

    G4cout
        << "  Orientation type: "
        << detectorOrientationType
        << G4endl;

    G4cout
        << "  X rotation: "
        << detectorXRotation / deg
        << " deg"
        << G4endl;

    G4cout
        << "  Y rotation: "
        << detectorYRotation / deg
        << " deg"
        << G4endl;

    G4cout
        << "  Z rotation: "
        << detectorZRotation / deg
        << " deg"
        << G4endl;


    // DETECTOR APERTURE MASTER FLAG

    PrintSection("DETECTOR APERTURE");

    G4cout
        << "Detector aperture enabled: "
        << BoolText(isDetectorApertureUse)
        << G4endl;


    // DETECTOR COLLIMATORS

    PrintComponentCollection(
        "DETECTOR COLLIMATORS",
        isDetectorCollimatorUse,
        detectorCollimators
    );


    // DETECTOR INTERNAL MASKS

    PrintComponentCollection(
        "DETECTOR INTERNAL MASKS",
        isDetectorInternalMaskUse,
        detectorInternalMasks
    );


    // DETECTOR FILTERS

    PrintComponentCollection(
        "DETECTOR FILTERS",
        isDetectorFilterUse,
        detectorFilters
    );


    // DETECTOR HOUSING

    PrintSection("DETECTOR HOUSING");

    G4cout
        << "Enabled: "
        << BoolText(isDetectorHousingUse)
        << G4endl;

    G4cout
        << "Housing shape: "
        << detectorHousingShape
        << G4endl;


    G4cout << "Housing geometry:" << G4endl;

    G4cout
        << "  Side gap: "
        << detectorHousingSideGap / mm
        << " mm"
        << G4endl;

    G4cout
        << "  Front gap: "
        << detectorHousingFrontGap / mm
        << " mm"
        << G4endl;

    G4cout
        << "  Back gap: "
        << detectorHousingBackGap / mm
        << " mm"
        << G4endl;

    G4cout
        << "  Housing wall thickness: "
        << detectorHousingWallThickness / mm
        << " mm"
        << G4endl;


    // Housing aperture
    G4cout << "Housing aperture:" << G4endl;

    G4cout
        << "  Shape: "
        << detectorHousingApertureShape
        << G4endl;

    G4cout
        << "  Radius: "
        << detectorHousingApertureRadius / mm
        << " mm"
        << G4endl;

    G4cout
        << "  Width: "
        << detectorHousingApertureWidth / mm
        << " mm"
        << G4endl;

    G4cout
        << "  Height: "
        << detectorHousingApertureHeight / mm
        << " mm"
        << G4endl;


    // Housing material
    G4cout << G4endl;
    G4cout << "Housing material:" << G4endl;

    PrintMaterial(
        detectorHousingMaterialType,
        detectorHousingMaterialName,
        detectorHousingDensity,
        detectorHousingMaterialComposition
    );


    // ============================================================
    // DETECTOR HOUSING CAVITY
    // ============================================================

    G4cout << G4endl;
    G4cout << "Housing cavity:" << G4endl;

    G4cout
        << "Cavity material type: "
        << detectorHousingCavityMaterialType
        << G4endl;

    G4cout
        << "Cavity material name: "
        << detectorHousingCavityMaterialName
        << G4endl;

    G4cout
        << "Cavity density: "
        << detectorHousingCavityDensity / (g / cm3)
        << " g/cm3"
        << G4endl;

    G4cout
        << "Cavity wall thickness: "
        << detectorHousingCavityWallThickness / mm
        << " mm"
        << G4endl;

    G4cout
        << "Cavity internal medium material: "
        << detectorHousingCavityInternalMaterialName
        << G4endl;

    PrintComposition(
        detectorHousingCavityMaterialComposition
    );


    // ============================================================
    // DETECTOR HOUSING WINDOW
    // ============================================================

    G4cout << G4endl;
    G4cout << "Housing entrance window:" << G4endl;

    PrintMaterial(
        detectorHousingWindowMaterialType,
        detectorHousingWindowMaterialName,
        detectorHousingWindowDensity,
        detectorHousingWindowComposition
    );

    G4cout
        << "Window thickness: "
        << detectorHousingWindowThickness / mm
        << " mm"
        << G4endl;

    // ============================================================
    // VARIANCE REDUCTION / BIASING
    // ============================================================

    PrintSection("VARIANCE REDUCTION / BIASING");

    G4cout
        << "Number of secondary splitting: "
        << numberOfSecondarySplitting
        << G4endl;


    // ============================================================
    // PHYSICS
    // ============================================================

    PrintSection("PHYSICS");


    // Atomic de-excitation
    G4cout << "Atomic de-excitation:" << G4endl;

    G4cout
        << "  Fluorescence: "
        << BoolText(isFluorescenceUse)
        << G4endl;

    G4cout
        << "  Auger: "
        << BoolText(isAugerUse)
        << G4endl;

    G4cout
        << "  PIXE: "
        << BoolText(isPixeUse)
        << G4endl;

    G4cout
        << "  Ignore de-excitation cut: "
        << BoolText(isIgnoreCutUse)
        << G4endl;


    // Secondary splitting
    G4cout << G4endl;
    G4cout << "Secondary splitting:" << G4endl;

    G4cout
        << "  Enabled: "
        << BoolText(isSecondarySplittingUse)
        << G4endl;

    G4cout
        << "  Photoelectric factor: "
        << photoelectricFactor
        << G4endl;

    G4cout
        << "  Compton factor: "
        << comptFactor
        << G4endl;

    G4cout
        << "  Rayleigh factor: "
        << rayleighFactor
        << G4endl;

    G4cout
        << "  Maximum energy: "
        << maximumEnergy / keV
        << " keV"
        << G4endl;


    // Interaction biasing
    G4cout << G4endl;
    G4cout << "Interaction biasing:" << G4endl;

    G4cout
        << "  Enabled: "
        << BoolText(isInteractionBiasingUse)
        << G4endl;


    // Production cuts
    G4cout << G4endl;
    G4cout << "Production cuts:" << G4endl;

    G4cout
        << "  Gamma cut: "
        << gammaCut / mm
        << " mm"
        << G4endl;

    G4cout
        << "  Electron cut: "
        << electronCut / mm
        << " mm"
        << G4endl;

    G4cout
        << "  Positron cut: "
        << positronCut / mm
        << " mm"
        << G4endl;

    G4cout
        << "  Proton cut: "
        << protonCut / mm
        << " mm"
        << G4endl;


    // ============================================================
    // End
    // ============================================================

    G4cout << G4endl;

    PrintSeparator();

    G4cout
        << "              END SIMULATION CONFIGURATION"
        << G4endl;

    PrintSeparator();

    G4cout << G4endl;
}