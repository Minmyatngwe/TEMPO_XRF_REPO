#ifndef PHYSICSLIST_HH
#define PHYSICSLIST_HH

#include "G4VModularPhysicsList.hh"
#include "G4EmLivermorePhysics.hh"
#include "G4EmParameters.hh"

class PhysicsList:public G4VModularPhysicsList{
    public:
        PhysicsList();
        ~PhysicsList();
};

#endif