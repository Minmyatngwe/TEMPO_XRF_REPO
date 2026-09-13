#include "steppingAction.hh"
#include "trackInformation.hh"
#include "browserTrackExporter.hh"
#include "G4RunManager.hh"

SteppingAction::SteppingAction(SimulationConfig & config){
    fConfig=&config;
}

SteppingAction::~SteppingAction(){}

void SteppingAction::UserSteppingAction(const G4Step * step){

    G4Track *track=step->GetTrack();
    G4double energy=track->GetKineticEnergy();
    G4StepPoint *preStepPoint=step->GetPreStepPoint();
    G4StepPoint *postStepPoint=step->GetPostStepPoint();
    const auto * event=G4RunManager::GetRunManager()->GetCurrentEvent();
    if (event !=nullptr && event ->GetEventID()<10){
        BrowserTrackExporter::Instance().RecordStep(event->GetEventID(),track,preStepPoint->GetPosition(),postStepPoint->GetPosition());

    }

    if (!postStepPoint || !postStepPoint->GetPhysicalVolume()){
        return ;
    }

    G4String preVolumeName=preStepPoint->GetPhysicalVolume()->GetName();
    G4String postVolumeName=postStepPoint->GetPhysicalVolume()->GetName();

    if (postVolumeName==fConfig->detectorConfig.name+"_placement" && preVolumeName!=fConfig->detectorConfig.name+"_placement"){
        if(track->GetUserInformation()==nullptr){
            G4int trackID=track->GetTrackID();
            TrackInformation * info=new TrackInformation(trackID);
            track->SetUserInformation(info);

        }
    }

    TrackInformation * info=dynamic_cast<TrackInformation*>(track->GetUserInformation());
    if(info!=nullptr && preVolumeName==fConfig->detectorConfig.name+"_placement"){
        const G4int rootId=info->GetRootId();
        const auto *secondaries=step->GetSecondaryInCurrentStep();

        if(secondaries!=nullptr){
            for (const G4Track * secondary:*secondaries){
                G4Track * secondaryTrack=const_cast<G4Track*>(secondary);

                if(secondary->GetUserInformation()==nullptr){
                    auto *secondaryInfo=new TrackInformation(rootId);
                    secondaryTrack->SetUserInformation(secondaryInfo);
                }
            }
        }

    }

}


