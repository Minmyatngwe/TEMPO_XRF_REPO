#include "sensitiveDetector.hh"
#include "trackInformation.hh"
#include "G4Step.hh"
#include "G4Track.hh"
#include "G4StepPoint.hh"
#include "G4VPhysicalVolume.hh"
#include "G4Gamma.hh"
#include "G4UnitsTable.hh"
#include "G4LogicalVolume.hh"
#include "G4VPhysicalVolume.hh"
SensitiveDetector::SensitiveDetector():G4VSensitiveDetector("SensitiveDetector"),fTotalEnergyDeposited(0.0){

}
SensitiveDetector::~SensitiveDetector(){

}



void SensitiveDetector::Initialize(G4HCofThisEvent *hce){

    fTotalEnergyDeposited=0.0;
    energyWeight=1.0;
    energyDepositTrackEnergy.clear();
    energyDepositTrackWeight.clear();

}

G4bool SensitiveDetector::ProcessHits(G4Step *step, G4TouchableHistory *hist)
{
G4double edep = step->GetTotalEnergyDeposit();

    G4Track* track = step->GetTrack();

    TrackInformation* info =
        dynamic_cast<TrackInformation*>(track->GetUserInformation());
    G4StepPoint* pre  = step->GetPreStepPoint();
    G4StepPoint* post = step->GetPostStepPoint();

 auto* creatorProc = track->GetCreatorProcess();

G4String creatorName =
    creatorProc ? creatorProc->GetProcessName() : "primary";

// Parent track ID
G4int parentID = track->GetParentID();

// Where this track was created
G4ThreeVector vertexPos = track->GetVertexPosition();

// Volume where this track was created
auto* vertexLV = track->GetLogicalVolumeAtVertex();

G4String vertexVolumeName =
    vertexLV ? vertexLV->GetName() : "unknown";

// Current volume where this energy deposit happens
auto* currentPV = pre->GetPhysicalVolume();

G4String currentVolumeName =
    currentPV ? currentPV->GetName() : "out_of_world";

// G4cout
//     << "[WEIGHT CHECK] "
//     << "trackID = " << track->GetTrackID()
//     << " parentID = " << parentID
//     << " particle = " << track->GetParticleDefinition()->GetParticleName()
//     << " creator = " << creatorName
//     << " createdPos = " << G4BestUnit(vertexPos, "Length")
//     << " createdVolume = " << vertexVolumeName
//     << " currentVolume = " << currentVolumeName
//     << " E = " << pre->GetKineticEnergy()/keV << " keV"
//     << " edep = " << edep/keV << " keV"
//     << " trackWeight = " << track->GetWeight()
//     << " preWeight = " << pre->GetWeight()
//     << " postWeight = " << post->GetWeight()
//     << G4endl;


    G4int rootId = -1;
    if (info != nullptr) {
        rootId = info->GetRootID();
    }

    if (info ==nullptr){
        return true;
    }

    if (edep <= 0) {
        return true; 
    }
        // G4cout << "Energy deposited: " << edep / keV << " keV" << G4endl;



    // energyDepositTrackEnergy[rootId] += edep;

    energyDepositTrackWeight[rootId] = track->GetWeight();
    energyDepositTrackEnergy[rootId] += edep; 




    return true;
}

void SensitiveDetector::EndOfEvent(G4HCofThisEvent *hce){
    G4AnalysisManager* analysisManager = G4AnalysisManager::Instance();
    for(const auto& [trackId,energy]: energyDepositTrackEnergy) {
        G4double weight = energyDepositTrackWeight[trackId];
        if(energy>0){
            // G4cout << "Track ID: " << trackId << ", Energy Deposited: " << energy / keV << " keV, Weight: " << weight << G4endl;
            G4AnalysisManager* analysisManager = G4AnalysisManager::Instance();
            analysisManager->FillH1(0, energy / keV,weight);

            
        }
    }
}