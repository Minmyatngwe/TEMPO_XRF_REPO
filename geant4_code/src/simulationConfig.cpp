#include "simulationConfig.hh"
namespace
{

void PrintSection(const G4String& title)
{
    G4cout << "\n========== "
           << title
           << " =========="
           << G4endl;
}


void PrintMaterial(
    const G4String& label,
    const MaterialConfig& material)
{
    G4cout << label << ":\n"
           << "  Type: " << material.type << "\n"
           << "  Name: " << material.name
           << G4endl;

    if (material.type == "custom") {

        G4cout << "  Density: "
               << material.density / (g/cm3)
               << " g/cm3"
               << G4endl;

        for (const auto& composition : material.compositions) {

            G4cout << "    "
                   << composition.elementName
                   << ": "
                   << composition.fraction
                   << G4endl;
        }
    }
}

}
void SimulationConfig::LoadFromJson(const nlohmann::json& jsonConfig)
{       
       tubeFilterComponents.clear();
       detectorFilterConfig.clear();
       detectorCollimatorConfig.clear();
       detectorInternalMaskConfig.clear();

       isHousingUse = false;

        //world 

        const auto & worldConfig=getRequired<nlohmann::json>(jsonConfig,
            "SimulationConfig",
            "world",
            "Simulation Config");


        if(!worldConfig.is_object()){
            G4String errorMsg = "Key 'world' must be a JSON object in context: Simulation Config";
            G4Exception(
                "SimulationConfig::LoadFromJson",
                "ConfigParseError",
                FatalException,
                errorMsg.c_str()
            );
        }

        parseMaterialConfig(getRequired<nlohmann::json>(worldConfig,"SimulationConfig","world_material","Simulation Config"),"worldMaterial",worldMaterial);
        worldXSize=getRequired<G4double>(worldConfig,"SimulationConfig","world_size_x_mm","Simulation Config")*mm;
        worldYSize=getRequired<G4double>(worldConfig,"SimulationConfig","world_size_y_mm","Simulation Config")*mm;
        worldZSize=getRequired<G4double>(worldConfig,"SimulationConfig","world_size_z_mm","Simulation Config")*mm;

        //xray tube 


        const auto & tubeJson =getRequired<nlohmann::json>(jsonConfig,
            "SimulationConfig",
            "xray_tube",
            "Simulation Config");
       tubeConfig.name=getRequired<G4String>(tubeJson ,"SimulationConfig","name","Simulation Config");
       focalSpotDiameter=getRequired<G4double>(tubeJson,"SimulationConfig","focal_spot_diameter_mm","Simulation Config")*mm;
       tubeWindowToSampleDistance=getRequired<G4double>(tubeJson,"SimulationConfig","tube_window_to_sample_distance_mm","Simulation Config")*mm;
       tubeCollimatorRadius=getRequired<G4double>(tubeJson,"SimulationConfig","tube_collimator_radius_mm","Simulation Config")*mm;
       tubeWindowToVirtualCollimator=getRequired<G4double>(tubeJson,"SimulationConfig","tube_window_to_virtual_collimator_distance_mm","Simulation Config")*mm;
        const auto & tubePlacementJson=getRequired<nlohmann::json>(tubeJson,"Simulation config",
       "placement",
       "Simulation Config");

        parsePlacementConfig(tubePlacementJson,tubeConfig);
        //window

        const auto & tubeWindowJson =getRequired<nlohmann::json>(tubeJson ,
            "SimulationConfig",
            "tube_window",
            "Simulation Config");
        
        tubeWindowConfig.name=getRequired<G4String>(tubeWindowJson ,"SimulationConfig","name","Simulation Config");

        const auto & tubeWindowMaterialJson =getRequired<nlohmann::json>(tubeWindowJson ,
            "SimulationConfig",
            "material",
            "Simulation Config");
        
        parseMaterialConfig(tubeWindowMaterialJson ,tubeWindowConfig.name,tubeWindowConfig.material);
        tubeWindowConfig.thickness=getRequired<G4double>(tubeWindowJson,tubeWindowConfig.name,"thickness_mm","Tube window config")*mm;
        
        //filters

        const auto& tubeFiltersJson = getRequired<nlohmann::json>(
            tubeJson,
            "SimulationConfig",
            "tube_filters_geant4",
            "Simulation Config"
        );

        if (!tubeFiltersJson.is_array()) {
            G4String errorMsg =
                "Key 'filters' must be a JSON array in context: Simulation Config";

            G4Exception(
                "SimulationConfig::LoadFromJson",
                "ConfigParseError",
                FatalException,
                errorMsg.c_str()
            );
        }
        for (const auto& filterJson : tubeFiltersJson) {
            ComponentConfig filterConfig;

            parseComponentConfig(filterJson, filterConfig,true);

            tubeFilterComponents.emplace_back(filterConfig);
        }    
        //sample 
        const auto & sampleJson=getRequired<nlohmann::json>(jsonConfig,"SimulationConfig","sample","Simulation sample config");
        sampleConfig.name=getRequired<G4String>(sampleJson,"SimulationConfig","name","Simulation sample name");
        
        const auto & sampleMaterialJson=getRequired<nlohmann::json>(sampleJson,"SimulationConfig","material","Simulation sample material");
        parseMaterialConfig(sampleMaterialJson,sampleConfig.name,sampleConfig.material);

        const auto & sampleGeometryJson=getRequired<nlohmann::json>(sampleJson,"Simulation Config","geometry","simulation samle geometry");
        parseGeometryConfig(sampleGeometryJson,sampleConfig);


        //physics
        const auto & physicsJson=getRequired<nlohmann::json>(jsonConfig,"simulationconfig","physics","simulationconfig");
        parsePhysicsConfig(physicsJson);

        //detector
        const auto & detectorJson=getRequired<nlohmann::json>(jsonConfig,"SimulationConfig ","detector","Simulation detector config");
        parseComponentConfig(detectorJson,detectorConfig);
       
        //detector filters

        const auto detectorFilterJson=getRequired<nlohmann::json>(detectorJson,"SimulationConfig","detector_filters","Simulation detector filters config");

        for(const auto & filter:detectorFilterJson){
              ComponentConfig tempoFilter;
              parseComponentConfig(filter,tempoFilter,true);
              detectorFilterConfig.emplace_back(tempoFilter);
        }

        //detector collimator

        const auto & detectorCollimatorJson=getRequired<nlohmann::json>(detectorJson,"SimulationConfig","detector_collimators","simulation detector collimators");

        for(const auto & collimatorJson:detectorCollimatorJson){
              ComponentConfig tempoCollimator;
              parseComponentConfig(collimatorJson,tempoCollimator,true);
              detectorCollimatorConfig.emplace_back(tempoCollimator);
        }

        //detector internal mask

        const auto  & internalMaskJson=getRequired<nlohmann::json>(detectorJson,"SimulationConfig","internal_masks","Internal mask simulation config");

        for(const auto  & maskJson:internalMaskJson){
              ComponentConfig tempomask;
              parseComponentConfig(maskJson,tempomask,true);
              detectorInternalMaskConfig.emplace_back(tempomask); 

        }


       //housing
       
       parseHousingConfig(detectorJson,housingConfig);



       

       


        
}
void SimulationConfig::printComponentConfig(
    const ComponentConfig& component)
{
    G4cout << "----------------------------------------" << G4endl;
    G4cout << "Name: " << component.name << G4endl;

    // Material
    if (!component.material.type.empty()) {
        PrintMaterial("Material", component.material);
    }

    // Geometry
    if (!component.shape.empty()) {

        G4cout << "Geometry:" << G4endl;
        G4cout << "  Shape: " << component.shape << G4endl;

        if (component.shape == "rectangular") {

            G4cout << "  Size: "
                   << component.width / mm << " x "
                   << component.height / mm
                   << " mm" << G4endl;

            G4cout << "  Thickness: "
                   << component.thickness / mm
                   << " mm" << G4endl;
        }

        else if (component.shape == "circular") {

            G4cout << "  Radius: "
                   << component.radius / mm
                   << " mm" << G4endl;

            G4cout << "  Thickness: "
                   << component.thickness / mm
                   << " mm" << G4endl;
        }

        else if (component.shape == "circular aperture") {

            G4cout << "  Aperture Radius: "
                   << component.apertureRadius / mm
                   << " mm" << G4endl;

            G4cout << "  Outer Radius: "
                   << component.outerRadius / mm
                   << " mm" << G4endl;

            G4cout << "  Length: "
                   << component.length / mm
                   << " mm" << G4endl;
        }

        else if (component.shape == "rectangular aperture") {

            G4cout << "  Aperture Size: "
                   << component.apertureWidth / mm
                   << " x "
                   << component.apertureHeight / mm
                   << " mm" << G4endl;

            G4cout << "  Outer Size: "
                   << component.outerWidth / mm
                   << " x "
                   << component.outerHeight / mm
                   << " mm" << G4endl;

            G4cout << "  Length: "
                   << component.length / mm
                   << " mm" << G4endl;
        }
    }

    // Placement
    if (component.isInherited) {

        G4cout << "Placement:" << G4endl;

        if (!component.referenceComponentName.empty()) {
            G4cout << "  Reference: "
                   << component.referenceComponentName
                   << G4endl;
        }

        G4cout << "  Surface Gap: "
               << component.distanceFromReferenceSurface / mm
               << " mm" << G4endl;

        G4cout << "  Orientation: inherited"
               << G4endl;
    }

    else if (!component.referenceComponentName.empty()) {

        G4cout << "Placement:" << G4endl;

        G4cout << "  Reference: "
               << component.referenceComponentName
               << G4endl;

        G4cout << "  Distance: "
               << component.distance / mm
               << " mm" << G4endl;

        G4cout << "  Elevation: "
               << component.elevationAngle / deg
               << " deg" << G4endl;

        G4cout << "  Azimuth: "
               << component.azimuthAngle / deg
               << " deg" << G4endl;

        G4cout << "  Orientation: "
               << component.orientationType
               << G4endl;

        if (component.orientationType == "manual") {

            G4cout << "  Rotation XYZ: "
                   << component.xRotation / deg << ", "
                   << component.yRotation / deg << ", "
                   << component.zRotation / deg
                   << " deg" << G4endl;
        }
    }

    G4cout << "----------------------------------------" << G4endl;
}
void SimulationConfig::Print()
{
    G4cout << "\n"
           << "==================================================\n"
           << "              XRF SIMULATION CONFIG\n"
           << "==================================================\n";


    // =========================================================
    // World
    // =========================================================

    PrintSection("WORLD");
    PrintMaterial("Material",worldMaterial);
    G4cout << "Size: "
           << worldXSize / mm << " x "
           << worldYSize / mm << " x "
           << worldZSize / mm
           << " mm\n";


    // =========================================================
    // X-ray tube
    // =========================================================

    PrintSection("X-RAY TUBE");

    G4cout << "Name: "
           << tubeConfig.name << "\n"

           << "Focal Spot Diameter: "
           << focalSpotDiameter / mm << " mm\n"

           << "Tube Window To Sample: "
           << tubeWindowToSampleDistance / mm << " mm\n"

           << "Tube Collimator Radius: "
           << tubeCollimatorRadius / mm << " mm\n"

           << "Window To Virtual Collimator: "
           << tubeWindowToVirtualCollimator / mm << " mm\n";


    if (!tubeConfig.referenceComponentName.empty()) {

        G4cout << "Placement:\n"
               << "  Reference: "
               << tubeConfig.referenceComponentName << "\n"

               << "  Distance: "
               << tubeConfig.distance / mm << " mm\n"

               << "  Elevation: "
               << tubeConfig.elevationAngle / deg << " deg\n"

               << "  Azimuth: "
               << tubeConfig.azimuthAngle / deg << " deg\n"

               << "  Orientation: "
               << tubeConfig.orientationType << "\n";
    }


    // =========================================================
    // Tube window
    // =========================================================

    PrintSection("TUBE WINDOW");

    G4cout << "Name: "
           << tubeWindowConfig.name << "\n"

           << "Thickness: "
           << tubeWindowConfig.thickness / mm
           << " mm\n";

    PrintMaterial(
        "Material",
        tubeWindowConfig.material
    );


    // =========================================================
    // Tube filters
    // =========================================================

    if (!tubeFilterComponents.empty()) {

        PrintSection("TUBE FILTERS");

        for (const auto& filter : tubeFilterComponents)
            printComponentConfig(filter);
    }


    // =========================================================
    // Sample
    // =========================================================

    PrintSection("SAMPLE");
    printComponentConfig(sampleConfig);


    // =========================================================
    // Detector
    // =========================================================

    PrintSection("DETECTOR");
    printComponentConfig(detectorConfig);


    // =========================================================
    // Detector filters
    // =========================================================

    if (!detectorFilterConfig.empty()) {

        PrintSection("DETECTOR FILTERS");

        for (const auto& filter : detectorFilterConfig)
            printComponentConfig(filter);
    }


    // =========================================================
    // Detector collimators
    // =========================================================

    if (!detectorCollimatorConfig.empty()) {

        PrintSection("DETECTOR COLLIMATORS");

        for (const auto& collimator : detectorCollimatorConfig)
            printComponentConfig(collimator);
    }


    // =========================================================
    // Internal masks
    // =========================================================

    if (!detectorInternalMaskConfig.empty()) {

        PrintSection("INTERNAL MASKS");

        for (const auto& mask : detectorInternalMaskConfig)
            printComponentConfig(mask);
    }


    // =========================================================
    // Housing
    // =========================================================

    if (!housingConfig.name.empty()) {

        PrintSection("DETECTOR HOUSING");

        G4cout << "Name: "
               << housingConfig.name << "\n"

               << "Shape: "
               << housingConfig.shape << "\n"

               << "Detector Clearance: "
               << housingConfig.detectorClearance / mm
               << " mm\n"

               << "Cavity Wall Thickness: "
               << housingConfig.housingCavityWallThickness / mm
               << " mm\n"

               << "Housing Wall Thickness: "
               << housingConfig.housingWallThickness / mm
               << " mm\n";


        // Aperture
        G4cout << "Aperture:\n"
               << "  Shape: "
               << housingConfig.apertureShape
               << G4endl;

        if (housingConfig.apertureShape == "circular") {

            G4cout << "  Radius: "
                   << housingConfig.apertureRadius / mm
                   << " mm\n";
        }

        else if (housingConfig.apertureShape == "rectangular") {

            G4cout << "  Size: "
                   << housingConfig.apertureWidth / mm
                   << " x "
                   << housingConfig.apertureHeight / mm
                   << " mm\n";
        }


        // Materials
        PrintMaterial(
            "Housing Material",
            housingConfig.housingWallMaterial
        );

        PrintMaterial(
            "Cavity Wall Material",
            housingConfig.cavityWallMaterial
        );

        PrintMaterial(
            "Inner Cavity Medium",
            housingConfig.innerCavityMediumMaterial
        );

        PrintMaterial(
            "Detector Window Material",
            housingConfig.detectorWindowMaterial
        );
    }


    // =========================================================
    // Physics
    // =========================================================

    PrintSection("PHYSICS");

    G4cout << "Interaction Biasing: "
           << (isInteractionBiasingUse ? "Enabled" : "Disabled")
           << "\n"

           << "Secondary Splitting: "
           << (isSecondarySplittingUse ? "Enabled" : "Disabled")
           << "\n"

           << "Fluorescence: "
           << (isFluorescenceUse ? "Enabled" : "Disabled")
           << "\n"

           << "Auger: "
           << (isAugerUse ? "Enabled" : "Disabled")
           << "\n"

           << "PIXE: "
           << (isPixeUse ? "Enabled" : "Disabled")
           << "\n"

           << "Ignore Cuts: "
           << (isIgnoreCutUse ? "Enabled" : "Disabled")
           << "\n"

           << "Fluorescence Dataset: "
           << fluDatasetName
           << "\n"

           << "Maximum Energy: "
           << maximumEnergy
           << "\n";


    G4cout << "Biasing Factors:\n"
           << "  Photoelectric: "
           << photoelectricFactor << "\n"

           << "  Compton: "
           << comptFactor << "\n"

           << "  Rayleigh: "
           << rayleighFactor << "\n";


    G4cout << "Production Cuts:\n"
           << "  Gamma: "
           << gammaCut / mm << " mm\n"

           << "  Electron: "
           << electronCut / mm << " mm\n"

           << "  Positron: "
           << positronCut / mm << " mm\n"

           << "  Proton: "
           << protonCut / mm << " mm\n";


    G4cout << "==================================================\n"
           << "              END CONFIGURATION\n"
           << "==================================================\n"
           << G4endl;
}

