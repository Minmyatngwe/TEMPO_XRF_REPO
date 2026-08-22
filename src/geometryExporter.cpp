#include "geometryExporter.hh"

#include "G4Colour.hh"
#include "G4ModelingParameters.hh"
#include "G4Point3D.hh"
#include "G4Polyhedron.hh"
#include "G4SystemOfUnits.hh"
#include "G4Transform3D.hh"
#include "G4VisAttributes.hh"
#include "G4VSolid.hh"
#include "G4VisExtent.hh"
#include "G4LogicalVolume.hh"
#include <fstream>


GeometryExportScene::GeometryExportScene(
    G4PhysicalVolumeModel& model,
    nlohmann::json& output
)
    :
    fModel(model),
    fOutput(output)
{
}


void GeometryExportScene::ProcessVolume(
    const G4VSolid& solid
)
{

    auto *pv=fModel.GetCurrentPV();

    if(pv==nullptr){
        return;
    }
    if(fModel.GetCurrentDepth()==0){
        

        return;
    }

    if(fpVisAttributes!=nullptr && !fpVisAttributes->IsVisible()){
        return ;    
    }



    const G4Polyhedron *polyhedron=solid.GetPolyhedron();

    if(polyhedron==nullptr||polyhedron->GetNoFacets()==0){
        return;
    }
    
    nlohmann::json volume;

    volume["name"]=pv->GetName();
    volume["copyNo"]=fModel.GetCurrentPVCopyNo();
    volume["solidName"]=solid.GetName();
    volume["solidType"]=solid.GetEntityType();
    volume["path"]=G4PhysicalVolumeModel::GetPVNamePathString(fModel.GetFullPVPath());

    if(fpVisAttributes!=nullptr){

        const auto &color=fpVisAttributes->GetColour();
        volume["color"]={color.GetRed(),color.GetGreen(),color.GetBlue()};
        volume["opacity"]=color.GetAlpha();

    }
    else{
        volume["color"]={0.8,0.8,0.8};
        volume["opacity"]=1.0;
    }


    volume["triangles"]=nlohmann::json::array();
    volume["edges"]=nlohmann::json::array();


    if(fpCurrentObjectTransformation==nullptr){
        return;
    }

    const auto& transform=*fpCurrentObjectTransformation;
    G4Point3D vertices[4];
    G4Normal3D normals[4];
    G4int edgeFlags[4];
    G4bool moreFacets;
    G4int nVertices=0;

    do{
        
        moreFacets=polyhedron->GetNextFacet(
            nVertices,
            vertices,
            edgeFlags,
            normals
        );

        if(nVertices<3){
            continue;
        }

        G4Point3D worldVertex[4];

        for(G4int i=0;i<nVertices;i++){
            worldVertex[i]=transform*vertices[i];
        }

        for(G4int i=1;i<nVertices-1;i++){

            volume["triangles"].push_back(
                {
                    worldVertex[0].x()/mm,
                    worldVertex[0].y()/mm,
                    worldVertex[0].z()/mm,


                    worldVertex[i].x()/mm,
                    worldVertex[i].y()/mm,
                    worldVertex[i].z()/mm,

                    worldVertex[i+1].x()/mm,
                    worldVertex[i+1].y()/mm,
                    worldVertex[i+1].z()/mm
                }
            );

        }

        for(G4int i=0;i<nVertices;i++){
            G4int next=(i+1)%nVertices;
            if(edgeFlags[i]<=0){
                continue;
            }

            volume["edges"].push_back({
                worldVertex[i].x()/mm,
                worldVertex[i].y()/mm,
                worldVertex[i].z()/mm,

                worldVertex[next].x()/mm,
                worldVertex[next].y()/mm,
                worldVertex[next].z()/mm

            });
        }




    }while(moreFacets);

    fOutput["volumes"].push_back( std::move(volume));

}


void ExportGeometryForBrowser(
    G4VPhysicalVolume* world,
    const std::string& filename,
    G4int segmentsPerCircle
)
{
    if (world == nullptr) {
        return;
    }

    auto* worldSolid =world->GetLogicalVolume()->GetSolid();

    const auto extent =worldSolid->GetExtent();
    nlohmann::json output;

    output["world"] = {
        {"xmin", extent.GetXmin() / mm},
        {"xmax", extent.GetXmax() / mm},

        {"ymin", extent.GetYmin() / mm},
        {"ymax", extent.GetYmax() / mm},

        {"zmin", extent.GetZmin() / mm},
        {"zmax", extent.GetZmax() / mm}
    };
    // Same concept as:
    // /vis/viewer/set/lineSegmentsPerCircle 48

    G4Polyhedron::SetNumberOfRotationSteps(
        segmentsPerCircle
    );


    // Default visual attributes for volumes which

    G4VisAttributes defaultVis(
        G4Colour(
            0.8,
            0.8,
            0.8,
            1.0
        )
    );


    // Modeling parameters

    G4ModelingParameters modelingParameters(

        &defaultVis,

        G4ModelingParameters::wf,

        false,  // global culling
        false,  // cull invisible
        false,  // density culling

        0.0,

        false,  // cull daughters of opaque mothers

        segmentsPerCircle
    );


    // This is Geant4's own geometry visualization traversal.
    G4PhysicalVolumeModel model(

        world,

        G4PhysicalVolumeModel::UNLIMITED,

        G4Transform3D(),

        &modelingParameters,

        true
    );



    output["format"] =
        "geant4-polyhedron";

    output["units"] =
        "mm";

    output["segmentsPerCircle"] =
        segmentsPerCircle;

    output["volumes"] =
        nlohmann::json::array();


    GeometryExportScene scene(
        model,
        output
    );


    model.DescribeYourselfTo(
        scene
    );


    std::ofstream file(
        filename
    );

    file<< output.dump(2);

    file.close();


    G4cout
        << "Browser geometry exported to: "
        << filename
        << G4endl;
}