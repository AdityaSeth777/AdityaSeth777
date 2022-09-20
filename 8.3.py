list1 = []

n = int(input("Enter number of elements : "))
# iterating till the range
for i in range(0, n):
	print("Enter the element: ")
	ele = input()
	list1.append(ele) # adding the element
# open file
a=input("Enter the name of the file you want to open: ")
with open(a, 'w+') as f:
	
	for items in list1:
		f.write('%s\n' %items)
	
	print("File written successfully.")


# close the file
f.close()