void SimulationConfig::parseComponentConfig(const nlohmann::json & componentConfigJson,ComponentConfig & componentConfig,G4bool isInherited)
{

    componentConfig.name=getRequired<G4String>(componentConfigJson,"SimulationConfig","name","Component Config");

    const auto & geometryConfig=getRequired<nlohmann::json>(componentConfigJson,
        componentConfig.name,
        "geometry",
        "Component Config");


    parseGeometryConfig(geometryConfig,componentConfig);
    

    const auto & materialConfigJson=getRequired<nlohmann::json>(componentConfigJson,
        componentConfig.name,
        "material",
        "Component Config");

    parseMaterialConfig(materialConfigJson,componentConfig.name,componentConfig.material);
    if(!isInherited){
       const auto & placementConfig=getRequired<nlohmann::json>(componentConfigJson,
              componentConfig.name,
              "placement",
              "Component Config");

       parsePlacementConfig(placementConfig,componentConfig);

    }
    else{
       const auto & placementJson=getRequired<nlohmann::json>(componentConfigJson,componentConfig.name,"placement","simulation  config");
       const auto & positionJson=getRequired<nlohmann::json>(placementJson,componentConfig.name,"position","simulation  config");

       componentConfig.distanceFromReferenceSurface=getRequired<G4double>(positionJson,componentConfig.name,"distance_mm","simulation  config")*mm;


       componentConfig.isInherited=true;

    }

}

