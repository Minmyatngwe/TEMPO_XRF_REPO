#include "steppingAction.hh"
#include "trackInformation.hh"

#include "G4Step.hh"
#include "G4Track.hh"
#include "G4SystemOfUnits.hh"
#include "G4UnitsTable.hh"
#include "G4SteppingManager.hh" 
#include "G4EmCalculator.hh"
#include "G4Gamma.hh"
#include "G4LogicalVolumeStore.hh"
#include "G4LogicalVolume.hh"
#include "G4Box.hh"
#include "G4VProcess.hh"
#include <iomanip>
#include "G4RunManager.hh"
#include "G4AnalysisManager.hh"
#include "G4RegionStore.hh"
#include "G4Region.hh"
#include "G4ProductionCuts.hh"
#include "runAction.hh"
SteppingAction::SteppingAction(
    SimulationConfig& config,
    RunAction* runAction
)
    : G4UserSteppingAction(),
      fConfig(&config),
      fRunAction(runAction)
{}
SteppingAction::~SteppingAction() {}

// Track particles entering the detector and propagate their detector-entry
// root ID to all secondaries created inside the detector.
// This allows SensitiveDetector to combine all energy deposits originating
// from the same particle that entered the active detector volume.

void SteppingAction::UserSteppingAction(const G4Step* step) {


    G4Track* track = step->GetTrack();

    G4double energy = track->GetKineticEnergy();

    // G4ThreeVector position = track->GetPosition();

    // if (position.z()<-5*cm||position.x()<-5*cm){
    //     track->SetTrackStatus(fStopAndKill);
    // }

    G4StepPoint *preStepPoint = step->GetPreStepPoint();

    G4StepPoint *postStepPoint = step->GetPostStepPoint();

    if (!postStepPoint || !postStepPoint->GetPhysicalVolume()) {
        return;
        }




    G4String preVolumeName = preStepPoint->GetPhysicalVolume()->GetName();
    G4String postVolumeName = postStepPoint->GetPhysicalVolume()->GetName();

    const G4bool crossedBoundary =(postStepPoint->GetStepStatus() ==fGeomBoundary &&preVolumeName != postVolumeName);
    // When a particle enters the active detector for the first time,
    // use its Geant4 track ID as the root ID for the complete detector
    // interaction chain produced by this incoming particle.

        
    if(postVolumeName=="detectorPhys" && preVolumeName!="detectorPhys"){
        if(track->GetUserInformation()==nullptr){
            G4int trackID = track->GetTrackID();
            
            TrackInformation *info=new TrackInformation(trackID);
            track->SetUserInformation(info);
        }

    }

    // If this track already belongs to a detector interaction chain,
    // propagate the same root ID to every secondary it creates
    // while travelling inside the active detector.

    TrackInformation *info=dynamic_cast<TrackInformation*>(track->GetUserInformation());
    if (info != nullptr && preVolumeName == "detectorPhys") {

    const G4int rootId = info->GetRootID();
    const auto* secondaries =
        step->GetSecondaryInCurrentStep();
    if (secondaries != nullptr) {
        for (const G4Track* secondaryConst : *secondaries) {

            G4Track* secondaryTrack =
                const_cast<G4Track*>(secondaryConst);
            // Only assign information if another action has not
            // already attached user information to this secondary.

            if (secondaryTrack->GetUserInformation() == nullptr) {

                auto* secondaryInfo =
                    new TrackInformation(rootId);

                secondaryTrack->SetUserInformation(
                    secondaryInfo
                );
            }
        }
    }
    }


}
