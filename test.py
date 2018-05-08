boarddata2 = [0, 1, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15]
test = [0,1,3,6,10,14,4,5,7,2,9,12]
possibilities = list(filter(lambda x: x not in test, boarddata2))
print(possibilities)