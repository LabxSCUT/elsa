%module test
%{
#include <vector>
%}
%include <std_vector.i>
%template(VectorDouble) std::vector<double>;
