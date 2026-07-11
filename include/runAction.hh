#ifndef RUNACTION_HH
#define RUNCATION_HH


#include "G4UserRunAction.hh"
#include "G4Run.hh"
#include "G4AnalysisManager.hh"
#include "G4SystemOfUnits.hh"
#include "G4UnitsTable.hh"
#include "detectorConstruction.hh"
#include "simulationConfig.hh"



class RunAction:public G4UserRunAction{
    public:
        RunAction(SimulationConfig &config);
        ~RunAction() override;
        void BeginOfRunAction(const G4Run* run) override;
        void EndOfRunAction(const G4Run* run) override;
    private:
        SimulationConfig &fConfig;
};  


#endif