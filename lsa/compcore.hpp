#include <vector>
#include <iostream>
#include <cstdlib>
#include <cmath>
#include <algorithm>
#include <limits>
//#include <numeric>

using namespace std;

//Customized types
typedef vector<double> VectorDouble;
typedef vector<VectorDouble> MatrixDouble;
typedef vector<int> VectorInt;
typedef vector<VectorInt> MatrixInt;
//typedef vector<double> VectorDouble;
//typedef vector<VectorDouble> MatrixDouble;

//easy functions
int test();
//double calc_LA(VectorDouble, VectorDouble, VectorDouble);

//// LSA section

class LSA_Data {
public:
  int max_shift;
  VectorDouble X;
  VectorDouble Y;
  LSA_Data(){ VectorDouble X; VectorDouble Y; max_shift=std::numeric_limits<int>::max(); };
  LSA_Data(int shift, VectorDouble x, VectorDouble y): max_shift(shift),X(x),Y(y){ };
  void assign(int, VectorDouble, VectorDouble);
};

class LSA_Result {
public:
  double score;
  MatrixInt trace;
  //LSA_Result();
  //~LSA_Result();
};

LSA_Result DP_lsa( const LSA_Data&, bool ); 


//// LLA section
class LLA_Data {
public:
  // Member variables
  int max_shift;
  VectorDouble X;
  VectorDouble Y;
  VectorDouble Z;
  // Default Constructor. Initialize with default values
  LLA_Data(){max_shift = std::numeric_limits<int>::max(); VectorDouble X; VectorDouble Y; VectorDouble Z; };
  // Construct with parameters
  LLA_Data(int shift, VectorDouble x, VectorDouble y, VectorDouble z): max_shift(shift),X(x),Y(y),Z(z){ };
};


class LLA_Result {
public:
    double score;
    MatrixInt trace;
    
    // Add constructor
    LLA_Result() : score(0.0) {}
};

// Add documentation
/**
 * Performs dynamic programming for Liquid Local Association analysis
 * @param data Input data containing X, Y, Z sequences and max_shift
 * @param keep_trace Whether to keep alignment trace
 * @return LLA_Result containing score and optional trace
 * @throws std::invalid_argument if input data is invalid
 */

// Update function declaration to match new implementation
LLA_Result DP_lla(const LLA_Data& data, bool keep_trace = true); 


/// Potential improvements? encapsulation
/*
class LLA_Data {
public:
    // Constructor
    LLA_Data(int shift, VectorDouble x, VectorDouble y, VectorDouble z)
        : max_shift(shift), X(std::move(x)), Y(std::move(y)), Z(std::move(z)) 
    { }

    // Add getters for encapsulation
    int getMaxShift() const { return max_shift; }
    const VectorDouble& getX() const { return X; }
    const VectorDouble& getY() const { return Y; }
    const VectorDouble& getZ() const { return Z; }

private:  // Make members private for better encapsulation
    int max_shift;
    VectorDouble X;
    VectorDouble Y;
    VectorDouble Z;
};
*/

/// using examples
/*
// Creating vectors
VectorDouble x = {1.0, 2.0, 3.0};
VectorDouble y = {4.0, 5.0, 6.0};
VectorDouble z = {7.0, 8.0, 9.0};

// Creating LLA_Data object
LLA_Data data(5, x, y, z);

// Using the data
// Current way (with public members):
double first_x = data.X[0];

// Better way (with suggested improvements):
double first_x = data.getX()[0];
*/



/*
class LA_Result {
public:
  double score;
};

int LLA_Data::random_shuffle(){
  std::random_shuffle(X.begin(),X.end());
  //cout<<"X="<<X[0]<<","<<X[1]<<","<<X[2]<<","<<X[3]<<endl;
  std::random_shuffle(Y.begin(),Y.end());
  //cout<<"Y="<<Y[0]<<","<<Y[1]<<","<<Y[2]<<","<<Y[3]<<endl;
  std::random_shuffle(Z.begin(),Z.end());
  //cout<<"Z="<<Z[0]<<","<<Z[1]<<","<<Z[2]<<","<<Z[3]<<endl;
  return 0;
};
*/

//// Permutation test template
/*
class PT_Return {
public:
  VectorDouble scores;
  double pvalue;
};
*/

//Declaration of functions
//LLA_Result DP_lla( const LLA_Data& ); //const: passing the reference not for modifying
//LA_Result ST_la( const LLA_Data& );


/*
template <class DataType, class ResultType>
    PT_Return PT( DataType data, const ResultType& result, int pn, ResultType (*test_func)( const DataType& ) )
{
  PT_Return pt_return;
  double score;
  int count=0;
  for( int i=0; i<pn; i++ ){
    data.random_shuffle_x();
    score = (test_func(data)).score;
    //cout << i << "-th: " << score << endl;
    pt_return.scores.push_back(score);
    if ( abs(score) > abs(result.score) ) count++; // for two tailed p-value
  }
  //cout << count <<endl;
  pt_return.pvalue = (double)count/(double)pn;
  return pt_return;
};
*/

//// LSA with replicates data types
/* currently not used
class LSA_Rep_Data{
public:
  int max_shift;
  MatrixDouble X;
  MatrixDouble Y;
  LSA_Rep_Data(){ MatrixDouble X; MatrixDouble Y; max_shift=std::numeric_limits<int>::infinity(); };
  LSA_Rep_Data(int shift, MatrixDouble x, MatrixDouble y): max_shift(shift), X(x), Y(y){ };
  inline int random_shuffle();
};

int LSA_Rep_Data::random_shuffle(){  //shuffle rows, we want each column is a time sequence, do proper transformation at input
  std::random_shuffle(X.begin(),X.end());
  std::random_shuffle(Y.begin(),Y.end());
  return 0;
};
*/
