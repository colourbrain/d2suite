# d2lib
`d2lib` is a C++ library of discrete distribution (d2) based 
large-scale data processing framework. It also contains a collection of
computing tools supporting the analysis of d2 data.

*[under construction]*

Dependencies
 - BLAS
 - [rabit](https://github.com/dmlc/rabit): the use of generic parallel infrastructure
 - [mosek](https://www.mosek.com): fast LP/QP solvers

Make sure you have those pre-compiled libraries installed and
configured in the [d2lib/Makefile](d2lib/Makefile).
```bash
cd d2lib && make && make test
```

## Introduction
### Data Format Specifications
 - discrete distribution over Euclidean space
 - discrete distribution with finite possible supports in Euclidean space (e.g., bag-of-word-vectors and sparsified histograms)
 - n-gram data with cross-term distance
 - dense histogram

### Basic Functions
 - distributed/serial IO 
 - compute distance between a pair of D2: Wasserstain distance (or EMD), Sinkhorn Distances (entropic regulared optimal transport).


### Learnings
 - nearest neighbors [TBA]
 - D2-clustering [TBA]
 - Dirichlet process [TBA]

## Other Tools
 - document analysis: from bag-of-words to .d2s format [TBA]

