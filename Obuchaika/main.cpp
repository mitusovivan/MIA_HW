#include <iostream>

#include "menu.hpp"
#include "menu_functions.hpp"
#include "menu_items.hpp"


int main(){
    const MIA::MenuItem* current = &MIA::MAIN;
    do {
        current = current->funct(current);
    }while (true);
    
    return 0;    
}

        /*std::cout << "Главное Меню:" << std::endl;
        for (int i = 1; i < main_size; i++){
            std::cout << main_children[i]->title << std::endl;
        }
        std::cout << main_children[0]->title << std::endl;
        std::cout << "Unknown type > ";*/

        /*std::cin >> user_input;
        std::cout << std::endl;

        main.children[user_input]->funct(main.children[user_input]);
    */
       //std::setlocale(LC_ALL, "");
       //#include <clocale>