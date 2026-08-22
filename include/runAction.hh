#ifndef RUNACTION_HH
#define RUNCATION_HH


#include "G4UserRunAction.hh"
#include "G4Run.hh"
#include "G4AnalysisManager.hh"
#include "G4SystemOfUnits.hh"
#include "G4UnitsTable.hh"
#include "detectorConstruction.hh"
#include "simulationConfig.hh"


#include "G4Accumulable.hh"
#include "globals.hh"

class RunAction:public G4UserRunAction{
    public:
        RunAction(SimulationConfig &config);
        ~RunAction() override;
        void BeginOfRunAction(const G4Run* run) override;
        void EndOfRunAction(const G4Run* run) override;
            void AddPrimaryEnteringSample(G4double weight)
    {
        fPrimaryEnteringSample += weight;
    }

    void AddGammaEnteringSilicon(G4double weight)
    {
        fGammaEnteringSilicon += weight;
    }

    private:
        SimulationConfig &fConfig;
        G4Accumulable<G4double> fPrimaryEnteringSample = 0.0;
        G4Accumulable<G4double> fGammaEnteringSilicon = 0.0;

};  


#endif