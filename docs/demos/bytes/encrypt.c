
void encrypt(char * in, int length_in, char * out,  char * key,
       int key_length, int key_multiplier) {
  /* Encrypt `in` into `out` with encryption key `key`.
    Set `key_multiplier` to 1 to encrypt or -1 to decrypt. */

  for (int i = 0; i < length_in; i++)
    out[i] = in[i] + key[i % key_length] * key_multiplier;
}
