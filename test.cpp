#include <graphviz/gvc.h>
#include <graphviz/cgraph.h>
#include <iostream>
using namespace std;

int main() {
    {
        auto c = gvContext();
        auto g = agopen("G", Agdirected, nullptr);
        auto n = agnode(g, "n", 1);
        auto m = agnode(g, "m", 1);
        auto e = agedge(g, n, m, "Ling", 1);
        auto r = gvLayout(c, g, "dot");
        cout << r << endl;
        r = gvRenderFilename(c, g, "svg", "gvRenderFilename.svg");
        cout << r << endl;
        gvFreeLayout(c, g);
        agclose(g);
    }

    return 0;
}