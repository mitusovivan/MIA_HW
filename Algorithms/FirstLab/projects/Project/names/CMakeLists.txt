target_sources(Algorithm
    PRIVATE
        generator.cpp;
        generator.hpp;
        men_Fam.txt;
        men_fNames.txt;
        men_Names.txt;
        wmen_Fam.txt;
        wmen_fNames.txt;
        wmen_Names.txt;
        

)

target_include_directories(Algorithm PRIVATE
    "${PROJECT_SOURCE_DIR}/names"
)