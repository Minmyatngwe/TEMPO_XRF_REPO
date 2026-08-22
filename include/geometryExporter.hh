#pragma once

#include "G4PseudoScene.hh"
#include "G4PhysicalVolumeModel.hh"
#include "G4VPhysicalVolume.hh"
#include "G4VSolid.hh"

#include <nlohmann/json.hpp>

#include <string>

class GeometryExportScene : public G4PseudoScene
{
    public:
        GeometryExportScene(
            G4PhysicalVolumeModel& model,
            nlohmann::json& output
        );

    protected:
        void ProcessVolume(const G4VSolid& solid) override;

    private:
        G4PhysicalVolumeModel& fModel;
        nlohmann::json& fOutput;
};


void ExportGeometryForBrowser(
    G4VPhysicalVolume* world,
    const std::string& filename,
    G4int segmentsPerCircle = 48
);