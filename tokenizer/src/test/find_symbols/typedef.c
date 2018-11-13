typedef int number;

typedef struct {
    number x;
    number y;
} point2;

typedef struct point3  {
    number x;
    number y;
    number z;
} point3;

void test() {
    point2 p;
    number x = 1;
    number y = 2;
    p.x = x;
    p.y = y;

    struct point3 q;
    q.x = 1;
    q.y = 2;
    q.z = 3;
}
