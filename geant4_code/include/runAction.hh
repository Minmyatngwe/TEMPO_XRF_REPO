#ifndef RUNACTION_HH
#define RUNACTION_HH

#include "G4UserRunAction.hh"
#include "globals.hh"
#include "G4SystemOfUnits.hh"
#include "G4AnalysisManager.hh"
#include "simulationConfig.hh"


class RunAction:public G4UserRunAction{
    public:
        explicit RunAction (SimulationConfig &config);
        ~RunAction() override;
        void BeginOfRunAction(const G4Run* run)override;
        void EndOfRunAction(const G4Run * run) override;
        

    private:
        SimulationConfig *fConfig{nullptr};

};

#endif 
