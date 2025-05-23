#include "doubly_linked_list.hpp"

#include <iostream>

using mia::DoublyLinkedList;

template<typename T>
DoublyLinkedList<T>::~DoublyLinkedList() {
	if (!begin) return;
	Node* lst = begin;
	while (lst)
	{
		Node* nx = lst->next;
		delete lst;
		lst = nx;
	}
	begin = nullptr;
	end = nullptr;	
}

template<typename T>
std::size_t DoublyLinkedList<T>::get_size() const noexcept {
	std::size_t sz = 0;
	Node* lst = begin;
	while (lst)
	{
		sz++;
		lst = lst->next;
	}
	return sz;

}

template<typename T>
bool DoublyLinkedList<T>::has_item(const T& value) const noexcept {
	Node* lst = begin;
	while (lst)
	{
		if (lst->value == value) return true;
		lst = lst->next;
	}
	return false;
}

template<typename T>
void DoublyLinkedList<T>::print() const noexcept {
	Node* lst = begin;
	if (!begin){
		std::cout << "";
		return;
	}
	std::cout << lst->value;
	lst = lst->next;
	while (lst) {
		std::cout << ", " << lst->value;
		lst = lst->next;
	}
	std::cout << std::endl;
}

template<typename T>
void DoublyLinkedList<T>::push_back(const T& value) {
	Node* nw = new Node(value);
	if (!nw) return;
	if (begin == nullptr){
		begin = nw; end = nw;
	}else{
		end->next = nw;
		nw->prev = end;
		end = nw;
	}
}

template<typename T>
bool DoublyLinkedList<T>::remove_first(const T& value) noexcept {
	Node* lst = begin;
	if (!begin) return false;
	while (lst)
	{
		if (lst->value == value){
			if (lst == begin && lst == end) begin = end = nullptr;
			else if (lst == begin) {
				begin = lst->next;
				begin->prev = nullptr;
			} else if (lst == end) {
				end = lst->prev;
				end->next = nullptr;
			} else {
				(lst->prev)->next = lst->next;
				(lst->next)->prev = lst->prev;
			}
			delete lst;
			return true;
			
		}
		lst = lst->next;
	}
	return false;
}
