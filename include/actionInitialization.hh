#ifndef ACTIONINITIALIZATION_HH
#define ACTIONINITIALIZATION_HH

#include "G4VUserActionInitialization.hh"
#include "simulationConfig.hh"


class ActionInitialization:public G4VUserActionInitialization
{
    public:
        ActionInitialization(SimulationConfig& config):fConfig(&config){};
        virtual ~ActionInitialization();

        virtual void Build() const override;
        virtual void BuildForMaster() const override;
        SimulationConfig *fConfig{nullptr};
};
#endif