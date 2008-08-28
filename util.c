#include <caml/mlvalues.h>
#include <caml/alloc.h>
#include <caml/memory.h>
#include <time.h>

CAMLprim value process_time()
{
  return caml_copy_double((double) clock() / CLOCKS_PER_SEC);
}
