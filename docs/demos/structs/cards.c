#include <stdint.h> // Needed for unit8_t.

typedef struct Card {
  uint8_t face;
  uint8_t suit;
} Card;


/* --- Python to C --- */

uint8_t get_card_face(Card card) {
  return card.face;
}

uint8_t get_card_ptr_face(Card * card) {
  return card -> face;
}

/* --- C to Python --- */

Card make_card(uint8_t face, uint8_t suit) {
  Card card;
  card.face = face;
  card.suit = suit;
  return card;
}

/* --- C to Python by ptr - Bad! Dangling pointer! --- */

Card * make_card_ptr(uint8_t face, uint8_t suit) {
  Card card;
  card.face = face;
  card.suit = suit;
  return &card;
}

/* --- C to Python by ptr - Good, but remember to call free() --- */

#include <stdlib.h> // Needed for malloc() and free().

Card * make_card_ptr_safer(uint8_t face, uint8_t suit) {
  Card * card =  malloc(sizeof(Card));
  if (!card) return NULL; // Return None if no memory available.
  card -> face = face;
  card -> suit = suit;
  return card;
}

void delete_card(Card * card) {
  free(card);
}
