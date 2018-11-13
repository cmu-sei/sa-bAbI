void test1() {
    int x;
    float y;
    char z;
    x = 0;
    y = 0;
    z = 0;
}

void test2() {
    int x;
    float y;
    char z;
    x = 0;
    y = 0;
    z = 0;

    {
        int x;
        float y;
        char z;
        x = 0;
        y = 0;
        z = 0;
        
        {
            int x;
            float y;
            char z;
            x = 0;
            y = 0;
            z = 0; 
        }
    }
}
