import random

# Takes an id and generates a psuedo hash string.
# This hash is simple and very tolerable for urls
def falseHash(id):
    hashableID = id * 11
    idFirstHalf = hashableID // 10
    idSecondHalf = hashableID % 10
    hash = "0r" + str(idFirstHalf) + "p" + str(idSecondHalf) + "g" + str(random.randint(301,399))
    return hash

# Takes a hashed id and reverses the falseHash
def dehash(hash):
    hashLen = len(hash)
    reverseHash = hash[2:hashLen - 6] + hash[hashLen - 5]
    trueHash = int(reverseHash) / 11
    return trueHash
