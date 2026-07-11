cmake_minimum_required(VERSION 3.2 FATAL_ERROR)

project(XRF_ONLY)
find_package(Geant4 REQUIRED ui_all vis_all)

include(${Geant4_USE_FILE} )
include_directories(${PROJECT_SOURCE_DIR}/include)
file(GLOB sources ${PROJECT_SOURCE_DIR}/src/*.cpp)
file(GLOB MACRO_FILE "macro/*.mac")

file(COPY ${MACRO_FILE} DESTINATION ${CMAKE_BINARY_DIR})

add_executable(sim sim.cpp ${sources})
target_link_libraries(sim ${Geant4_LIBRARIES})
add_custom_target(XRF_ONLY Depends sim)