#include "runAction.hh"

#include "steppingAction.hh"

RunAction::RunAction(SimulationConfig &config): fConfig(config){

    auto* analysismanager = G4AnalysisManager::Instance();
    analysismanager->SetNtupleMerging(true);
analysismanager->CreateH1("Edep", "Total Energy Deposited", 10000, 0., 100);   
analysismanager->CreateH1("beforeentering", "Total Energy Deposited", 10000, 0., 100);    

}

RunAction::~RunAction() = default;

void RunAction::BeginOfRunAction(const G4Run* run){
    auto *analysismanager = G4AnalysisManager::Instance();
    analysismanager->OpenFile(fConfig.outputFileName);
    G4cout<<"Output file: "<<fConfig.outputFileName<<G4endl;
    // BeginOfRunAction
// SteppingAction::ResetFirstInteractionCounters();


}
void RunAction::EndOfRunAction(const G4Run* run){
    auto *analysismanager = G4AnalysisManager::Instance();
    analysismanager->Write();
    analysismanager->CloseFile();
    // EndOfRunAction
// SteppingAction::PrintFirstInteractionCounters();
}