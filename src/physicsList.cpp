#include "physicsList.hh"
#include "G4EmParameters.hh"
#include "G4EmLivermorePhysics.hh"
#include "G4ios.hh"
#include "G4SystemOfUnits.hh"
#include "G4UnitsTable.hh"  
#include "G4EmStandardPhysics_option4.hh"
#include "G4GenericBiasingPhysics.hh"
#include "G4RegionStore.hh"
#include "G4Region.hh"
#include "G4ProductionCuts.hh"
#include "G4Exception.hh"
PhysicsList::PhysicsList(SimulationConfig & config):fConfig(&config){

    RegisterPhysics(new G4EmStandardPhysics_option4());
    auto *parameters = G4EmParameters::Instance();
    if(fConfig->isInteractionBiasingUse){
        G4cout<<"Interaction bais is used"<<G4endl;
        auto * genericBiasing=new G4GenericBiasingPhysics();
        genericBiasing->Bias("gamma");
        RegisterPhysics(genericBiasing);

    }


}

void PhysicsList::ConstructProcess()
{
    auto* parameters = G4EmParameters::Instance();

    parameters->SetFluo(fConfig->isFluorescenceUse);
    parameters->SetAuger(fConfig->isAugerUse);
    parameters->SetPixe(fConfig->isPixeUse);
    parameters->SetDeexcitationIgnoreCut(fConfig->isIgnoreCutUse);

    if(fConfig->fluDatasetName=="ANSTO"){
        parameters->SetANSTOFluoDir(true);

    }
    else if(fConfig->fluDatasetName=="Bearden"){
        parameters->SetBeardenFluoDir(true);

    }
    else if(fConfig->fluDatasetName=="RoboAI"){
        
    }

    else{
        G4Exception(
            "PhysicsList::ConstructProcess",
            "FluDataset",
            FatalException,
            "FluDataset name is not defined (ANSTO,Bearden,RoboAI)."
        );


    }
    if(fConfig->debug){
        parameters->SetVerbose(1);  

    }
    else{
        parameters->SetVerbose(0);  

    }


    if (fConfig->isSecondarySplittingUse) {
            G4cout
                << "Splitting bias use during initialization = "
                << G4endl;

        G4double maxEnergy=fConfig->maximumEnergy;

        parameters->ActivateSecondaryBiasing(
            "phot",
            "SampleRegion",
            fConfig->photoelectricFactor,
            maxEnergy
        );

        parameters->ActivateSecondaryBiasing(
            "compt",
            "SampleRegion",
            fConfig->comptFactor,
            maxEnergy
        );

        parameters->ActivateSecondaryBiasing(
            "Rayl",
            "SampleRegion",
            fConfig->rayleighFactor,
            maxEnergy
        );

    }

    G4VModularPhysicsList::ConstructProcess();
}


PhysicsList::~PhysicsList(){}
void PhysicsList::SetCuts()
{
    SetCutsWithDefault();

    G4Region* sampleRegion =
        G4RegionStore::GetInstance()->GetRegion(
            "SampleRegion",
            false
        );

    if (sampleRegion == nullptr)
    {
        G4Exception(
            "PhysicsList::SetCuts",
            "SampleRegionNotFound",
            FatalException,
            "SampleRegion could not be found."
        );

        return;
    }

    
    auto* sampleCuts = new G4ProductionCuts();

    sampleCuts->SetProductionCut(
         fConfig->gammaCut,
        G4ProductionCuts::GetIndex("gamma")
    );

    sampleCuts->SetProductionCut(
        fConfig->electronCut,
        G4ProductionCuts::GetIndex("e-")
    );

    sampleCuts->SetProductionCut(
       fConfig->positronCut,
        G4ProductionCuts::GetIndex("e+")
    );

    sampleCuts->SetProductionCut(
       fConfig->protonCut,
        G4ProductionCuts::GetIndex("proton")
    );

    sampleRegion->SetProductionCuts(sampleCuts);

    G4cout
        << "[SAMPLE CUTS CREATED] pointer = "
        << static_cast<const void*>(sampleCuts)
        << G4endl;
}