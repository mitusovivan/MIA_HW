#include <iostream>
#include <vector>
#include <random>
#include <algorithm>
#include <cmath>
#include <chrono>

using namespace std;

int main(){
    int n, k;
    cin >> n >> k;
    vector<int> arr(n, 0);
    for (int i = 0; i<n; i++) cin >> arr[i];
    int ma = -1;
    for (int i = 0; i<n; i++) ma = max(ma, arr[i]);
    vector<int> e(ma + 1, 0);
    vector<int> pref(ma + 1, 0);
    for (int i = 0; i < n; i++) e[arr[i]]++;
    pref[0] = e[0];

    for (int i = 1; i < ma + 1; i++) pref[i] = pref[i - 1] + e[i];

    //for (int i = 0; i < pref.size(); i++) cout << pref[i] << ' '; cout << '\n';
    for (int i = 0; i < k; i++){
        int l, r;
        cin >> l >> r;
        if (r > ma) r = ma;

        if (l > 0) cout << pref[r] - pref[l - 1]<<'\n';   
        else cout <<  pref[r] << '\n';
    }
}