#include "vector.hpp"

#include <iostream>

using mia::Vector;

template<typename T>
const std::size_t Vector<T>::START_CAPACITY = 10;

template<typename T>
Vector<T>::Vector() {
	arr = new T[capacity];
}

template<typename T>
Vector<T>::~Vector() {
	delete [] arr;
}

template<typename T>
std::size_t Vector<T>::get_size() const noexcept {
	return size;
}

template<typename T>
bool Vector<T>::has_item(const T& value) const noexcept {
	for (std::size_t i = 0; i < size; i++){
		if (arr[i] == value) return true;
	}
	return false;
}

template<typename T>
bool Vector<T>::insert(const std::size_t position, const T& value) {
	if ((position < 0) || (position > size)) return false;
	if (size == capacity){
		capacity = capacity * 2;
		T* arr2 = new T[capacity];
		std::copy(arr, arr + position, arr2);
		arr2[position] = value;
		std::copy(arr + position, arr + size, arr2 + position + 1);
		delete [] arr;
		arr = arr2;
	}else{
		for (std::size_t i = size; i > position; --i) arr[i] = arr[i - 1];
		arr[position] = value;
	}

	size++;
	return true;
}

template<typename T>
void Vector<T>::print() const noexcept {
	if (size == 0){
		std::cout << "";
		return;
	}
	for (std::size_t i = 0; i < size - 1; ++i) {
        std::cout << arr[i] << ", " ;
    }
    std::cout << arr[size - 1] << std::endl;
}

template<typename T>
void Vector<T>::push_back(const T& value) {
	if (size == capacity){
		capacity *= 2;
		T* arr2 = new T[capacity];
        std::copy(arr, arr + size, arr2);
        delete[] arr;
        arr = arr2;
	}
	arr[size] = value;
	size++;
}

template<typename T>
bool Vector<T>::remove_first(const T& value) {
	for (std::size_t i = 0; i < size; ++i) {
        if (arr[i] == value) {
            for (std::size_t j = i; j < size - 1; ++j) arr[j] = arr[j + 1];
            size--;
            return true;
        }
    }
    return false;
}
