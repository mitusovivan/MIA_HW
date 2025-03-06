#include <cstddef>

#include "menu_items.hpp"
#include "menu_functions.hpp"

const MIA::MenuItem MIA::STUDY_CLASS_ONE_RUSSIAN = { 
    "1 - учим русский", MIA::study_class_one_russian, &MIA::STUDY_CLASS_ONE
};
const MIA::MenuItem MIA::STUDY_CLASS_ONE_LITERATURE = {
     "2 - Изучение литературы", MIA::study_class_one_literature, &MIA::STUDY_CLASS_ONE
};
const MIA::MenuItem MIA::STUDY_CLASS_ONE_MATH = {
    "3 - Я люблю Математику", MIA::study_class_one_math, &MIA::STUDY_CLASS_ONE
};
const MIA::MenuItem MIA::STUDY_CLASS_ONE_FISCULTURE = {
    "4 - Физкульт привет мир!!!", MIA::study_class_one_fisculture, &MIA::STUDY_CLASS_ONE
};
const MIA::MenuItem MIA::STUDY_GO_BACK_1 = {
    "0 - Выйти в меню выше", MIA::study_go_back_1, &MIA::STUDY_CLASS_ONE
};

namespace {
    const MIA::MenuItem* const study_children_1[] = {
        &MIA::STUDY_GO_BACK_1,
        &MIA::STUDY_CLASS_ONE_RUSSIAN,
        &MIA::STUDY_CLASS_ONE_LITERATURE,
        &MIA::STUDY_CLASS_ONE_MATH,
        &MIA::STUDY_CLASS_ONE_FISCULTURE,
    };

    const int study_size_1 = sizeof(study_children_1) / sizeof(study_children_1[0]);
}

const MIA::MenuItem MIA::STUDY_CLASS_ONE = { 
    "1 - Изучить предметы 1-го класса", MIA::study_class_one, &MIA::STUDY, study_children_1, study_size_1
};
const MIA::MenuItem MIA::STUDY_CLASS_TWO = {
     "2 - Изучить предметы 2-го класса", MIA::study_class_two, &MIA::STUDY
};
const MIA::MenuItem MIA::STUDY_CLASS_THREE = {
    "3 - Изучить предметы 3-го класса", MIA::study_class_three, &MIA::STUDY
};
const MIA::MenuItem MIA::STUDY_GO_BACK = {
    "0 - Выйти в главное меню", MIA::study_go_back, &MIA::STUDY
};

namespace {
    const MIA::MenuItem* const study_children[] = {
        &MIA::STUDY_GO_BACK,
        &MIA::STUDY_CLASS_ONE,
        &MIA::STUDY_CLASS_TWO,
        &MIA::STUDY_CLASS_THREE,
    };

    const int study_size = sizeof(study_children) / sizeof(study_children[0]);
}

const MIA::MenuItem MIA::STUDY = {
     "1 - Предметы какого класса шлолы вы хотите учить?", MIA::show_menu, &MIA::MAIN, study_children, study_size
};
const MIA::MenuItem MIA::EXIT = {
    "0 - Я уже закончил школу, но ничего не знаю ;)", MIA::exit, &MIA::MAIN
};

namespace{
    const MIA::MenuItem*  const main_children[] = {
        &MIA::EXIT, 
        &MIA::STUDY
    };
    const int main_size = sizeof(main_children) / sizeof(main_children[0]);
}

const MIA::MenuItem MIA::MAIN = {
    nullptr, MIA::show_menu, nullptr, main_children, main_size
};

/*main.funct(&main);
int user_input;*/

/*study_class_one.parent = &study;
study_class_two.parent = &study;
study_class_three.parent = &study;
study_go_back.parent = &study;

study.parent = &main;
exit.parent = &main;*/