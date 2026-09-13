#include "sensitiveDetector.hh"
#include "trackInformation.hh"
#include "G4RunManager.hh"
#include "G4AnalysisManager.hh"
#include "G4UnitsTable.hh"
#include "G4SystemOfUnits.hh"

SensitiveDetector::SensitiveDetector():G4VSensitiveDetector("SensitiveDetector"){


}

SensitiveDetector::~SensitiveDetector()=default;


void SensitiveDetector::Initialize( G4HCofThisEvent*){
    energyDepositTrackWeight.clear();
    energyDepositTrackEnergy.clear();
}
G4bool SensitiveDetector::ProcessHits(G4Step *step ,G4TouchableHistory *hist){
    const G4double edep=step->GetTotalEnergyDeposit();
    G4Track *track=step->GetTrack();
    TrackInformation *info=dynamic_cast<TrackInformation *>(track->GetUserInformation());

    if(info==nullptr || edep<0.0){

        return false ;
    }

    const G4int rootId=info->GetRootId();
    energyDepositTrackWeight[rootId]=track->GetWeight();
    energyDepositTrackEnergy[rootId]+=edep;

    return true ;

}


void SensitiveDetector::EndOfEvent(G4HCofThisEvent  *hce){

    const G4RunManager *runManager=G4RunManager::GetRunManager();
    const G4int eventId=runManager->GetCurrentEvent()->GetEventID();
    G4AnalysisManager* analysisManager = G4AnalysisManager::Instance();

    for(const  auto&[rootId,energy]:energyDepositTrackEnergy){
        G4double weight=energyDepositTrackWeight[rootId];

        if(energy>0){
            // G4cout<<"Energy"<<energy<<"weight "<<weight<<G4endl;
            analysisManager->FillH1(0, energy / keV,weight);
            analysisManager->FillNtupleIColumn(0, eventId);
            analysisManager->FillNtupleIColumn(1, rootId);
            analysisManager->FillNtupleDColumn(2, energy/keV); 
            analysisManager->FillNtupleDColumn(3, weight);
            analysisManager->AddNtupleRow();

        }
    }

}