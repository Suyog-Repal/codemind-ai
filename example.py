class Area:
    # Function to calculate rectangle area
    def rectangle_area(self, length, width):
        return length * width

    # Function to calculate square area
    def square_area(self, side):
        return side * side


# Create object
obj = Area()

# Input
length = int(input("Enter length of rectangle: "))
width = int(input("Enter width of rectangle: "))
side = int(input("Enter side of square: "))

# Output
print("Rectangle Area =", obj.rectangle_area(length, width))
print("Square Area =", obj.square_area(side))