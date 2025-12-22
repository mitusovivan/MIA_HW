#pragma once
#include <string>


namespace mia{

    int findUseBin(int day);
    std::string generateBankCardNumber(int V, int M, int W);
    std::string generateDate(int minYear, int maxYear, int train_number, int total_time); 
    int generateInt(const int a, const int b);
    std::string generateFullName();
    std::string generatePassportData();
    std::string getRandomLineFromFile(const std::string& filename);
    std::string returnDate(const std::string& dateStr, long daysToAdd, std::string time);
  
}