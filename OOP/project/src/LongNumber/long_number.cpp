#include "long_number.hpp"

using mia::LongNumber;
		
LongNumber::LongNumber() {
	numbers = new int[length];
	numbers[0] = 0;
}

LongNumber::LongNumber(const char* const str) {
	int str_length = std::strlen(str);
	if (str[0] == '-'){
		sign = -1;
		length = str_length - 1;
	} 
	else{
		sign = 1;
		length = str_length;
	}

	std::cout << "LN2" << std::endl;
	
	numbers = new int[length];
	for (int i = 0; i < length; i++){
		numbers[i] = str[str_length - i -1] - '0';
	} 
	
}

LongNumber::LongNumber(const LongNumber& x) {
	length = x.length;
	sign = x.sign;
	numbers = new int[length];
	for (int i = 0; i < length; i++){
		numbers[i] = x.numbers[i];
	}
}

LongNumber::LongNumber(LongNumber&& x) {
	length = x.length;
	sign = x.sign;
	numbers = x.numbers;
	x.numbers = nullptr;
}

LongNumber::~LongNumber() {
	length = 0;
	delete [] numbers;
	numbers = nullptr;
}

LongNumber& LongNumber::operator = (const char* const str) {
	int str_length = std::strlen(str);
	if (str[0] == '-'){
		sign = -1;
		length = str_length - 1;
	} else{
		sign = 1;
		length = str_length;
	}

	delete [] numbers;
	numbers = new int[length];
	for (int i = 0; i < length; i++){
		numbers[i] = str[str_length - i - 1] - '0';
	}

	return *this;
}

LongNumber& LongNumber::operator = (const LongNumber& x) {
	if (this == &x) return *this;

	length = x.length;
	sign = x.sign;
	
	delete [] numbers;
	numbers = new int[length];
	for (int i = 0; i < length; i++){
		numbers[i] = x.numbers[i];
	}

	return *this;
}

LongNumber& LongNumber::operator = (LongNumber&& x) {
	length = x.length;
	sign = x.sign;
	
	delete [] numbers;
	numbers = x.numbers;
	x.numbers = nullptr;
	
	return *this;
}

bool LongNumber::operator == (const LongNumber& x) const {
	if ((length == x.length) && (sign == x.sign)){
		for (int i = 0; i < length; i++){
			if (numbers[i] != x.numbers[i]){
				return false;
			}
		}
		return true;
	}
	else{
		return false;
	}
}

bool LongNumber::operator != (const LongNumber& x) const {
	return !operator== (x);
}

bool LongNumber::operator > (const LongNumber& x) const {
	bool s = sign > 0 ? 0 : 1;
	if (sign == x.sign){
		if (length == x.length){
			for (int i = 0; i < length; i++){
				if (numbers[length - 1 - i] > x.numbers[length - 1 - i]){
					return (1 + s) % 2;
				}
			}
			return (s) % 2;
		}else{
			return ((length > x.length) + s) % 2;
		}
	}else{
		return (sign > x.sign);
	}
}

bool LongNumber::operator < (const LongNumber& x) const {
	bool s = sign > 0 ? 0 : 1;
	if (sign == x.sign){
		if (length == x.length){			
			for (int i = 0; i < x.length; i++){
				if (numbers[length - 1 - i] < x.numbers[length - 1 - i]){
					return (1 + s) % 2;
				}
			}
			return (s) % 2;
		}else{
			return ((length < x.length) + s) % 2;
		}
	}else{
		return (sign < x.sign);
	}
}

LongNumber LongNumber::operator + (const LongNumber& x) const {
	LongNumber Sum;

	if (sign != x.sign){
		Sum.length = x.length;
		int* sum = new int[x.length];
		for (int i = 0; i < x.length; i++) {
			sum[i] = x.numbers[i];
		}
		Sum.sign = x.sign * -1;
		Sum.numbers = sum;
		return (*this).operator-(Sum);

	}else{
		std::cout << "ST1" << std::endl;
		int sum_len = std::max(x.length, length) + 1;
		int* sum = new int[sum_len];

		for (int i = 0; i < sum_len; i++) sum[i] = 0;
		for (int i = 0; i < x.length; i++) {
			sum[i] = x.numbers[i];
		}

		std::cout << "ST2" << std::endl;
		int reg = 0;
		for (int i = 0; i < length; i++){
			int res = reg + sum[i] + numbers[i];
			reg = res / 10;
			sum[i] = res % 10;
		}
		sum[sum_len - 1] = reg;

		int res_len = sum_len;
		std::cout << "ST3" << std::endl;
		for (int i = 0; i < sum_len; i++){
			if (sum[sum_len - 1 - i] != 0) break;
			res_len--;
		}

		int* res = new int[res_len];
		for (int i = 0; i < res_len; i++) res[i] = sum[i]; 

		std::cout << "Sum"<< sign <<": ";
		for (int i=0; i < length; i++) {
			std::cout << numbers[length - i - 1];
		}
		std::cout << " + ";
		for (int i=0; i < x.length; i++) {
			std::cout << x.numbers[x.length - i - 1];
		}
		std::cout << " = ";
		for (int i=0; i < res_len; i++) {
			std::cout << res[res_len - i - 1];
		}
		std::cout <<std::endl << res_len <<std::endl;

		delete [] sum;
		Sum.sign = sign;
		Sum.length = res_len;
		
		
		Sum.numbers = res;
		std::cout << "ST4" << std::endl;
		return Sum;
	}

}

