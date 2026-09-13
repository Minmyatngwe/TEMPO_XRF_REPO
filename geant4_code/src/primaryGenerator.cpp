#include "primaryGenerator.hh"
#include "G4ThreeVector.hh"
#include "G4AnalysisManager.hh"
#include "G4PhysicalConstants.hh"
#include "Randomize.hh"


PrimaryGenerator::PrimaryGenerator(SimulationConfig & config):fConfig(&config){

    fgun=new G4GeneralParticleSource();
    auto *source=fgun->GetCurrentSource();
    auto * posDist=source->GetPosDist();

    posDist->SetCentreCoords(fConfig->sourcePosition);
    posDist->SetPosDisType("Plane");
    posDist->SetPosDisShape("Circle");

    source->GetPosDist()->SetRadius(fConfig->focalSpotDiameter/2);

    G4ThreeVector normal=(fConfig->sampleReferencePoint-fConfig->sourcePosition).unit();
    G4ThreeVector helperVector(0,1,0);

    if (std::abs(normal.dot(helperVector))>0.99){
        helperVector=G4ThreeVector(1,0,0);
    }

    G4ThreeVector xAxis=helperVector.cross(normal).unit();
    G4ThreeVector yAxis=helperVector.cross(xAxis).unit();
    posDist->SetPosRot1(xAxis);
    posDist->SetPosRot2(yAxis);
    G4double radius=fConfig->tubeCollimatorRadius;
    fConfig->virtualTubeCollimatorArea=CLHEP::pi*radius*radius;  

    G4cout<<"Source position "<<fConfig->sourcePosition<<G4endl;
    G4cout<<"Virtual tube collimator position "<<fConfig->virtualTubeCollimatorPosition<<G4endl;

    G4cout<<"Virtual tube collimator area "<<fConfig->virtualTubeCollimatorArea<<G4endl;



}
PrimaryGenerator::~PrimaryGenerator(){
    delete fgun;
}

void PrimaryGenerator::GeneratePrimaries(G4Event *event){

    G4double randomNumber=fConfig->tubeCollimatorRadius*std::sqrt(G4UniformRand());
    G4double randomAngle=2*CLHEP::pi*G4UniformRand();
    G4ThreeVector randomBeamPointOnCollimator(
        randomNumber*std::sin(randomAngle),
        randomNumber*std::cos(randomAngle),0);
    
    G4ThreeVector randomEndingPoint(fConfig->virtualTubeCollimatorPosition+randomBeamPointOnCollimator);

    fgun->GeneratePrimaryVertex(event);
    G4PrimaryVertex* vertex = event->GetPrimaryVertex(0);
    G4PrimaryParticle* particle = vertex->GetPrimary(0);
    G4ThreeVector sourceRandomPosition=vertex->GetPosition();
    G4ThreeVector SourceDirection=(randomEndingPoint-sourceRandomPosition).unit();

    particle->SetMomentumDirection(SourceDirection.unit());

    if(event->GetEventID()<=10){
        G4cout<<"Random point on collimator  vector "<<randomBeamPointOnCollimator<<G4endl;
        G4cout<<"Random point on collimator  POSITION  "<<randomEndingPoint<<G4endl;
        G4cout<<"Source direction "<<SourceDirection<<G4endl;

        G4cout<<"Random point on focal spot "<<sourceRandomPosition<<G4endl;
        

    }
    

}