#include "physicsList.hh"
#include "G4EmParameters.hh"
#include "G4EmLivermorePhysics.hh"
#include "G4ios.hh"
#include "G4SystemOfUnits.hh"
#include "G4UnitsTable.hh"  


PhysicsList::PhysicsList(){

    RegisterPhysics(new G4EmLivermorePhysics());
    auto *parameters = G4EmParameters::Instance();
    parameters->SetFluo(true);
    parameters->SetAuger(true);
    parameters->SetPixe(true);
    parameters->SetDeexcitationIgnoreCut(true);
    parameters->SetBeardenFluoDir(true);

    parameters->SetVerbose(0);

    parameters->ActivateSecondaryBiasing("phot","SampleRegion",1000,100*MeV);
    parameters->ActivateSecondaryBiasing("compt","SampleRegion",1000,100*MeV);
    parameters->ActivateSecondaryBiasing("Rayl", "SampleRegion", 1000, 100*MeV);
    parameters->ActivateSecondaryBiasing("eBrem", "SampleRegion", 1000, 100*MeV); 

    parameters->ActivateForcedInteraction("phot",  "SampleRegion", 0.0025*mm, true);
    parameters->ActivateForcedInteraction("compt", "SampleRegion", 0.0025*mm, true);
    parameters->ActivateForcedInteraction("Rayl",  "SampleRegion", 0.0025*mm, true);

    //     parameters->SetProcessBiasingFactor("phot", 100, true);
    // parameters->SetProcessBiasingFactor("compt", 100, true);
    // parameters->SetProcessBiasingFactor("Rayl",100, true);


}
PhysicsList::~PhysicsList(){}
