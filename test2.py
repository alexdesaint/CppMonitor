import os
path = '../../../mingw64/lib'
files = []
for i in os.listdir(path):
    if i.startswith("libclang"):
        print(i.replace('lib', '').replace('.a', ''))
