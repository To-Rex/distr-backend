import uuid

# Generate a random UUID and convert it to a string for use as a key
unique_key = str(uuid.uuid4())
my_dict = {unique_key: "some value"}

print(f"Generated Customer ID: {unique_key}")

