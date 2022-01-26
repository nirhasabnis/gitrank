import math

class LizardExtension(object):

  def __init__(self):
    self.total_maintainability_index = 0
    self.total_files = 0

  def __call__(self, tokens, reader):
    ''' This method is called per file.
        tokens is a list of all the tokens in a file.'''
    unique_tokens = set()
    non_unique_tokens = []
    for token in tokens:
      if not(token == ')' or token == '}' or token == ']'):
        unique_tokens.add(token)
        non_unique_tokens.append(token)
      yield token

    num_functions = len(reader.context.fileinfo.function_list)
    if num_functions == 0:
      return

    avg_halstead_vol = round(len(non_unique_tokens) * math.log(len(unique_tokens), 2) / num_functions, 2)
    avg_cyclomatic_complexity = reader.context.fileinfo.average_cyclomatic_complexity
    avg_nloc =  reader.context.fileinfo.average_nloc
    print('avg_nloc:', avg_nloc)

    maintainability_index = 171 - 5.2 * math.log(avg_halstead_vol) \
         - 0.23 * avg_cyclomatic_complexity \
         - 16.2 * math.log(avg_nloc)
    reader.context.fileinfo.maintainability_index = maintainability_index

  def cross_file_process(self, fileinfos):
    ''' aggregate results across all the files '''
    for fileinfo in fileinfos:
      if hasattr(fileinfo, "maintainability_index"):
        self.total_maintainability_index += fileinfo.maintainability_index
        self.total_files += 1
      yield fileinfo

  def print_result(self):
    print('avg_maintainability_index:', round(self.total_maintainability_index / self.total_files, 2))
