#include <string>

class House {

};

namespace Vehicle {

    namespace Carburant {
        class Electric {
            class Pipe {};
        };
    }

    struct Engine {
        int HP;
    };

    class Vehicle {
    public:
        std::string brand;
        std::string model;
        int year;
        int kilometer;
        Engine engine;

        void start() {
            kilometer++;
        }
    };

    class Car : public Vehicle {
    };

    class Motorcycle : public Vehicle {
    };

    class Bicycle : public Vehicle {
    };
}

int main() {
    return 0;
}
