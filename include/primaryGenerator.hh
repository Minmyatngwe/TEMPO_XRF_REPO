#ifndef PRIMARYGENERATOR_HH
#define PRIMARYGENERATOR_HH

#include "G4VUserPrimaryGeneratorAction.hh"
#include "G4ParticleDefinition.hh"
#include "G4SystemOfUnits.hh"
#include "G4GeneralParticleSource.hh"
#include "G4Event.hh"
#include "G4Gamma.hh"
#include "G4ParticleGun.hh"
#include "G4SystemOfUnits.hh"
#include "Randomize.hh"
#include <cmath>
#include "simulationConfig.hh"
#include "G4AutoLock.hh"

class PrimaryGenerator:public G4VUserPrimaryGeneratorAction{

    public:
        PrimaryGenerator(SimulationConfig& config);
        
        ~PrimaryGenerator()override;
        
        void GeneratePrimaries(G4Event* event) override;

        void CalulateSourcePositionAndDirection();

    private:
        G4GeneralParticleSource *fgun{nullptr};
        SimulationConfig *fConfig{nullptr};

        G4ThreeVector SourcePosition;
        G4ThreeVector SourceDirection;
};


#endif