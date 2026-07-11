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

#include <algorithm>
#include <string>
#include <vector>


class DetectorConstruction:public G4VUserDetectorConstruction{

    public:
        DetectorConstruction (SimulationConfig& config);
        ~DetectorConstruction() override;
        G4VPhysicalVolume* Construct() override;
        void ConstructSDandField() override;
                SimulationConfig *fConfig{nullptr};
    private:
        G4LogicalVolume* fDetectorLV{nullptr};

};


#endif