#pragma once

#include "menu.hpp"

namespace MIA {
    const MenuItem* show_menu(const MenuItem* current);
    
    const MenuItem* exit(const MenuItem* current);

    const MenuItem* study_go_back(const MenuItem* current);
    const MenuItem* study_class_one(const MenuItem* current);
    const MenuItem* study_class_two(const MenuItem* current);
    const MenuItem* study_class_three(const MenuItem* current);

    const MenuItem* study_go_back_1(const MenuItem* current);
    const MenuItem* study_class_one_russian(const MenuItem* current);
    const MenuItem* study_class_one_literature(const MenuItem* current);
    const MenuItem* study_class_one_math(const MenuItem* current);
    const MenuItem* study_class_one_fisculture(const MenuItem* current);
}

    //const MenuItem* study();