void SimulationConfig::parsePhysicsConfig(const nlohmann::json & physicsJson){
        isInteractionBiasingUse=getRequired<G4bool>(physicsJson,"physics","interaction_bias_use","simulationConfig");
        isSecondarySplittingUse=getRequired<G4bool>(physicsJson,"physics","secondary_splitting_use","simulationConfig");
        isFluorescenceUse=getRequired<G4bool>(physicsJson,"physics","flu_use","simulationConfig");
        isAugerUse=getRequired<G4bool>(physicsJson,"physics","auger_use","simulationConfig");
        isPixeUse=getRequired<G4bool>(physicsJson,"physics","pixe_use","simulationConfig");
        isIgnoreCutUse=getRequired<G4bool>(physicsJson,"physics","ignore_cut_use","simulationConfig");

        fluDatasetName=getRequired<G4String>(physicsJson,"physics","flu_dataset_name","simulationConfig");

        maximumEnergy=getRequired<G4double>(physicsJson,"physics","maximum_energy","simulationConfig");
        photoelectricFactor=getRequired<G4double>(physicsJson,"physics","phot_factor","simulationConfig");
        comptFactor=getRequired<G4double>(physicsJson,"physics","compt_factor","simulationConfig");
        rayleighFactor=getRequired<G4double>(physicsJson,"physics","rayl_factor","simulationConfig");
        electronCut=getRequired<G4double>(physicsJson,"physics","electron_cut","simulationConfig");

        gammaCut=getRequired<G4double>(physicsJson,"physics","gamma_cut","simulationConfig");
        positronCut=getRequired<G4double>(physicsJson,"physics","positron_cut","simulationConfig");
        protonCut=getRequired<G4double>(physicsJson,"physics","proton_cut","simulationConfig");


}

