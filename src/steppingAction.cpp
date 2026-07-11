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

SteppingAction::SteppingAction(SimulationConfig & config) : G4UserSteppingAction(),fConfig(&config) {}

SteppingAction::~SteppingAction() {}


G4double SteppingAction::GetCrossSectionPerVolume(G4double energy,G4String processName){
    G4EmCalculator emCal;
    const G4ParticleDefinition* gamma = G4Gamma::GammaDefinition();
    const G4Material* mat = fConfig->sampleMat;

    G4double mu  = emCal.ComputeCrossSectionPerVolume(energy,gamma,processName,mat);
    return mu ;
}

G4double SteppingAction::CalculateDistancePhotonNeedToTravelInSample(G4Track* track){
    //need to change for mesth file uploade


    // auto logicalVolumeStore = G4LogicalVolumeStore::GetInstance();
    // auto logicalVolume = logicalVolumeStore->GetVolume("sampleLogic");

    // auto box = dynamic_cast<G4Box*>(logicalVolume->GetSolid());


    // G4double X=box->GetXHalfLength();
    // G4double Y=box->GetYHalfLength();

    G4ThreeVector XAxisVector(1*mm,0,0);
    G4ThreeVector YAxisVector(0,1*mm,0);
    G4ThreeVector NormalVector=XAxisVector.cross(YAxisVector).unit();
    G4ThreeVector safeSourcePosition = track->GetVertexPosition();
    G4ThreeVector safeSourceDirection = track->GetVertexMomentumDirection();

    G4double theta=(-safeSourceDirection).angle(NormalVector);
    G4double distance=fConfig->sampleMaterialSize.z()/std::cos(theta);
    // G4cout<<"Sample thickness: "<<fConfig->sampleMaterialSize.z()/mm<<" mm"<<G4endl;
    // G4cout<<"normal vector: "<<NormalVector<<G4endl;
    // G4cout<<"source position: "<<safeSourcePosition<<G4endl;
    // G4cout<<"source direction: "<<safeSourceDirection<<G4endl;
    // G4cout<<"X axis vector: "<<XAxisVector<<G4endl;
    // G4cout<<"Y axis vector: "<<YAxisVector<<G4endl;
    //     G4cout<<"theta: "<<theta/deg<<G4endl;


    // G4cout<<"Distance photon need to travel in sample: "<<distance/mm<<" mm"<<G4endl;
    return distance;


}
void SteppingAction::UserSteppingAction(const G4Step* step) {
    
    G4Track* track = step->GetTrack();

    G4double energy = track->GetKineticEnergy();

    G4ThreeVector position = track->GetPosition();

    if (position.z()<-5*cm||position.x()<-5*cm){
        track->SetTrackStatus(fStopAndKill);
    }

    G4StepPoint *preStepPoint = step->GetPreStepPoint();

    G4StepPoint *postStepPoint = step->GetPostStepPoint();

    if (!postStepPoint || !postStepPoint->GetPhysicalVolume()) {
        return;
        }
    G4String preVolumeName = preStepPoint->GetPhysicalVolume()->GetName();
    G4String postVolumeName = postStepPoint->GetPhysicalVolume()->GetName();

    if(postVolumeName=="detectorPhys" && preVolumeName!="detectorPhys"){
        if(track->GetUserInformation()==nullptr){
            G4int trackID = track->GetTrackID();
            
            TrackInformation *info=new TrackInformation(trackID);
            track->SetUserInformation(info);
        }

    }
    TrackInformation *info=dynamic_cast<TrackInformation*>(track->GetUserInformation());

    if (info!=nullptr){

        G4int rootId=info->GetRootID();
        const G4TrackVector* secondaries = fpSteppingManager->GetSecondary();
        if(secondaries!=nullptr){
            for (size_t i = 0; i < secondaries->size(); ++i) {
                G4Track *secondaryTrack = (*secondaries)[i];
                if(secondaryTrack->GetUserInformation()==nullptr){
                    TrackInformation *secondaryInfo=new TrackInformation(rootId);
                    secondaryTrack->SetUserInformation(secondaryInfo);
                }
            }
        }
    }
    if (preVolumeName == "samplePhys" &&
        track->GetParentID() == 0 &&
        track->GetParticleDefinition()->GetParticleName() == "gamma")
    {
        const G4VProcess* proc = postStepPoint->GetProcessDefinedStep();

        if (proc == nullptr) return;

        G4String procName = proc->GetProcessName();

        if (procName == "Transportation") return;

        if (procName != "phot" &&
            procName != "compt" &&
            procName != "Rayl")
        {
            return;
        }

        G4double energy = preStepPoint->GetKineticEnergy();

        G4double oldWeight = preStepPoint->GetWeight();

        G4double distanceNeedToTravel =
            CalculateDistancePhotonNeedToTravelInSample(track);

        G4double mu_phot  = GetCrossSectionPerVolume(energy, "phot");
        G4double mu_compt = GetCrossSectionPerVolume(energy, "compt");
        G4double mu_rayl  = GetCrossSectionPerVolume(energy, "Rayl");

        G4double mu_total = mu_phot + mu_compt + mu_rayl;

        // G4cout<<"mu_phot: "<<mu_phot<<" mm^-1"<<G4endl;
        // G4cout<<"mu_compt: "<<mu_compt<<" mm^-1"<<G4endl;
        // G4cout<<"mu_rayl: "<<mu_rayl<<" mm^-1"<<G4endl;
        // G4cout<<"mu_total: "<<mu_total<<" mm^-1"<<G4endl;

        if (mu_total <= 0.0) return;

        G4double p_any = 1.0 - std::exp(-mu_total * distanceNeedToTravel);

        G4double p_real_process = 0.0;

        if (procName == "phot") {
            p_real_process = p_any * mu_phot / mu_total;
        }
        else if (procName == "compt") {
            p_real_process = p_any * mu_compt / mu_total;
        }
        else if (procName == "Rayl") {
            p_real_process = p_any * mu_rayl / mu_total;
        }

        G4double p_forced_process = 1.0 / 3.0;

        G4double newWeight =oldWeight* p_real_process / p_forced_process;

        track->SetWeight(newWeight);
        preStepPoint->SetWeight(newWeight);
        postStepPoint->SetWeight(newWeight);

        const G4TrackVector* secondaries = fpSteppingManager->GetSecondary();

        if (secondaries != nullptr) {   
            for (size_t i = 0; i < secondaries->size(); ++i) {
                G4Track* secondaryTrack = (*secondaries)[i];
                secondaryTrack->SetWeight(newWeight);
            }
        }

        // G4cout
        //     << "[WEIGHT SET] proc = " << procName
        //     << " E = " << energy / keV << " keV"
        //     << " oldWeight = " << oldWeight
        //     << " p_any = " << p_any
        //     << " p_real_process = " << p_real_process
        //     << " p_forced_process = " << p_forced_process
        //     << " newWeight = " << newWeight
        //     << " secondaries = "
        //     << (secondaries ? secondaries->size() : 0)
        //     << G4endl;
    }
        
}
