#ifndef DETECTORCONSTRUCTION_HH
#define DETECTORCONSTRUCTION_HH

#include "G4VUserDetectorConstruction.hh"
#include "G4ThreeVector.hh"
#include "simulationConfig.hh"
#include "globals.hh"
#include "G4GenericMessenger.hh"
#include "G4VPhysicalVolume.hh"
#include "G4Box.hh"
#include "G4Element.hh"
#include "G4LogicalVolume.hh"
#include "G4Material.hh"
#include "G4NistManager.hh"
#include "G4PVPlacement.hh"
#include "G4RotationMatrix.hh"
#include "G4SDManager.hh"
#include "G4SubtractionSolid.hh"
#include "G4SystemOfUnits.hh"
#include "G4VisAttributes.hh"
#include "G4Colour.hh"
#include "G4RunManager.hh"
#include <nlohmann/json.hpp>
#include <fstream>
#include <stdexcept>

#include <algorithm>
#include <string>
#include <vector>

using json = nlohmann::json;


struct FaceOrientationToSample{

    G4ThreeVector localXAxis;
    G4ThreeVector localYAxis;
    G4ThreeVector localZAxis;
    G4RotationMatrix *rotMatrix{nullptr};

};
class DetectorConstruction:public G4VUserDetectorConstruction{

    public:
        DetectorConstruction (SimulationConfig& config,nlohmann::json & jsonConfig,std::string updateJsonPath);
        ~DetectorConstruction() override;
        G4VPhysicalVolume* Construct() override;
        void ConstructSDandField() override;
        G4ThreeVector CalculatePositionFromSphericalCoordinates(G4double distance, G4double azimuthalAngle, G4double elevationAngle);
        FaceOrientationToSample CalculateRotationToFaceSample(const G4ThreeVector& detectorPosition,const  G4ThreeVector &samplePosition);

        void BuildComponent(const std::vector<ComponentConfig>& filters,G4LogicalVolume* motherLogic,   const G4ThreeVector &sampleSurfacePoint,G4int & physplacementIndex,G4String type="filter",nlohmann::json *componentJson=nullptr);

        G4Material * BuildMaterial(const G4String&,const G4String&,
        G4double,const std::vector<MaterialComponent>&);
                
    private:
        G4LogicalVolume* fDetectorLV{nullptr};
        G4LogicalVolume *fSampleLogical {nullptr};
        G4double detectorThickness{0.0};
        SimulationConfig *fConfig{nullptr};
        nlohmann::json * fjsonConfig{nullptr};
        std::string fupdateJsonPath;

        void storeRotationMatrix(json &,const G4RotationMatrix &);
        void saveJsonFile(
            const std::string&filePath,
            const nlohmann::json &configJson
        );
        void checkGeometryOrDie(G4VPhysicalVolume* volume,const G4String &name);
        G4VSolid* BuildFilterSolid(const ComponentConfig& filter);
        G4VSolid* BuildCollimatorOrInternalMaskSolid(const ComponentConfig& component);

};


#endif