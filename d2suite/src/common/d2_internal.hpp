#ifndef _D2_INTERNAL_H_
#define _D2_INTERNAL_H_


#include "d2.hpp"

namespace d2 {
  namespace internal {

    template <typename D2Type, size_t D>
    class _Meta {};

    template <size_t D>
    class _Meta<def::WordVec, D> : public _Meta<def::Euclidean, D> {
    public:
      _Meta(): size(0), embedding(NULL), _is_allocated(false) {};
      size_t size;
      real_t *embedding;
      void allocate() {
	embedding = new real_t [size*D];
	_is_allocated = true;
      }
      ~_Meta() {
	if (embedding!=NULL && _is_allocated) delete [] embedding;
      }
    private:
      bool _is_allocated;
    };

    template <size_t D>
    class _Meta<def::Histogram, D> {
    public:
      _Meta(): size(0), dist_mat(NULL), _is_allocated(false) {};
      size_t size;
      real_t *dist_mat;
      void allocate() {
	dist_mat = new real_t [size*size];
	_is_allocated = true;
      }
      ~_Meta() {
	if (dist_mat!=NULL && _is_allocated) delete [] dist_mat;
      }
    private:
      bool _is_allocated;
    };

    template <size_t D>
    class _Meta<def::NGram, D>: public _Meta<def::Histogram, D> {
    public:
      using _Meta<def::Histogram, D>::_Meta;
      index_t vocab[255]; // map from char to index
    };

    template <size_t D>
    class _Meta<def::SparseHistogram, D> : public _Meta<def::Histogram, D> {
    public:
      using _Meta<def::Histogram, D>::_Meta;
    };


    template <typename T1=Elem<def::Euclidean, 0>, typename... Ts>
    struct _ElemMultiPhaseConstructor: public _ElemMultiPhaseConstructor<Ts...> {
      _ElemMultiPhaseConstructor (const index_t i=0): 
	ind(i), _ElemMultiPhaseConstructor<Ts...>(i + 1) {}
      index_t ind;
      T1 head;
    };
    template <>
    struct _ElemMultiPhaseConstructor<> {
      _ElemMultiPhaseConstructor (const index_t i) {}
    };

    template <typename T1=Elem<def::Euclidean, 0>, typename... Ts>
    class _BlockMultiPhaseConstructor: public _BlockMultiPhaseConstructor<Ts...> {
    public:
      _BlockMultiPhaseConstructor (const size_t thesize, 
				   const size_t* thelen,
				   const index_t i = 0) : 
	head(thesize, *thelen), ind(i),
	_BlockMultiPhaseConstructor<Ts...>(thesize, thelen+1, i+1) {}
      index_t ind;
      Block<T1> head;
    };

    template <>
    class _BlockMultiPhaseConstructor<> {
    public:
      _BlockMultiPhaseConstructor (const size_t thesize, 
				   const size_t* thelen,
				   const index_t i) {}    
    };

    

    template <typename T=Elem<def::Euclidean, 0>, typename... Ts>
    struct tuple_size {
      static const size_t value = tuple_size<Ts...>::value + 1;
    };

    template <>
    struct tuple_size<> {
      static const size_t value = 0;
    };

    template <size_t k, typename T, typename... Ts>
    struct _elem_type_holder {
      typedef typename _elem_type_holder<k - 1, Ts...>::type type;
    };
    
    template <typename T, typename... Ts>
    struct _elem_type_holder<0, T, Ts...> {
      typedef T type;
    };

    template <size_t k, typename T, typename... Ts>
    typename std::enable_if<
      k == 0, typename _elem_type_holder<0, T, Ts... >::type & >::type
    _get_phase(_ElemMultiPhaseConstructor<T, Ts...>& t) {
      return t.head;
    }

    template <size_t k, typename T, typename... Ts>
    typename std::enable_if<
      k != 0, typename _elem_type_holder<k, T, Ts...>::type & >::type
    _get_phase(_ElemMultiPhaseConstructor<T, Ts...>& t) {
      _ElemMultiPhaseConstructor<Ts...>& base = t;
      return _get_phase<k - 1>(base);
    }

  
    template <size_t k, typename T, typename... Ts>
    typename std::enable_if<
      k == 0, Block<typename _elem_type_holder<0, T, Ts... >::type> & >::type
    _get_block(_BlockMultiPhaseConstructor<T, Ts...>& t) {
      return t.head;
    }

    template <size_t k, typename T, typename... Ts>
    typename std::enable_if<
      k != 0, Block<typename _elem_type_holder<k, T, Ts...>::type> & >::type
    _get_block(_BlockMultiPhaseConstructor<T, Ts...>& t) {
      _BlockMultiPhaseConstructor<Ts...>& base = t;
      return _get_block<k - 1>(base);
    }


    template <typename T=Elem<def::Euclidean, 0>, typename... Ts>
    void _copy_elem_from_block(_ElemMultiPhaseConstructor<T, Ts...>&e,
			       const _BlockMultiPhaseConstructor<T, Ts...>&b,
			       size_t ind) {
      _ElemMultiPhaseConstructor<Ts...> & e_base = e;
      const _BlockMultiPhaseConstructor<Ts...> & b_base = b;
      e.head = b.head[ind];      
      _copy_elem_from_block<Ts...>(e_base, b_base, ind);
    }

    template <>
    void _copy_elem_from_block(_ElemMultiPhaseConstructor<>&e,
			       const _BlockMultiPhaseConstructor<>&b,
			       size_t ind) {
    }

    template <typename T=Elem<def::Euclidean, 0>, typename... Ts>
    size_t _get_max_len(const _ElemMultiPhaseConstructor<T, Ts...> &e) {
      const _ElemMultiPhaseConstructor<Ts...> & e_base = e;
      return std::max(e.head.len, _get_max_len<Ts...>(e_base));
    }

    template <>
    size_t _get_max_len(const _ElemMultiPhaseConstructor<> &e) {
      return 0;
    }

    template <typename T=Elem<def::Euclidean, 0>, typename... Ts>
    size_t _get_max_len(const _BlockMultiPhaseConstructor<T, Ts...> &b) {
      const _BlockMultiPhaseConstructor<Ts...> & b_base = b;
      return std::max(b.head.get_max_len(), _get_max_len<Ts...>(b_base));
    }

    template <>
    size_t _get_max_len(const _BlockMultiPhaseConstructor<> &b) {
      return 0;
    }

    
    
  }

    

}

#endif /* _D2_INTERNAL_H_ */
