import * as THREE from "three"

import {OrbitControls} from "three/addons/controls/OrbitControls.js"
import {CSS2DRenderer,CSS2DObject} from "three/addons/renderers/CSS2DRenderer.js"

const scene=new THREE.Scene()
let axisNumber=50
const axisGroup=new THREE.Group()
const wireframeGroup=new THREE.Group()
const surfaceGroup=new THREE.Group()
const trackGroup=new THREE.Group()
scene.add(wireframeGroup)
scene.add(axisGroup)
scene.add(surfaceGroup)
scene.add(trackGroup)
scene.background=new THREE.Color(0x202020)


const renderer=new THREE.WebGLRenderer({antialias: true})

const labelRenderer=new CSS2DRenderer()


const camera=new THREE.PerspectiveCamera(
            45, 
            window.innerWidth/window.innerHeight,
            0.1,
            5000
            )
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(
    Math.min(window.devicePixelRatio, 2)
);
labelRenderer.setSize(window.innerWidth,window.innerHeight)
labelRenderer.domElement.style.position="absolute"
labelRenderer.domElement.style.top="0px"
labelRenderer.domElement.style.pointerEvents="none"

document.body.appendChild(labelRenderer.domElement)

window.addEventListener(
    "resize",()=>{
        console.log("New window width", window.innerWidth);
    console.log("New window height", window.innerHeight);
    
    renderer.setSize(window.innerWidth, window.innerHeight);
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    labelRenderer.setSize(window.innerWidth,window.innerHeight)

    }
    
)

const checkBoxXYZ=document.getElementById("showXYZAxis")
const seletboxsurface=document.getElementById("volume")
const checkBoxBeamDirection=document.getElementById("showBeam")
const debugElement=document.getElementById("debug-output")


seletboxsurface.addEventListener("change",updateVolumeSurface)

checkBoxXYZ.addEventListener("change",updateAxis)
checkBoxBeamDirection.addEventListener("change",updateBeamDirection)
    

document.body.appendChild(renderer.domElement)


const controls=new OrbitControls(camera,renderer.domElement)
controls.target.set(0,0,0)
controls.update()
await loadGeometry("/xrf_geometry_vis.json")
camera.near = axisNumber / 1000;
camera.far = axisNumber * 10;
camera.updateProjectionMatrix();
camera.position.z=axisNumber
camera.position.y=axisNumber
camera.position.x=axisNumber

const ambientLight =
    new THREE.AmbientLight(
        0xffffff,
        1.5
    );

scene.add(ambientLight);
showBeamDirection("xrf_tracks.json")

createAxis()
updateAxis()
updateBeamDirection()
updateVolumeSurface()
loadDebugLogFile("/geant4_debug.log")
animate()

function updateBeamDirection(){
    if(checkBoxBeamDirection.checked){
        trackGroup.visible=true
    }
    else(
        trackGroup.visible=false
    )
}
function updateVolumeSurface(){
    if(seletboxsurface.value=="wireframe"){
        surfaceGroup.visible=false
        wireframeGroup.visible=true
    }
    else{
        surfaceGroup.visible=true
        wireframeGroup.visible=false
    }

}

async function  loadDebugLogFile(filename) {
    try{
        const response=await fetch(filename)
        if (!response.ok){
            console.error("Could not load",filename)
            return
        }
        const text=await response.text()
        debugElement.innerHTML =text

    }
    catch (error) {

        console.error(
            "Failed to read debug log:",
            error
        )

    }


    

    
}
async function showBeamDirection(filename){
    const response=await fetch(filename)
    if (!response.ok){
        console.error("Could not load",filename)
        return
    }
    const data=await response.json()
    for(const track of data.tracks){
        const points=[]
        for(const point of track.points){
            points.push(new THREE.Vector3(point[0],point[1],point[2]))
        }
        const geometry=new THREE.BufferGeometry().setFromPoints(points)
        const material =
            new THREE.LineBasicMaterial({
                color: 0xffff00
            });

        const line =
            new THREE.Line(
                geometry,
                material
            );

        trackGroup.add(line);


    }
}
async function loadGeometry(filename) {

    const response = await fetch(filename);

    if (!response.ok) {
        console.error("Could not load:", filename)
        return
    }

    const data = await response.json()

    for (const volume of data.volumes) {

        const wireframePositions = [];
        const surfacePositions=[]

        for(const triangle of volume.triangles){
            surfacePositions.push(...triangle)
        }

        for (const edge of volume.edges) {
            wireframePositions.push(...edge)
        }

        const wireframegeometry = new THREE.BufferGeometry()

        wireframegeometry.setAttribute(
            "position",
            new THREE.Float32BufferAttribute(
                wireframePositions,
                3
            )
        );

        const wireframematerial = new THREE.LineBasicMaterial({
            color: new THREE.Color(
                volume.color[0],
                volume.color[1],
                volume.color[2]
            )
        })

        const wireframe = new THREE.LineSegments(
            wireframegeometry,
            wireframematerial
        );

        wireframe.name = volume.name;

        wireframeGroup.add(wireframe);

        const surfaceGeometry=new THREE.BufferGeometry()
        surfaceGeometry.setAttribute("position",
            new THREE.Float32BufferAttribute(surfacePositions,3)
        )
        const surfaceMaterial=new THREE.MeshBasicMaterial({
            color:new THREE.Color(
                volume.color[0],
                volume.color[1],
                volume.color[2]
                )
            }
        )
        const surface=new THREE.Mesh(
            surfaceGeometry,surfaceMaterial
        )

        surfaceGroup.add(surface)

    }
    const world=data.world
    axisNumber=Math.max(
            Math.abs(world.xmin),
            Math.abs(world.xmax),
            Math.abs(world.ymin),
            Math.abs(world.ymax),
            Math.abs(world.zmin),
            Math.abs(world.zmax)

    )
    console.log(axisNumber)

}
function createAxis(){
    console.log(axisNumber)

    const axesHelper=new THREE.AxesHelper(axisNumber)

    axisGroup.add(axesHelper)
    axisGroup.add(createLable("X", axisNumber+30, 0, 0));
    axisGroup.add(createLable("Y", 0, axisNumber+30, 0));
    axisGroup.add(createLable("Z", 0, 0, axisNumber+30));

    const gap = axisNumber / 10;

    for (let i = 1; i <= 10; i++) {

        axisGroup.add(
            createLable(`${gap * i}`, gap * i, 0, 0)
        );

        axisGroup.add(
            createLable(`${gap * i}`, 0, gap * i, 0)
        );

        axisGroup.add(
            createLable(`${gap * i}`, 0, 0, gap * i)
        );
    }


}
function updateAxis(){
    axisGroup.visible=checkBoxXYZ.checked
}

    

function createLable(text,x,y,z){
    const div=document.createElement("div")
    div.textContent=text
    div.style.color="white"
    div.style.fontSize="15px"
    const label=new CSS2DObject(div)
    label.position.set(x,y,z)
    return label
}

function animate() {
    controls.update()
    renderer.render(scene, camera);
    labelRenderer.render(scene, camera);

    requestAnimationFrame(animate);

}
