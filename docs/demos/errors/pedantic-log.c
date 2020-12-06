#include <math.h>
#include "status-codes.h"

int pedantic_log(double in, double * out) {
  if (in == 0) return LOG_OF_0_ERROR;
  if (in < 0) return LOG_OF_NEGATIVE_VALUE_ERROR;
  *out = log(in);
  return OK;
}
