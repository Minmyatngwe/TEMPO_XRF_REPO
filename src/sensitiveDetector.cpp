#include "sensitiveDetector.hh"
#include "trackInformation.hh"
#include "G4Step.hh"
#include "G4Track.hh"
#include "G4StepPoint.hh"
#include "G4VPhysicalVolume.hh"
#include "G4Gamma.hh"
#include "G4UnitsTable.hh"
#include "G4LogicalVolume.hh"
#include "G4RunManager.hh"
#include "G4Event.hh"
#include "G4Run.hh"
#include "G4Region.hh"
#include "G4AnalysisManager.hh"
SensitiveDetector::SensitiveDetector():G4VSensitiveDetector("SensitiveDetector"){

}
SensitiveDetector::~SensitiveDetector(){

}


// Reset all per-event detector scoring containers before
// processing energy deposits from the new event.

void SensitiveDetector::Initialize(G4HCofThisEvent *hce){

    energyDepositTrackEnergy.clear();
    energyDepositTrackWeight.clear();
}
// Accumulate detector energy deposits by root track ID.
// Deposits from secondary tracks belonging to the same root
// particle are combined into one detector-energy value.

G4bool SensitiveDetector::ProcessHits(
    G4Step* step,
    G4TouchableHistory* hist)
{
    const G4double edep =
        step->GetTotalEnergyDeposit();

    G4Track* track =
        step->GetTrack();

    TrackInformation* info =
        dynamic_cast<TrackInformation*>(
            track->GetUserInformation()
        );

    if (info == nullptr) {
        return true;
    }


    if (edep <= 0.0) {
        return true;
    }

    const G4int rootId =info->GetRootID();

    energyDepositTrackWeight[rootId] =track->GetWeight();

    energyDepositTrackEnergy[rootId] +=edep;
    return true;
}
// Write one detector response entry for each root particle
// that deposited energy during this event.

void SensitiveDetector::EndOfEvent(G4HCofThisEvent *hce){
    const G4RunManager* runManager = G4RunManager::GetRunManager();
    
    G4int eventId = runManager->GetCurrentEvent()->GetEventID();
    G4AnalysisManager* analysisManager = G4AnalysisManager::Instance();
    for(const auto& [rootId,energy]: energyDepositTrackEnergy) {
        G4double weight = energyDepositTrackWeight[rootId];
        if(energy>0){
            // G4cout << "Track ID: " << rootId << ", Energy Deposited: " << energy / keV << " keV, Weight: " << weight << G4endl;
            
            analysisManager->FillH1(0, energy / keV,weight);
            analysisManager->FillNtupleIColumn(0, eventId);
            analysisManager->FillNtupleIColumn(1, rootId);
            analysisManager->FillNtupleDColumn(2, energy/keV); 
            analysisManager->FillNtupleDColumn(3, weight);
            analysisManager->AddNtupleRow();
            
        }
    }
}