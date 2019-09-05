import os
import sys
import marshal
import array
import heapq
import itertools


from operator import itemgetter

from heapq import heappush, heappop

try:
    import cPickle as pickle
except:
    import pickle


def frequencies(msg):
    #finds frequencies of each character in list and adds it to a dictionary
    freq = {}
    for x in msg:
        if x not in freq:
            freq[x] = 1
        else:
             freq[x] += 1
    return freq


def findcodes(tree):
    #convert the list made by walk tree into actual codes
    filled = [] #stores filled non leaf nodes
    nodes = [] #stores half filled non leaf nodes
    path = [] #stores current path
    code = {} #code book

    #initialization invariant: path is empty
    #maintenance invariant: path is currently on a non filled node
    #termination invariant: path is empty
    for x in tree:
        #checks to see if current item in list is a leaf node
        if type(x) == type(()):
            #if it is a leaf node add previous node to filled
            filled.append(nodes.pop(-1))
            code[x[1]] = path.copy()
            if len(nodes)<1:
                return code
            #if the node has 2 children then new path is last open node in nodes
            path = nodes[-1].copy()
            filled = nodes.pop(-1)
            continue
        #if current item in tree is not a node then it is an int that represents am edge on the tree
        path.append(x)
        #checks if the current path is filled if it isnt then add it to nodes
        #else you remove the current path from nodes
        if path not in filled:
            nodes.append(path.copy())
        elif path in nodes:
            nodes.remove(path)

    return code




def walktree(tree, direction):
    codes  = []
    #recursive function that goes through tree made in tree function
    if type(tree) == type(()):
        #checks if the current node has a child if it doesn't then append the direction and the leaf tuple
        try:
            tree[1][0]
        except:
            codes.append(direction)
            codes.append(tree)
            return codes

        #if the current node is not a leaf node then add the current direction to codes
        if type(tree[0]) != type(()):
            codes.append(direction)

        #call function on left side of tuple and right side of tuple
        left = walktree(tree[0], 0)
        right = walktree(tree[1], 1)
        #add what is returned from both left and right to the codes list
        codes += left
        codes += right

    return codes


def tree(freq):
    #sorts frequency by the frequencies and turns into list of tuples
    freq = sorted(freq.items(),key=lambda x: x[1])
    tree = [x[::-1] for x in freq]
    #swap tuples and set to tree

    #initialization invariant: first element of tree is lowest frequency
    #maintenance invariant: len of tree is 1 less after each iteration
    #termination invariant: len of tree is 1
    while len(tree)>1:
        #take 2 lowest numbers from tree and make a head with both of their frequencies added.
        #make a child node with both the left and right nodes in a tuple
        #append the new node to the tree and then resort the tree by the first value in each tuple
        left = tree.pop(0)
        right = tree.pop(0)
        child  = (left, right)
        head = left[0]+right[0]
        node = (head, child)
        tree.append(node)
        tree = sorted(tree ,key=itemgetter(0))
    return tree

def encode(msg):
    freq = frequencies(msg)
    ctree = tree(freq)
    ring = {}
    #try calling walk tree on left and right side of tree
    #if it fails that means that their is only one leaf node which is easily solved
    try:
        tree1 = walktree(ctree[0][1][0], 0)
        tree2 = walktree(ctree[0][1][1], 1)
    except:
        ring[chr(ctree[0][1])] = "0"
        enc = "0"
        return (enc, ring)
    #find the codes of left and right tree
    codes1 = findcodes(tree1)
    codes2 = findcodes(tree2)
    #combine both codes to create the temp ring
    tempring = {**codes1, **codes2}
    enc = []
    #convert the codes to strings and add to ring dict
    for x in tempring:
        s = "".join(str(y) for y in tempring[x])
        ring[x] = s
    #encode the message using ring
    for x in msg:
        enc.append(ring[x])
    #make encode a single string
    enc = "".join(str(y) for y in enc)
    return(enc, ring)



def decode(msg, decoderRing):
    #decoderring is a dictionary
    #go through msg by starting at first character, then look in dictionary to see if theirs a match
    #then add another character and continue on until you find a character in dictionary
    #reset bin and startover
    bin = ""
    output = array.array('B')
    ring = dict((v,k) for k,v in decoderRing.items())
    for x in msg:
        bin+=str(x)
        if ring.get(str(bin)) != None:
            output.append(ring[bin])
            bin = ""
    return output

def compress(msg):
    (enc, ring) = encode(msg)
    # Initializes an array to hold the compressed message.
    compressed = array.array('B')
    buf = 0
    count = 0
    size = 0
    for x in enc:
        if x == '0':
            buf = (buf << 1)
        else:
            buf = ((buf << 1) | 1)
        count += 1
        size += 1
        #check if current byte is full.  if it is append it to byte array and then start over
        if(count == 8):
            compressed.append(buf)
            buf = 0
            count = 0

    #padds the byte array
    if count!=0:
         padding = 8-count
         for x in range(0,padding):
             buf = (buf<<1)
         compressed.append(buf)

    #add a size key to ring so that decompress can know how many characters it needs to read
    ring["size"] = size
    return (compressed, ring)

def decompress(msg, decoderRing):
    # Represent the message as a bytearray
    byteArray = array.array('B',msg)
    bits = ""
    size = 0
    max = decoderRing["size"] #amount of characters
    for x in byteArray:
        for i in range(7,-1,-1):
            if size!=max: #once you reach the amount of characters don't read in the padded characters
                bits += str(x >> i & 1)
                size+=1;

    message = decode(bits, decoderRing)
    return message

def usage():
    sys.stderr.write("Usage: {} [-c|-d|-v|-w] infile outfile\n".format(sys.argv[0]))
    exit(1)

if __name__=='__main__':
    if len(sys.argv) != 4:
        usage()
    opt = sys.argv[1]
    compressing = False
    decompressing = False
    encoding = False
    decoding = False
    if opt == "-c":
        compressing = True
    elif opt == "-d":
        decompressing = True
    elif opt == "-v":
        encoding = True
    elif opt == "-w":
        decoding = True
    else:
        usage()

    infile = sys.argv[2]
    outfile = sys.argv[3]
    assert os.path.exists(infile)

    if compressing or encoding:
        fp = open(infile, 'rb')
        msg = fp.read()
        fp.close()
        if compressing:
            compr, decoder = compress(msg)
            fcompressed = open(outfile, 'wb')
            marshal.dump((pickle.dumps(decoder), compr), fcompressed)
            fcompressed.close()
        else:
            enc, decoder = encode(msg)
            #print(msg)
            fcompressed = open(outfile, 'wb')
            marshal.dump((pickle.dumps(decoder), enc), fcompressed)
            fcompressed.close()
    else:
        fp = open(infile, 'rb')
        pickleRick, compr = marshal.load(fp)
        decoder = pickle.loads(pickleRick)
        fp.close()
        if decompressing:
            msg = decompress(compr, decoder)
        else:
            msg = decode(compr, decoder)
        fp = open(outfile, 'wb')
        fp.write(msg)
        fp.close()