void SimulationConfig::parseHousingConfig(const nlohmann::json & detectorJson,ComponentConfig &housingConfig){


       if(detectorJson.contains("housing")){

              const auto & housingJson=detectorJson.at("housing");

              if (!housingJson.is_object()){
                     G4String errorMsg =
                            "Key 'housing' must be a JSON object in context: Detector Configuration";

                     G4Exception(
                            "SimulationConfig::parseHousigConfig",
                            "ConfigParseError",
                            FatalException,
                            errorMsg.c_str()
                     );
              }

              housingConfig.name=toLower(getRequired<G4String>(housingJson,"Housing","name","Housing config"));
              // housingConfig.apertureShape=toLower(getRequired<G4String>(housingJson,"Housing",""))
              // housingConfig.innerCavityMedium=getRequired<G4String>(housingJson,"Housing","inner_cavity_medium_geant4","Housing inner cavity medium");
              const auto &housingGeometryJson=getRequired<nlohmann::json>(housingJson,housingConfig.name,"geometry","Housing geometry config");
              //geometry
              parseGeometryConfig(housingGeometryJson,housingConfig);

              //material
              //cavity
              const auto & housingCavityWallMaterialJson=getRequired<nlohmann::json>(housingJson,housingConfig.name,"cavity_wall_material","Housing cavity wall material");

              parseMaterialConfig(housingCavityWallMaterialJson,housingConfig.name,housingConfig.cavityWallMaterial);
              //housing
              const auto &  housingMaterialJson=getRequired<nlohmann::json>(housingJson,housingConfig.name,"housing_material","Housing  material");
              parseMaterialConfig(housingMaterialJson,housingConfig.name,housingConfig.housingWallMaterial);

              //innerCavityMediumMaterial

              const auto &  innerCavityMediumMaterialJson=getRequired<nlohmann::json>(housingJson,housingConfig.name,"inner_cavity_medium_material","Housing  material");
              parseMaterialConfig(innerCavityMediumMaterialJson,housingConfig.name,housingConfig.innerCavityMediumMaterial);

              //detectorwindowmaterial
              const auto &  detectorWinodwMaterial=getRequired<nlohmann::json>(housingJson,housingConfig.name,"window_material","Housing  material");
              parseMaterialConfig(detectorWinodwMaterial,housingConfig.name,housingConfig.detectorWindowMaterial);
              
              housingConfig.window_thickness_mm=getRequired<G4double>(housingJson,housingConfig.name,"window_thickness_mm","Housing detector window thickness")*mm;


              isHousingUse=true;


       }

}