LongNumber LongNumber::operator - (const LongNumber& x) const {
	LongNumber Sum;
	std::cout << "Start -" << std::endl;
	if (sign != x.sign){
		Sum.length = x.length;
		int* sum = new int[x.length];
		for (int i = 0; i < x.length; i++) {
			sum[i] = x.numbers[i];
		}
		Sum.numbers = sum;
		Sum.sign = -1 * x.sign;
		return (*this).operator+(Sum);
	}else{

		int sum_len = std::max(x.length, length);
		int* sum = new int[sum_len];
		int* a;
		int* b;
		int s, a_len, b_len;


		if (((sign == 1 ? 0 : 1) + (x).operator>(*this)) % 2) {
			a = x.numbers;
			a_len = x.length;
			b = numbers;
			b_len = length;
			s = sign * -1;
		}else{
			a = numbers;
			a_len = length;
			b = x.numbers;
			b_len = x.length;
			s = sign;
		}

		for (int i = 0; i < a_len; i++) {
			sum[i] = a[i];
		}

		int reg = 0;
		for (int i = 0; i < b_len; i++){
			int res = sum[i] - b[i] - reg;
			reg = ((res >= 0) ? 0 : 1);
			sum[i] = ((10 * reg) + res);
		}
		

		int res_len = sum_len;
		for (int i = 0; i < sum_len; i++){
			if (sum[sum_len - i - 1] != 0) break;
			res_len--;
		}

		if (res_len == 0) {
			Sum.sign = 1;
			Sum.length = 1;
			Sum.numbers = sum;
			return Sum;
		}
		int* res = new int[res_len];
		for (int i = 0; i < res_len; i++) res[i] = sum[i]; 
		
		
		std::cout << "Subs: ";
		for (int i=0; i < a_len; i++) {
			std::cout << a[a_len - i - 1];
		}
		std::cout << " - ";
		for (int i=0; i < b_len; i++) {
			std::cout << b[b_len - i - 1];
		}
		std::cout << " = ";
		for (int i=0; i < res_len; i++) {
			std::cout << res[res_len - i - 1];
		}

		
		delete [] sum;


		Sum.sign = s;
		Sum.length = res_len;
		Sum.numbers = res;
		return Sum;
	}
}

LongNumber LongNumber::operator * (const LongNumber& x) const {
	LongNumber Prod;
	int prod_sig = sign * x.sign;
	int prod_len = x.length + length + 1;
    int* prod = new int[prod_len];

	for (int i = 0; i < prod_len; i++) {
		prod[i] = 0;
	}

	/*for (int i = 0; i < x.length; i++) {
		prod[prod_len - i - 1] = x.numbers[x.length - 1 - i];
	}*/
	
	
    for (int i = 0; i < length; i++){
		int reg = 0;
		for (int j = 0; j < x.length; j++){
			int ind = j + i; 
			int po_pr = (x.numbers[j] * numbers[i]) + reg + prod[ind];
			reg = po_pr / 10;
			//std::cout << "po_pr = " << po_pr << std::endl;
			prod[ind] = po_pr - (reg * 10);
		}

	}
	std::cout << "prod = ";
			for (int i = 0; i < prod_len; i++) std::cout << prod[prod_len - 1 -i];
			std::cout << std::endl;

	//std::cout << "prod_len = " << prod_len << std::endl;

	int prod_res_len = prod_len;
	for (int i = 0; i < prod_len; i++){
		if (prod[prod_len - 1 -i] != 0) break;
		prod_res_len--;
	}

	//std::cout << "prod_res_len = " << prod_res_len << std::endl;

	int* prod_res = new int[prod_res_len];
	for (int i = 0; i < prod_res_len; i++) prod_res[i] = prod[i]; 
    Prod.sign = prod_sig;
	Prod.length = prod_res_len;
	Prod.numbers = prod_res;
	delete[] prod;
    return Prod;
}

