from itertools import zip_longest

def split_seq(seq, n):
	s = [seq[i::n] for i in range(n)]
	return [ [ i for i in row  if i is not None ]  for row in zip_longest(*s)]