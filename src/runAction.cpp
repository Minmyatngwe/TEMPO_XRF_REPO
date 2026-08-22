#include "runAction.hh"

#include "steppingAction.hh"
#include "G4AccumulableManager.hh"
#include "G4Run.hh"
#include "G4ios.hh"
#include "browserTrackExporter.hh"

#include "G4Threading.hh"

RunAction::RunAction(SimulationConfig &config): fConfig(config){

    auto* analysismanager = G4AnalysisManager::Instance();
    analysismanager->SetNtupleMerging(true);
    analysismanager->CreateH1("Edep", "Total Energy Deposited", 10000, 0., 100);   
    analysismanager->CreateNtuple("MyTree", "Energy deposition"); 
    analysismanager->CreateNtupleIColumn("EventId"); 
    analysismanager->CreateNtupleIColumn("rootId");  
    analysismanager->CreateNtupleDColumn("Energy"); 
    analysismanager->CreateNtupleDColumn("Weight");  
    analysismanager->FinishNtuple();


    auto* manager = G4AccumulableManager::Instance();

    manager->Register(fPrimaryEnteringSample);
    manager->Register(fGammaEnteringSilicon);

}

RunAction::~RunAction() = default;

void RunAction::BeginOfRunAction(const G4Run* run){
    auto *analysismanager = G4AnalysisManager::Instance();
    analysismanager->OpenFile(fConfig.outputFileName);
    G4cout<<"Output file: "<<fConfig.outputFileName<<G4endl;

    G4AccumulableManager::Instance()->Reset();

if (
    !G4Threading::IsWorkerThread()
)
{
    BrowserTrackExporter::
        Instance()
        .Clear();


    BrowserTrackExporter::
        Instance()
        .SetMaxEvents(
            10
        );
}
}
void RunAction::EndOfRunAction(const G4Run* run){
    auto *analysismanager = G4AnalysisManager::Instance();
    analysismanager->Write();
    analysismanager->CloseFile();
    auto* manager = G4AccumulableManager::Instance();
    manager->Merge();

    if (!IsMaster()) {
        return;
    }

    const G4double beamOn =
        static_cast<G4double>(run->GetNumberOfEvent());

    const G4double primaryEnteringSample =
        fPrimaryEnteringSample.GetValue();

    const G4double gammaEnteringSilicon =
        fGammaEnteringSilicon.GetValue();

    G4cout
        << G4endl
        << " TRANSPORT COUNTERS"
        << G4endl
        << "Beam-on events: "
        << beamOn
        << G4endl
        << "Weighted primary photons entering sample: "
        << primaryEnteringSample
        << G4endl
        << "Primary sample-entry fraction: "
        << (
            beamOn > 0.0
                ? primaryEnteringSample / beamOn
                : 0.0
        )
        << G4endl
        << "Weighted gamma photons entering silicon: "
        << gammaEnteringSilicon
        << G4endl
        << "Gamma-to-silicon yield per primary: "
        << (
            beamOn > 0.0
                ? gammaEnteringSilicon / beamOn
                : 0.0
        )
        << G4endl
        << "========================================"
        << G4endl;
    if (
        !G4Threading::IsWorkerThread()
    )
        {
            BrowserTrackExporter::
                Instance()
                .Write(
                    fConfig.parentFilePath/"xrf_tracks.json"
                );
        }
}