LongNumber LongNumber::operator / (const LongNumber& x) const {
	/*int div_sig = sign * x.sign;

    if (length < x.length) {
        LongNumber Prod(0);
        return Prod;
    }

    else if (numbers == x.numbers) {
        LongNumber Prod;
		Prod.sign = div_sig;
		Prod.length = 1;
		int* res = new int[1] {1};
		Prod.numbers = res;
        return Prod;
    }

    else {
        LongNumber Prod;
		int* div_a = new int[length];
		int* div_b = new int[length];
		int* div_res = new int[length];

		for (int i = 0; i < length; i++){
			div_a[i] = 0;
			div_b[i] = numbers[i];
		}

		while (delt(div_a, div_b, length)){

			int* div_m = new int[length];
			for (int i = 0; i < length; i++) div_m[i] = (div_a[i] + div_b[i]) / 2;

			int dl = length;
			for (int i = 0; i < length; i++){
				if (div_m[i] != 0) break;
				dl--;
			}
			int* dml = new int[dl];
			for (int i = 0; i < dl; i++) dml[dl - i - 1] = div_m[length - i - 1];

			int prod_len = x.length + length + 1;
			int* prod = new int[prod_len];

			for (int i = 0; i < x.length; i++) prod[prod_len - i - 1] = x.numbers[x.length - 1 - i];

			for (int i = 0; i < dl; i++){
				int reg = 0;
				for (int j = 0; j < prod_len; j++){
					int po_pr = prod[prod_len - j - 1] * dml[dl - 1 - i] + reg;
					reg = po_pr % 10;
					prod[prod_len - j - 1] = po_pr - reg;
				}
			}

			int prod_res_len = prod_len;
			for (int i = 0; i < prod_len; i++){
				if (prod[i] != 0) break;
				prod_res_len--;
			}
			int* prod_res = new int[prod_res_len];
			for (int i = 0; i < prod_res_len; i++) prod_res[prod_res_len - i - 1] = prod[prod_len - i - 1];

			delete [] prod, dml;

			if (prod_res_len > length){
				for (int i = 0; i < length; i++) div_b[i] = div_m[i];
			}else if (prod_res_len < length){
				for (int i = 0; i < length; i++) div_a[i] = div_m[i];
			}else{
				bool flag = true;
				for (int i = 0; i < length; i++){
					if (numbers[i] < prod_res[i]){
						flag = false;
						for (int i = 0; i < length; i++) div_b[i] = div_m[i];
						break;
					}
				}
				if (flag) for (int i = 0; i < length; i++) div_a[i] = div_m[i];
			}
			delete [] prod_res, div_m;
		}


			int prod_len = x.length + length + 1;
			int* prod = new int[prod_len];

			for (int i = 0; i < x.length; i++) prod[prod_len - i - 1] = x.numbers[x.length - 1 - i];

			for (int i = 0; i < length; i++){
				int reg = 0;
				for (int j = 0; j < prod_len; j++){
					int po_pr = prod[prod_len - j - 1] * div_b[length - 1 - i] + reg;
					reg = po_pr % 10;
					prod[prod_len - j - 1] = po_pr - reg;
				}
			}

			int prod_res_len = prod_len;
			for (int i = 0; i < prod_len; i++){
				if (prod[i] != 0) break;
				prod_res_len--;
			}
			int* prod_res = new int[prod_res_len];
			for (int i = 0; i < prod_res_len; i++) prod_res[prod_res_len - i - 1] = prod[prod_len - i - 1];

			delete [] prod;

			if (prod_res_len > length){
				for (int i = 0; i < length; i++) div_res[i] = div_a[i];
			}else if (prod_res_len < length){
				for (int i = 0; i < length; i++) div_res[i] = div_b[i];
			}else{
				bool flag = true;
				for (int i = 0; i < length; i++){
					if (numbers[i] < prod_res[i]){
						flag = false;
						for (int i = 0; i < length; i++) div_res[i] = div_a[i];
						break;
					}
				}
				if (flag) for (int i = 0; i < length; i++) div_res[i] = div_b[i];
			}
		delete [] prod_res, div_a, div_b;

		int div_Res_len = length;
		for (int i = 0; i < length; i++){
			if (div_res[i] != 0) break;
			div_Res_len--;
		}

		int* div_Res = new int[div_Res_len];
		for (int i = 0; i < div_Res_len; i++) div_Res[div_Res_len - i - 1] = div_res[length - i - 1];

		delete [] div_res;
		Prod.sign = div_sig;
		Prod.length = div_Res_len;
		Prod.numbers = div_Res;
        return Prod;
    }*/
   return x;
}

LongNumber LongNumber::operator % (const LongNumber& x) const {
	//LongNumber res = (*this).operator/(x);
	//return (*this).operator-(res);
	return x;
}

int LongNumber::get_digits_number() const noexcept {
	return 1;	
}

int LongNumber::get_rank_number(int rank) const {
	return rank;
}

bool LongNumber::is_negative() const noexcept {
	return sign == -1;
}

bool LongNumber::delt(int* a, int* b, int len) const{
	if (abs(b[len] - a[len]) > 1) return true; 
	for (int i = 0; i < len - 1; i++){
		if (abs(b[i] - a[i]) > 0) return true;
	}
	return false;
}
// ----------------------------------------------------------
// PRIVATE
// ----------------------------------------------------------
int LongNumber::get_length(const char* const str) const noexcept {
	if (!str) return 0;

    int length = 0;
    while (str[length] != '\0') {
        length++;
    }

    return length;
}

// ----------------------------------------------------------
// FRIENDLY
// ----------------------------------------------------------
namespace mia {
	std::ostream& operator << (std::ostream &os, const LongNumber& x) {
		if (x.sign == -1) {
			os << '-';
		}
		for (int i = 0; i < x.length; i++) {
			os << x.numbers[x.length - i - 1];
		}
		return os;
	}

}
