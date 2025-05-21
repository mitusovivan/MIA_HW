#include "long_number.hpp"

using mia::LongNumber;
		
LongNumber::LongNumber() : length(1), sign(1){
	
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

	//std::cout << "LN2" << std::endl;
	
	numbers = new int[length];
	for (int i = 0; i < length; i++){
		numbers[i] = str[str_length - i -1] - '0';
	} 
	
}

LongNumber::LongNumber(const LongNumber& x) {
	//std::cout << "LN3" << std::endl;
	length = x.length;
	sign = x.sign;
	numbers = new int[length];
	for (int i = 0; i < length; i++){
		numbers[i] = x.numbers[i];
	}
}

LongNumber::LongNumber(LongNumber&& x) {
	//std::cout << "LN4" << std::endl;
	length = x.length;
	sign = x.sign;
	numbers = x.numbers;
	x.numbers = nullptr;
	x.length = 0;
	x.sign = 0;
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
	return (!(*this).operator>(x) && !(*this).operator==(x));
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
		int sum_len = std::max(x.length, length) + 1;
		int* sum = new int[sum_len];

		for (int i = 0; i < sum_len; i++) sum[i] = 0;
		for (int i = 0; i < x.length; i++) {
			sum[i] = x.numbers[i];
		}

		int reg = 0;
		for (int i = 0; i < length; i++){
			int res = reg + sum[i] + numbers[i];
			reg = res / 10;
			sum[i] = res % 10;
		}
		sum[sum_len - 1] = reg;

		int res_len = sum_len;
		for (int i = 0; i < sum_len; i++){
			if (sum[sum_len - 1 - i] != 0) break;
			res_len--;
		}

		int* res = new int[res_len];
		for (int i = 0; i < res_len; i++) res[i] = sum[i]; 

		delete [] sum;
		Sum.sign = sign;
		Sum.length = res_len;
		Sum.numbers = res;
		return Sum;
	}

}

LongNumber LongNumber::operator - (const LongNumber& x) const {
	if (sign != x.sign) {
            LongNumber abs_x_copy = x;
            abs_x_copy.sign = 1;
            if (sign == 1) { 
                return *this + abs_x_copy;
            } else { 
                LongNumber abs_this_copy = *this;
                abs_this_copy.sign = 1;
                LongNumber sum = abs_this_copy + abs_x_copy;
                sum.sign *= -1; 
                return sum;
            }
        } else { 
            bool this_abs_greater = false;
            if (length > x.length) {
                this_abs_greater = true;
            } else if (length < x.length) {
                this_abs_greater = false;
            } else {
                for (int i = length - 1; i >= 0; --i) {
                    if (numbers[i] > x.numbers[i]) {
                        this_abs_greater = true;
                        break;
                    }
                    if (numbers[i] < x.numbers[i]) {
                        this_abs_greater = false;
                        break;
                    }
                }
            }

            const LongNumber* larger_abs = this_abs_greater ? this : &x;
            const LongNumber* smaller_abs = this_abs_greater ? &x : this;

            int result_length = std::max(length, x.length);
            int* result_digits = new int[result_length];
             for(int i = 0; i < result_length; ++i) result_digits[i] = 0;

            int borrow = 0;

            for (int i = 0; i < result_length; ++i) {
                int digit1 = (i < larger_abs->length) ? larger_abs->numbers[i] : 0;
                int digit2 = (i < smaller_abs->length) ? smaller_abs->numbers[i] : 0;
                int diff = digit1 - digit2 - borrow;
                if (diff < 0) {
                    diff += 10;
                    borrow = 1;
                } else {
                    borrow = 0;
                }
                result_digits[i] = diff;
            }

            int actual_length = result_length;
            while (actual_length > 1 && result_digits[actual_length - 1] == 0) {
                actual_length--;
            }

            LongNumber result;
            delete[] result.numbers; 
            result.length = actual_length;
            if (sign == 1) { 
                result.sign = this_abs_greater ? 1 : -1;
            } else {
                result.sign = this_abs_greater ? -1 : 1;
            }

             if (actual_length == 1 && result_digits[0] == 0) {
                result.sign = 1; 
            }

            result.numbers = new int[actual_length];
            for (int i = 0; i < actual_length; ++i) {
                result.numbers[i] = result_digits[i];
            }

            delete[] result_digits; 

            return result;
        }
	/*LongNumber Sum;
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
		
		delete [] sum;

		Sum.sign = s;
		Sum.length = res_len;
		Sum.numbers = res;
		return Sum;
	}*/
}

