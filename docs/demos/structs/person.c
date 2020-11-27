#include <stddef.h>

typedef struct Person {
    wchar_t * name;
} Person;

Person make_person(wchar_t * name) {
    Person person;
    person.name = name;
    return person;
}
