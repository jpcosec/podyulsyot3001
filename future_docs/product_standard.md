 about issues. i think that all of them but match hardening are part of the same bigger problem. Organizing the modules, standardizing how to interact with them, creating an unified IO
  library, creating an unified CLI, creating an unified ui for that CLI using textual, mapping to a common langraph graph. testing the whole pipeline using spritetest.
  There are some definitions to make.
  state should be managed by langraph. the output of each node is better if it's managed in files for now.
  We should have a common way to wrapping tools.
  We should have a common way to wrapping langraph based nodes. (the scrapper falls out of this due to being an external library)
  We should have a common way to reviewing the output of nodes (the scrapper should be considered for this, and the generated documents)
  Unless theres a really good reason for it, we should always prioritize using tested libraries.
  Talking about langraph, we should always prioritize making things the more native posssible way.
  For interacting wiht the modules, each module must have it's own entrypoint with clear IOs and arguments. Then CLI wrapps them all, then langraph exposes an API, then textual interacts
  with the UI. Then later on we'll recover the ui that we are making in the other branches. Try to desing thinking on that, but prioritize for now making something that works.
  Always respect the standards.
  Use clean code on desing, with inline documentation, don't be a purist about this.
  There might be nodes that have things that can be shared in a common utils folder. don't do it yet.
  We must check the compatibility of the outputs of each step so we can make the pipeline run altogether.
  Besides langraph, we need an state manager, see what's already advanced on scraper about this.
  Create a long running plan that can be implemented in steps.
  define clear behaviour rules for each node, so when testing with testprite, once the pipeline runs end to end, we can add them to testprite for testing.