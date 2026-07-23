names = []

with open("team.txt", "r") as file:
    for line in file:
        line = line.strip()
        if line:
            parts = line.split("\t")
            name = parts[-1].strip()
            names.append(name)



for name in names:
    print(name)
