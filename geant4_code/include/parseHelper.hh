#ifndef PARSEHELPER_HH
#define PARSEHELPER_HH

#include <nlohmann/json.hpp>
#include "G4SystemOfUnits.hh"
#include "G4ThreeVector.hh"
#include "utility.hh"
#include "G4RotationMatrix.hh"

namespace ParseHelper{
    struct ComponentRotation{
        G4ThreeVector localXAxis;
        G4ThreeVector localYAxis;
        G4ThreeVector localZAxis;
        G4RotationMatrix *rotMatrix {nullptr};
    };


    struct  MaterialComponent{

        public:
            G4String elementName;
            G4double fraction;
            MaterialComponent(const G4String  &elementName, G4double fraction): elementName(elementName), fraction(fraction){};
    };
    struct MaterialConfig {

        G4String type;
        G4String name;

        G4double density = 0 * g/cm3;

        std::vector<MaterialComponent> compositions;
    };
    struct  ComponentConfig{

            G4String name;
            G4String shape;
            G4String apertureShape;

            //Rectangular geometry

            G4double width=0*mm;
            G4double height=0*mm;
            G4double thickness=0*mm;
            
            //Circular / cylindrical geometry
            G4double radius=0*mm; 


            G4double outerRadius=0*mm;
            G4double innerRadius=0*mm;
            
            //Aperture information
    
            G4double apertureRadius=0*mm;
            G4double apertureWidth=0*mm;
            G4double apertureHeight=0*mm;

            G4double length=0*mm;

            //Rectangular collimator outer dimensions
            G4double outerWidth=0*mm;
            G4double outerHeight=0*mm;


            //material information
            MaterialConfig material;

            //placement information
        
            G4String referenceComponentName;
            G4double distance=0*mm;
            
            G4double elevationAngle=0*deg;
            G4double azimuthAngle=0*deg;


            G4String orientationType;
            G4double xRotation=0*deg;
            G4double yRotation=0*deg;
            G4double zRotation=0*deg; 

            //internal mask
            G4double distanceFromReferenceSurface=0*mm;
            G4bool isInherited=false;

            //housing
            G4double detectorClearance=0*mm;
            G4double housingWallThickness=0*mm;
            G4double housingCavityWallThickness=0*mm; 
            MaterialConfig innerCavityMediumMaterial;
            MaterialConfig detectorWindowMaterial;

            MaterialConfig housingWallMaterial;
            MaterialConfig cavityWallMaterial;
            G4double window_thickness_mm=0*mm;
            //position and rotation

            G4ThreeVector position;
            ComponentRotation rotation;
                        

    };
    template<typename T>
    T getRequired(const nlohmann::json & jsonObject,const std::string & componentName,const std::string & key,const std::string & context ){    if(!jsonObject.contains(key)){
        
        G4String errorMsg = "Missing required key: ";
        errorMsg += key;
        errorMsg += " in component: ";
        errorMsg += componentName;
        errorMsg += " in context: ";
        errorMsg += context;
        
        G4Exception(
            "ParseHelper::getRequired",
            "ConfigParseError",
            FatalException,
            errorMsg.c_str()
        );

    }

    try{
        return jsonObject.at(key).get<T>();
    }
    catch(const nlohmann::json::exception&e){
        std::string errorMsg= "JSON parsing failed! Check your  config.\n";
        errorMsg += "Component: ";
        errorMsg += componentName;
        errorMsg += " Key: ";
        errorMsg += key;
        errorMsg += " Context: ";
        errorMsg += context;    
        errorMsg += "Nlohmann Error: ";
        errorMsg += e.what();
        G4Exception(
            "ParseHelper::getRequired",
            "ConfigParseError",
            FatalException,
            errorMsg.c_str()
        );

        throw;
    }

}
    void parseMaterialConfig(const nlohmann::json& materialJson,const G4String& componentName,MaterialConfig& materialConfig);
    void parseGeometryConfig(const nlohmann::json & geometryConfig,ComponentConfig &componentConfig);
    void parsePlacementConfig(const nlohmann::json & placementConfig,ComponentConfig &componentConfig);
    
}

#endif