 %{
 #define SWIG_FILE_WITH_INIT
 /* Includes the header in the wrapper code */
 #include "./epanet/epanet2.h"
 extern char TmpDir[200]; /* this makes it possible to overrride the TmpDir */
 %}


/* modify epanet2.h file as: 
1. Undefine __win32__ and WINDOWS 
2. for all output parameters, give the name value */
%module epanet2
 %include "typemaps.i"
 %include "cstring.i"
 %include "numpy.i"
 
 %init %{
 import_array();
 %} 
 
 %apply (float* IN_ARRAY1, int DIM1) {(float* floatarray, int nfloats)};
 
 /* read http://www.swig.org/Doc1.3/Arguments.html */
 
 %apply int *OUTPUT { int *result };
 %apply int *OUTPUT { int *result1 };
 %apply int *OUTPUT { int *result2 };
 %apply long *OUTPUT { long *result };
 %apply float *OUTPUT { float *result };
 %apply float *OUTPUT {float *c1}
 %apply float *OUTPUT {float *c2}
 %apply int *OUTPUT {int *ci1}
 %apply int *OUTPUT {int *ci2}
 %apply int *OUTPUT {int *ci3}
 %apply double *OUTPUT { double *result };
 %cstring_bounded_output(char *result,   1024);


 
 /* Parse the header file to generate wrappers */
 %include "./epanet/epanet2.h"
 
 extern char TmpDir[200]; /* this makes it possible to overrride the TmpDir */
;