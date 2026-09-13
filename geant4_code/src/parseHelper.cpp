#include "parseHelper.hh"

#include <cmath>
void ParseHelper::parseMaterialConfig(
    const nlohmann::json& materialJson,
    const G4String& componentName,
    MaterialConfig& materialConfig)
{

    materialConfig.type = toLower(
        getRequired<G4String>(
            materialJson,
            componentName,
            "material_type",
            "Material Config"
        )
    );


    if (materialConfig.type != "custom" &&
        materialConfig.type != "geant4") {

        G4String errorMsg =
            "Invalid material_type: " +
            materialConfig.type +
            " in component: " +
            componentName +
            " in context: Material Config";

        G4Exception(
            "ParseHelper::parseMaterialConfig",
            "ConfigParseError",
            FatalException,
            errorMsg.c_str()
        );
    }


    materialConfig.name =
        getRequired<G4String>(
            materialJson,
            componentName,
            "material_name",
            "Material Config"
        );


    if (materialConfig.type == "custom") {

        if (!materialJson.contains("compositions")) {

            G4String errorMsg =
                "Missing required key: compositions"
                " in component: " +
                componentName +
                " in context: Material Config";

            G4Exception(
                "ParseHelper::parseMaterialConfig",
                "ConfigParseError",
                FatalException,
                errorMsg.c_str()
            );
        }


        if (!materialJson.at("compositions").is_array()) {

            G4String errorMsg =
                "Key: compositions is not an array"
                " in component: " +
                componentName +
                " in context: Material Config";

            G4Exception(
                "ParseHelper::parseMaterialConfig",
                "ConfigParseError",
                FatalException,
                errorMsg.c_str()
            );
        }


        materialConfig.compositions.clear();

        G4double totalFraction = 0.0;

        int index = 0;


        for (const auto& component :
             materialJson.at("compositions")) {

            G4String elementName =
                getRequired<G4String>(
                    component,
                    componentName,
                    "element",
                    "Material Config Compositions[" +
                    std::to_string(index) +
                    "]"
                );


            G4double fraction =
                getRequired<G4double>(
                    component,
                    componentName,
                    "mass_fraction",
                    "Material Config Compositions[" +
                    std::to_string(index) +
                    "]"
                );


            if (fraction < 0.0 || fraction > 1.0) {

                G4String errorMsg =
                    "Mass fraction must be between 0 and 1"
                    " in component: " +
                    componentName +
                    " at composition index: " +
                    std::to_string(index);

                G4Exception(
                    "ParseHelper::parseMaterialConfig",
                    "ConfigParseError",
                    FatalException,
                    errorMsg.c_str()
                );
            }


            totalFraction += fraction;

            materialConfig.compositions.emplace_back(
                elementName,
                fraction
            );

            index++;
        }


        if (std::abs(totalFraction - 1.0) > 1e-6) {

            G4String errorMsg =
                "Total mass fraction of material components "
                "is not equal to 1.0 in component: " +
                componentName +
                " in context: Material Config Compositions";

            G4Exception(
                "ParseHelper::parseMaterialConfig",
                "ConfigParseError",
                FatalException,
                errorMsg.c_str()
            );
        }


        materialConfig.density =
            getRequired<G4double>(
                materialJson,
                componentName,
                "density_g_cm3",
                "Material Config"
            ) * g/cm3;
    }
}

