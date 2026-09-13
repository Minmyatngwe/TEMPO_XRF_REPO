#include "runAction.hh"
#include "browserTrackExporter.hh"

RunAction::RunAction(SimulationConfig & config):fConfig{&config}{


    auto *analysisManager=G4AnalysisManager::Instance();
    analysisManager->SetNtupleMerging(true);

    analysisManager->CreateH1("Edep", "Total Energy Deposited", 10000, 0., 100);   
    analysisManager->CreateNtuple("MyTree", "Energy deposition"); 
    analysisManager->CreateNtupleIColumn("EventId"); 
    analysisManager->CreateNtupleIColumn("rootId");  
    analysisManager->CreateNtupleDColumn("Energy"); 
    analysisManager->CreateNtupleDColumn("Weight");  
    analysisManager->FinishNtuple();


};


RunAction::~RunAction()=default;

void RunAction::BeginOfRunAction(const G4Run *run){
    auto *analysisManager=G4AnalysisManager::Instance();
    analysisManager->OpenFile(fConfig->parentFilePath+"/simulation.root");

    if(!G4Threading::IsWorkerThread()){
        BrowserTrackExporter::Instance().Clear();
        BrowserTrackExporter::Instance().SetMaxEvents(10);
        
    }
}

void RunAction::EndOfRunAction(const G4Run * run){

    auto *analysisManager=G4AnalysisManager::Instance();
    analysisManager->Write();
    analysisManager->CloseFile();

    if(!IsMaster()){
        return;
    }

    BrowserTrackExporter::Instance().Write("../../roboaixrf/vis/public/xrf_tracks.json");
    G4cout<<"Done recording"<<G4endl;

}