LongNumber LongNumber::operator * (const LongNumber& x) const {
	LongNumber Prod;
	int prod_sig = sign * x.sign;
	int prod_len = x.length + length + 1;
    int* prod = new int[prod_len];

	for (int i = 0; i < prod_len; i++) {
		prod[i] = 0;
	}
	int reg;
    for (int i = 0; i < length; i++){
		reg = 0;
		for (int j = 0; j < x.length; j++){
			int ind = j + i; 
			int po_pr = (x.numbers[j] * numbers[i]) + reg + prod[ind];
			reg = po_pr / 10;
			prod[ind] = po_pr - (reg * 10);
		}
		int j = 0;
        while (reg != 0){
                prod[i + x.length + j] = reg % 10;
                reg = reg/10;
                j++;
        }

	}



	int prod_res_len = prod_len;
	for (int i = 0; i < prod_len; i++){
		if (prod[prod_len - 1 -i] != 0) break;
		prod_res_len--;
	}

	if (prod_res_len == 0) {
			Prod.sign = 1;
			Prod.length = 1;
			Prod.numbers = prod;
			return Prod;
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
    if (((sign == 1 ? 0 : 1) + (x).operator>(*this)) % 2) {
        LongNumber Prod(0);
        return Prod;
    }
		if (sign == 0) {
        return LongNumber("0");
    }

    
    LongNumber dividend = *this;
    dividend.sign = 1;
    LongNumber divisor = x;
    divisor.sign = 1;
    
    if (dividend < divisor) {
        return LongNumber("0");
    }
    
    LongNumber quotient("0"); 
    LongNumber remainder("0");
    LongNumber ten("10");
    
    for (int i = dividend.length - 1; i >= 0; --i) {
        remainder = remainder * ten;
        
        LongNumber now;
        now.numbers = new int[1]{dividend.numbers[i]};
        now.length = 1;
        now.sign = 1;
        
        remainder = remainder + now;
        
        int digit = 0;
        while (remainder > divisor or remainder == divisor) {
            remainder = remainder - divisor;
            digit++;
        }
        
        quotient = quotient * ten;
        
        LongNumber digitNum;
        digitNum.numbers = new int[1]{digit};
        digitNum.length = 1;
        digitNum.sign = 1;
        
        quotient = quotient + digitNum;
    }


    while (quotient.length > 1 and quotient.numbers[quotient.length - 1] == 0) {
        quotient.length--;
    }

	LongNumber PseX, PseY;
	PseX = *this;
	PseY = x;
	PseX.sign = 1;
	PseY.sign = 1;
	if (!((quotient * PseY) == PseX) && (sign == -1)) quotient = quotient + "1";//кастыль

    quotient.sign = sign * x.sign;
    
    return quotient;

        /*LongNumber Prod, A;
		int* div_a = new int[length];
		int* div_b = new int[length];

		for (int i = 0; i < length; i++){
			div_a[i] = 0;
			div_b[i] = numbers[i];
		}
		int* div_m = new int[length];
		std::cout << "ST1" << std::endl;
		while (delt(div_a, div_b, length)){

			// std::cout << std::endl << "A: ";
			// for (int i =0; i < length; i++) std::cout << div_a[i];
			// std::cout << std::endl << "B: ";
			// for (int i =0; i < length; i++) std::cout << div_b[i];

			for (int i = 0; i < length; i++) div_m[i] = (div_a[i] + div_b[i]) / 2;

			// std::cout << std::endl << "M: ";
			// for (int i =0; i < length; i++) std::cout << div_m[i] << " ";

			// int hren;
			// std::cin >> hren;

			int dl = length;
			for (int i = 0; i < length; i++){
				if (div_m[dl - 1 - i] != 0) break;
				dl--;
			}
			int* dml = new int[dl];
			for (int i = 0; i < dl; i++) dml[i] = div_m[i];

			std::cout << std::endl << "A: ";
			for (int i =0; i < length; i++) std::cout << div_a[i];
			std::cout << std::endl << "B: ";
			for (int i =0; i < length; i++) std::cout << div_b[i];
			std::cout << std::endl << "M: ";
			for (int i =0; i < length; i++) std::cout << div_m[i] << " ";

			int hren;
			std::cin >> hren;


			int prod_len = x.length + dl + 1;
			int* prod = new int[prod_len];

			for (int i = 0; i < prod_len; i++) {
				prod[i] = 0;
			}
			int reg;
			for (int i = 0; i < dl; i++){
				reg = 0;
				for (int j = 0; j < x.length; j++){
					int ind = j + i; 
					int po_pr = (x.numbers[j] * dml[i]) + reg + prod[ind];
					reg = po_pr / 10;
					prod[ind] = po_pr - (reg * 10);
				}
				int j = 0;
				while (reg != 0){
						prod[i + x.length + j] = reg % 10;
						reg = reg/10;
						j++;
				}

			}



			int C_len = prod_len;
			for (int i = 0; i < prod_len; i++){
				if (prod[prod_len - 1 -i] != 0) break;
				C_len--;
			}

			if (C_len == 0) {
				C_len = 1;	
			}

			int* C_res = new int[C_len];
			for (int i = 0; i < C_len; i++) C_res[i] = prod[i]; 



			for (int i = 0; i < C_len; i++) std::cout << C_res[i];

			if (C_len > length){
				for (int i = 0; i < length; i++) div_b[i] = div_m[i];
			}else if (C_len < length){
				for (int i = 0; i < length; i++) div_a[i] = div_m[i];
			}else{
				bool flag = true;
				for (int i = 0; i < length; i++){
					if (numbers[length - i - 1] < C_res[length - i - 1]){
						flag = false;
						for (int i = 0; i < length; i++) div_b[i] = div_m[i];
						break;
					}
				}
				if (flag) for (int i = 0; i < length; i++) div_a[i] = div_m[i];
			}

			delete [] dml;
		}



		std::cout << "ST4" << std::endl;
		
		int prod_len = x.length + length + 1;
		int* prod = new int[prod_len];

		for (int i = 0; i < prod_len; i++) {
			prod[i] = 0;
		}
		int reg;
		for (int i = 0; i < length; i++){
			reg = 0;
			for (int j = 0; j < x.length; j++){
				int ind = j + i; 
				int po_pr = (x.numbers[j] * div_b[i]) + reg + prod[ind];
				reg = po_pr / 10;
				prod[ind] = po_pr - (reg * 10);
			}
			int j = 0;
			while (reg != 0){
					prod[i + x.length + j] = reg % 10;
					reg = reg/10;
					j++;
			}

		}



		int C_len = prod_len;
		for (int i = 0; i < prod_len; i++){
			if (prod[prod_len - 1 -i] != 0) break;
			C_len--;
		}

		if (C_len == 0) {
			C_len = 1;	
		}

		int* C_res = new int[C_len];
		for (int i = 0; i < C_len; i++) C_res[i] = prod[i]; 



		for (int i = 0; i < C_len; i++) std::cout << C_res[i];

		
		int* pre_res = new int[length];
		std::cout << "ST5" << std::endl;
		if (C_len > length){
			for (int i = 0; i < length; i++) pre_res[i] = div_a[i];
		}else if (C_len < length){
			for (int i = 0; i < length; i++) pre_res[i] = div_b[i];
		}else{
			bool flag = true;
			for (int i = 0; i < length; i++){
				if (numbers[length - i - 1] < C_res[length - i - 1]){
					flag = false;
					for (int i = 0; i < length; i++) pre_res[i] = div_a[i];
					break;
				}
			}
			if (flag) for (int i = 0; i < length; i++) pre_res[i] = div_b[i];
		}

		int res_len = length;
		for (int i = 0; i < length; i++){
			if (pre_res[length - 1 -i] != 0) break;
			res_len--;
		}
		int* res = new int[res_len];
		for (int i = 0; i < res_len; i++) res[i] = pre_res[i]; 
		std::cout << "ST6" << std::endl;
		delete [] div_a, div_b, div_m, pre_res;
		Prod.sign = div_sig;
		Prod.length = res_len;
		Prod.numbers = res;
        return Prod;
    */
}

LongNumber LongNumber::operator % (const LongNumber& x) const {
	LongNumber res = x.operator*((*this).operator/(x));
	return (*this).operator-(res);
}

int LongNumber::get_digits_number() const noexcept {
	return length;	
}

int LongNumber::get_rank_number(int rank) const {
	return (rank < 1) ? -1 : numbers[length - rank];
}

bool LongNumber::is_negative() const noexcept {
	return sign == -1;
}

bool LongNumber::delt(int* a, int* b, int len) const{ 
	for (int i = 1; i < len; i++){
		if (abs(b[i] - a[i]) > 0) return true;
	}
	return (abs(b[0] - a[0]) > 1) ? true : false;
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
