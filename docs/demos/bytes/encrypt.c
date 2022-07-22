void encrypt(char * in, int length_in, char * out,  char * key,
       int key_length, int key_multiplier) {
  for (int i = 0, j = 0; i < length_in; i++, j = (j + 1) % key_length) {
    out[i] = in[i] + key[j] * key_multiplier;
  }
}
