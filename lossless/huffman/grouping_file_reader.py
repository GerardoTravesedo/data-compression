class GroupingFileReader:
    """
    This class represents an iterator that allows us to group characters in a file into groups of configurable size.
    This can be used, for example, to implement blocking in Huffman codes.

    It works by wrapping an iterator for the input file. Every time next is called, it internally calls next on the
    input file iterator and returns the result as a list of groups of group_size. Rather than returning "Hello World!",
    it returns [[He], [ll], [o ], [Wo], [rl], [d!]] when group_size = 2.
    """

    def __init__(self, file_handler, group_size):
        self._remaining_string = None
        self._file_handler = file_handler
        self._group_size = group_size

    def __iter__(self):
        return self

    def __next__(self):
        try:
            string_to_group = \
                self._remaining_string + next(self._file_handler) if self._remaining_string \
                else next(self._file_handler)
        # If it gets to the end of the file but there is remaining stuff to return, then return it
        except StopIteration:
            if not self._remaining_string:
                raise StopIteration
            else:
                last_group = list(self._remaining_string)
                self._remaining_string = None
                return last_group

        # Grouping elements in groups of group_size
        grouped_symbols = [string_to_group[i:i + self._group_size]
                           for i in range(0, len(string_to_group), self._group_size)]

        # If there is a group at the end that doesn't contain group_size characters, then save that to be combined
        # with other following characters and form a group later
        if len(grouped_symbols[-1]) < self._group_size:
            self._remaining_string = grouped_symbols[-1]
            return grouped_symbols[:-1]

        self._remaining_string = None
        return grouped_symbols
