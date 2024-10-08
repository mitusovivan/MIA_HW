#include <iostream>
#include <vector>
#include <random>
#include <algorithm>
#include <cmath>
#include <chrono>
#include <set>


using namespace std;
using namespace chrono;
mt19937 mt(time(nullptr));

void shell_sort ( vector <int >& a, set<int>& e) {
    int n = a.size () ;
    /*while (3 * h + 1 <= (n + 2) / 3)
        h = 3 * h + 1;
    cout << "Ok" << " ";*/
    vector<int> t;
    for (int i : e) t.push_back(i); 
    for (int i = t.size(); i > 0; i--) {
            int h = t[i - 1];
            //cout << "Ok" << " ";
            for( int i = h ; i < n ; ++ i ) {
                int temp = a [ i ];
                int j = i ;
                for (; j >= h && a [ j - h ] > temp ; j -= h )
                    a [ j ] = a[ j - h ];
                a [ j ] = temp ;
        }
    }
}

set<int> gen(int n){
    set<int> a;
    for (int i = 0; i < n; i++){
            for (int j = 0; j < n; j++){
                a.insert(pow(2, i) * pow(3, j));
            }
    }
    //sort(a.begin(), a.end());
    return a;
}

int main(){
    for (int j = 3; j < 7; j++){
    //int n = (mt() % 100);
    int n = pow(10, j);
    cout << "For n = " << n << '\n';
    set<int> e;
    vector<int> a(n);
    vector<int> a1(n);
    e = gen(11);
    //for (int i : e) cout << i << ' ';
    for (int i = 0; i < n; i++){int s = mt() % 100; a[i] = s; a1[i] = s;}

    //using namespace chrono;
    auto start = steady_clock :: now () ;
    sort(a1.begin(), a1.end());
    auto end = steady_clock :: now () ;
    duration < double > elapsed_seconds = end - start ;
    cout << " Standart time : " << elapsed_seconds . count () << "s\n";

    start = steady_clock :: now () ;
    shell_sort(a, e);
    end = steady_clock :: now () ;
    elapsed_seconds = end - start ;
    cout << " Shell time : " << elapsed_seconds . count () << "s\n";
    
    //using namespace std;
    //for (int i = 0; i < a.size(); i++) cout << a[i] << ' '; 
    }
    return 0;
}