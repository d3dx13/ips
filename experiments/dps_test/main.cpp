#include "dps/dps.h"
#include <iostream>
#include <unistd.h>
#include <signal.h>

using namespace std;

struct test_msg {
    int a;
    int b;
    int c;
};

class SimpleNode : public dps::Node {
    public:
        SimpleNode() : dps::Node("SimpleNode"){
            // auto pub = this->create_publisher<test_msg>(test_msg, "test");
            // dps::Publisher this->create("test");
        }
};

int main(int argc, char *argv[])
{
    
    dps::Publisher<test_msg> pub(10);

    pub.print();

    pub.msg->a = 12312;
    pub.msg->b = 111;
    pub.msg->c = 44444;
    cout << "size " << sizeof(pub.msg) << "\n";

    pub.print();

    pub.publish();
    pub.print();
    
    int temp;

    SimpleNode node = SimpleNode();

    cout << "pid " << node.get_pid() << "\n";
    
    system("tree -a /dev/shm/");

    cin >> temp;

    // raise(SIGSEGV);
    
    return 0;
}