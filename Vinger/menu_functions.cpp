#include "menu_functions.hpp"

#include <cstdlib>
#include <iostream>

const MIA::MenuItem* MIA::show_menu(const MenuItem* current){
    std::cout << "Приветствую, юнный подаван:" << std::endl;
    for (int i = 1; i < current->children_count; i++){
        std::cout << current->children[i]->title << std::endl;
    }
    std::cout << current->children[0]->title << std::endl;
    std::cout << "Unknown type > ";

    int user_input;
    std::cin >> user_input;
    std::cout << std::endl;

    return current->children[user_input];
}

const MIA::MenuItem* MIA::exit(const MenuItem* current){
    std::exit(0);
}

const MIA::MenuItem* MIA::study_go_back(const MenuItem* current){
    std::cout << current->title << std::endl << std::endl;
    return current->parent->parent;
}

const MIA::MenuItem* MIA::study_class_one(const MenuItem* current){
    std::cout << "Ну что ж, выбирай: " << std::endl;
    for (int i = 1; i < current->children_count; i++){
        std::cout << current->children[i]->title << std::endl;
    }
    std::cout << current->children[0]->title << std::endl;
    std::cout << "Unknown type > ";

    int user_input;
    std::cin >> user_input;
    std::cout << std::endl;

    return current->children[user_input];
}
const MIA::MenuItem* MIA::study_class_two(const MenuItem* current){
    std::cout << current->title << std::endl << std::endl;
    return current->parent;
}
const MIA::MenuItem* MIA::study_class_three(const MenuItem* current){
    std::cout << current->title << std::endl << std::endl;
    return current->parent;
}




const MIA::MenuItem* MIA::study_go_back_1(const MenuItem* current){
    std::cout << current->title << std::endl << std::endl;
    return current->parent->parent;
}

const MIA::MenuItem* MIA::study_class_one_russian(const MenuItem* current){
    std::cout << current->title << std::endl << std::endl;
    return current->parent;
}
const MIA::MenuItem* MIA::study_class_one_literature(const MenuItem* current){
    std::cout << current->title << std::endl << std::endl;
    return current->parent;
}
const MIA::MenuItem* MIA::study_class_one_math(const MenuItem* current){
    std::cout << current->title << std::endl << std::endl;
    return current->parent;
}

const MIA::MenuItem* MIA::study_class_one_fisculture(const MenuItem* current){
    std::cout << current->title << std::endl << std::endl;
    return current->parent;
}

/*const MIA::MenuItem* MIA::study(){

}*/