project(Algorithm)

add_executable(${PROJECT_NAME} main.cpp)
set(DATA_FILES
    ${CMAKE_CURRENT_SOURCE_DIR}/names/men_Names.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/names/men_Fam.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/names/men_fNames.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/names/wmen_Names.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/names/wmen_Fam.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/names/wmen_fNames.txt
    ${CMAKE_CURRENT_SOURCE_DIR}/trains/trains.csv
)

# Копируем файлы в директорию, куда помещается исполняемый файл (Algorithm.exe)
file(COPY ${DATA_FILES} DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/../../build_Ninja/Project)
add_subdirectory(names)
add_subdirectory(trains)
