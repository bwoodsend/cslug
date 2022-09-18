#import <CoreGraphics/CGColorConversionInfo.h>

void foo() {
  CGColorConversionInfoCreate(NULL, NULL);  // Requires macOS >= 10.12
}
