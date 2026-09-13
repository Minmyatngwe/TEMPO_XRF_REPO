#ifndef PRIMARYGENERATOR_HH
#define PRIMARYGENERATOR_HH

#include "G4VUserPrimaryGeneratorAction.hh"
#include "G4ParticleDefinition.hh"
#include "G4GeneralParticleSource.hh"
#include "G4SystemOfUnits.hh"
#include "G4Event.hh"
#include "simulationConfig.hh"

class PrimaryGenerator:public G4VUserPrimaryGeneratorAction{
    public:
     explicit PrimaryGenerator(SimulationConfig & config );
     ~PrimaryGenerator()override;

     void GeneratePrimaries(G4Event *event) override;

     private:
        G4GeneralParticleSource *fgun{nullptr};
        SimulationConfig * fConfig{nullptr};
};

#endif 