void ParseHelper::parseGeometryConfig(const nlohmann::json & geometryConfigJson,ComponentConfig & componentConfig){

    componentConfig.shape =toLower(
            getRequired<G4String>(
                geometryConfigJson,
                componentConfig.name,
                "shape",
                "Geometry Config"
            )
        );
    if (componentConfig.shape=="rectangular"){
        componentConfig.width=getRequired<G4double>(geometryConfigJson,componentConfig.name,"width_mm","Geometry Config")*mm;
        componentConfig.height=getRequired<G4double>(geometryConfigJson,componentConfig.name,"height_mm","Geometry Config")*mm;
        componentConfig.thickness=getRequired<G4double>(geometryConfigJson,componentConfig.name,"thickness_mm","Geometry Config")*mm;
    }

    else if (componentConfig.shape=="circular"){
        componentConfig.radius=getRequired<G4double>(geometryConfigJson,componentConfig.name,"radius_mm","Geometry Config")*mm;
        componentConfig.thickness=getRequired<G4double>(geometryConfigJson,componentConfig.name,"thickness_mm","Geometry Config")*mm;

    }

    else if (componentConfig.shape=="circular aperture"){
        componentConfig.apertureShape=toLower(getRequired<G4String>(geometryConfigJson,componentConfig.name,"aperture_shape","Geometry Config aperture shape"));
        componentConfig.apertureRadius=getRequired<G4double>(geometryConfigJson,componentConfig.name,"aperture_radius_mm","Geometry Config")*mm;
        componentConfig.length=getRequired<G4double>(geometryConfigJson,componentConfig.name,"length_mm","Geometry Config")*mm;
        componentConfig.outerRadius=getRequired<G4double>(geometryConfigJson,componentConfig.name,"outer_radius_mm","Geometry Config")*mm;

    }
    else if(componentConfig.shape=="rectangular aperture"){
        componentConfig.apertureShape=toLower(getRequired<G4String>(geometryConfigJson,componentConfig.name,"aperture_shape","Geometry Config aperture shape"));

        componentConfig.apertureWidth=getRequired<G4double>(geometryConfigJson,componentConfig.name,"aperture_width_mm","Geometry Config")*mm;
        componentConfig.apertureHeight=getRequired<G4double>(geometryConfigJson,componentConfig.name,"aperture_height_mm","Geometry Config")*mm;
        componentConfig.length=getRequired<G4double>(geometryConfigJson,componentConfig.name,"length_mm","Geometry Config")*mm;
        componentConfig.outerWidth=getRequired<G4double>(geometryConfigJson,componentConfig.name,"outer_width_mm","Geometry Config")*mm;
        componentConfig.outerHeight=getRequired<G4double>(geometryConfigJson,componentConfig.name,"outer_height_mm","Geometry Config")*mm;

    }
    else if (componentConfig.shape=="detector housing"){

        componentConfig.apertureShape=toLower(getRequired<G4String>(geometryConfigJson,componentConfig.name,"aperture_shape","Geometry Config"));

        if(componentConfig.apertureShape=="circular"){
            componentConfig.apertureRadius=getRequired<G4double>(geometryConfigJson,componentConfig.name,"aperture_radius_mm","Housing Geometry config")*mm;

        }

        else if (componentConfig.apertureShape=="rectangular"){
            componentConfig.apertureWidth=getRequired<G4double>(geometryConfigJson,componentConfig.name,"aperture_width_mm","Housing Geometry Config")*mm;
            componentConfig.apertureHeight=getRequired<G4double>(geometryConfigJson,componentConfig.name,"aperture_height_mm","Housing Geometry Config")*mm;
        }
        else {

            G4String errorMsg =
                "Invalid aperture shape '" + componentConfig.apertureShape +
                "' for component '" + componentConfig.name +
                "'. Supported aperture shapes are 'circular' and 'rectangular'.";

            G4Exception(
                "SimulationConfig::parseGeometryConfig",
                "InvalidApertureShape",
                FatalException,
                errorMsg.c_str()
            );
        }
        componentConfig.detectorClearance=getRequired<G4double>(geometryConfigJson,componentConfig.name,"detector_clearance_mm","Housing Geometry config")*mm;
        componentConfig.housingWallThickness=getRequired<G4double>(geometryConfigJson,componentConfig.name,"housing_wall_thickness_mm","Housing Geometry Config")*mm;
        componentConfig.housingCavityWallThickness=getRequired<G4double>(geometryConfigJson,componentConfig.name,"cavity_wall_thickness_mm","Housing Geometry Config")*mm;

    }
    else{
        G4String errorMsg = "Invalid shape: ";
        errorMsg += componentConfig.shape;
        errorMsg += " in component: ";
        errorMsg += componentConfig.name;
        errorMsg += " in context: Geometry Config";
        
        G4Exception(
            "ParseHelper::parseGeometryConfig",
            "ConfigParseError",
            FatalException,
            errorMsg.c_str()
        );
    }

}

void ParseHelper::parsePlacementConfig(const nlohmann::json & placementConfigJson,ComponentConfig & componentConfig){

        const auto positiionConfigJson =getRequired<nlohmann::json>(
                placementConfigJson,
                componentConfig.name,
                "position",
                "Placement Config"
                );
        if (!positiionConfigJson.is_object()) {

            G4String errorMsg =
                "Key 'position' must be a JSON object"
                " in component: " + componentConfig.name +
                " in context: Placement Config";

            G4Exception(
                "ParseHelper::parsePlacementConfig",
                "ConfigParseError",
                FatalException,
                errorMsg.c_str()
            );
        }

        componentConfig.referenceComponentName=getRequired<G4String>(positiionConfigJson,componentConfig.name,"reference","Placement Config Position");

        componentConfig.distance=getRequired<G4double>(positiionConfigJson,componentConfig.name,"distance_mm","Placement Config Position")*mm;

        componentConfig.elevationAngle=getRequired<G4double>(positiionConfigJson,componentConfig.name,"elevation_deg","Placement Config Position")*deg;

        componentConfig.azimuthAngle=getRequired<G4double>(positiionConfigJson,componentConfig.name,"azimuth_deg","Placement Config Position")*deg;
    
        const auto orientationModeJson=getRequired<nlohmann::json>(placementConfigJson,"placement","orientation","simulation placement orientation mode");
        G4String orientationMode=toLower(getRequired<G4String>(orientationModeJson,componentConfig.name,"mode","Placement Config Orientation"));

        if(orientationMode=="face_sample"){
            componentConfig.orientationType=orientationMode;
        }

        else if(orientationMode=="manual"){
            componentConfig.orientationType=orientationMode;
            componentConfig.xRotation=getRequired<G4double>(orientationModeJson,componentConfig.name,"x","Placement Config Orientation")*deg;
            componentConfig.yRotation=getRequired<G4double>(orientationModeJson,componentConfig.name,"y","Placement Config Orientation")*deg;
            componentConfig.zRotation=getRequired<G4double>(orientationModeJson,componentConfig.name,"z","Placement Config Orientation")*deg;

        }

        else{
            G4String errorMsg = "Invalid orientation mode: ";
            errorMsg += orientationMode;
            errorMsg += " in component: ";
            errorMsg += componentConfig.name;
            errorMsg += " in context: Placement Config Orientation";
            
            G4Exception(
                "ParseHelper::parsePlacementConfig",
                "ConfigParseError",
                FatalException,
                errorMsg.c_str()
            );

        }
}

