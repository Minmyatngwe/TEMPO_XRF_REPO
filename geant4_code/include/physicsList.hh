#ifndef PHYSICSLIST_HH
#define PHYSICSLIST_HH

#include "G4VModularPhysicsList.hh"
#include "G4EmLivermorePhysics.hh"
#include "G4EmParameters.hh"
#include "simulationConfig.hh"

class PhysicsList:public G4VModularPhysicsList{
    public:
        PhysicsList(SimulationConfig & config );
        ~PhysicsList();
            void ConstructProcess() override;
    void SetCuts() override;

    private: 
        SimulationConfig *fConfig {nullptr};
};

#endif