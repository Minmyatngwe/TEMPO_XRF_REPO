cmake_minimum_required(VERSION 3.16 FATAL_ERROR)

project(XRF_ONLY)

find_package(Geant4 REQUIRED ui_all vis_all)
find_package(nlohmann_json REQUIRED)

include(${Geant4_USE_FILE})

# Source files
file(GLOB sources
    ${PROJECT_SOURCE_DIR}/src/*.cpp
)

file(GLOB MACRO_FILES
    ${PROJECT_SOURCE_DIR}/macro/*.mac
)

add_executable(
    sim
    sim.cpp
    ${sources}
)

target_include_directories(
    sim
    PRIVATE
    ${PROJECT_SOURCE_DIR}/include
)

target_link_libraries(
    sim
    PRIVATE
    ${Geant4_LIBRARIES}
    nlohmann_json::nlohmann_json
)

file(
    COPY ${MACRO_FILES}
    DESTINATION ${CMAKE_BINARY_DIR}
)

add_custom_target(
    XRF_ONLY
    DEPENDS sim
)