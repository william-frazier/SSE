
from random import sample
from Crypto.Cipher import AES
from Cryptodome.Hash import HMAC, SHA256



documents = [["this is a test",0],["Test this file",1],["here is the text",2],["the text is missing",3]]
keywords = ["this","is","test","text"]

key_f = b'\x00'*16
key_p = b'\x11'*16
iv = b'\x00'*16



def build_RAM1(documents, keywords):
    """
    Builds an array of lists. Each list is a document ID, a pointer to the next
    list which is tracking the same word (if such a list exists), an int
    keeping track of which word this is for, and a boolean designating if this
    is the first time a list for this word appears. This is a little complicated 
    because Python doesn't have pointers which is ideally what I would use.
    """
    
    # first I randomly shuffle the order of the documents because otherwise
    #a search would reveal the order of the documents in the database when 
    #they are searched.
    # sample() is not cryptographically secure so it's not what would be used 
    #in a real deployment.
    documents = sample(documents, len(documents))
    
    RAM1 = []
    for word in keywords:
        # we need a marker to keep track of when a word is new in order to 
        #construct our table later
        new_word = True
        
        for document in documents:
            if word.lower() in document[0].lower():
                # If the keyword appears in the document, then make a note of 
                #this and save it to RAM1
                i = keywords.index(word.lower())
                RAM1.append([document[1], None, i, new_word])
                i+=1
                # when we're not on a new word, we update the pointer of the
                #previous list
                if not new_word:
                    RAM1[-2][1] = len(RAM1) - 1
                new_word = False
    return RAM1



def build_RAM2(RAM1):
    """
    This function randomly permutes RAM1 and updates all of the "pointers".
    """
    
    # As with build_RAM1(), we are using sample() which is not cryptographically
    #secure.
    RAM2 = sample(RAM1, len(RAM1))
    
    # This loop just allows us to update our pointers. Again, it's a bit 
    #complicated because Python doesn't have pointers.
    for item in RAM2:
        location = RAM1.index(item)
        location = RAM1[location][1]
        if location != None:
            pointed_to = RAM1[location]
            pointed_to = RAM2.index(pointed_to)
            item[1] = pointed_to
        item = item[:2]
    #RAM2[i][0] is document ID
    #RAM2[i][1] is pointed to next document ID
    #RAM2[i][2] is the index of the keyword
    #RAM2[i][3] is a boolean describing if it is the first in a chain
    return RAM2



def build_RAM3(RAM2, keywords):
    """
    This function encrypts everything in RAM2. It does this by first finding 
    key_w = PRF(key_f, word) 
    for whatever word the current list is tracking. It then uses that key_w
    in AES to encrypt the two elements in RAM2 (there is no longer any need to
    keep track of the word so we can ditch the third element, and the boolean
    is only being used for the build_table() function).
    """
    
    RAM3 = []
    table = build_table(RAM2, keywords)
    
    for element in RAM2:
        current_list = []
        
        # Here we find key_w which is our word run through a PRF
        PRF = HMAC.new(key_f, digestmod=SHA256)
        PRF.update(pkcs7_pad(keywords[element[2]].encode()))
        key_w = PRF.digest()
        for item in element[:2]:
            padded_item = pkcs7_pad(str(item).encode())
            # I create a new cipher each time because I was having trouble 
            #getting it to work when I didn't. Not sure what the problem was 
            #but this doesn't appear to noticably slow the performance.
            # There's no need to initialize it again until a new key_w is 
            #selected.
            cipher = AES.new(key_w, AES.MODE_CBC, iv)
            ciphertext = cipher.encrypt(padded_item)
            current_list.append(ciphertext)
            # current_list is now [enc(documentID), enc(pointer to next elt)]
        RAM3.append(current_list)
    return RAM3, table
        
  
      
def build_table(RAM2, keywords):
    """
    This function builds our table which allows us to find the location of the
    first pointer in the chain for a given word. This should technically return
    an array, not a dictionary, but that would require a small-domain PRP 
    (and we need to be able to tweak the output size) which is really difficult
    to do based on what I saw online. So I'm simply using AES as my PRP in order
    to get a similar effect.
    """
    
    table = {}
    for entry in RAM2:
        # If this is the first element in a word chain:
        if entry[-1]:
            # The location in RAM2 is the same as RAM3 but can be searched easily
            index = RAM2.index(entry)
            # Again, we use HMAC as a PRF to derive key_w 
            PRF = HMAC.new(key_f, digestmod=SHA256)
            PRF.update(pkcs7_pad(keywords[entry[2]].encode()))
            key_w = PRF.digest()
            
            # Encrypt the index where the chain starts. This way the server 
            #can know nothing about where a given chain starts until we search
            #for that word.
            cipher = AES.new(key_w, AES.MODE_CBC, iv)
            value = cipher.encrypt(pkcs7_pad(str(index).encode()))
            
            #This should be a small domain PRP but this is my simulation of that.
            PRP = AES.new(key_p, AES.MODE_CBC, iv)
            table_location = PRP.encrypt(pkcs7_pad(keywords[entry[2]].encode()))
            table[table_location] = value
    return table
        
    
    
def produce_search_tokens(keyword):
    """
    When the client wants to search, they need to compute a search token
    tk = (tk1,tk2) = (PRP(w,key_p),PRF(w,key_f)). This function finds the 
    token.
    """
    
    keyword = pkcs7_pad(keyword.lower().encode())
    PRP = AES.new(key_p, AES.MODE_CBC, iv)
    tk1 = PRP.encrypt(keyword)
    PRF = HMAC.new(key_f, digestmod=SHA256)
    PRF.update(keyword)
    tk2 = PRF.digest()
    return tk1, tk2
    


def search_db(tk1,tk2,db,table):
    """
    This function simulates the server searching. When the client creates the
    encrypted database, they will pass it along with the table to the server. 
    Then, when the client wants to search, they will pass along their search
    token which consists of tk1,tk2. The server is now able to use these in 
    order to find the IDs of all documents which the keyword being searched for.
    Notice that the server never sees the word being search or any of the 
    contents of the documents, only the IDs of the documents in which the 
    word being searched appears.
    """
    
    # The server uses tk1 to find the beginning of the chain for the word.
    try:
        pointer = table[tk1]
        
    except:
        raise KeyError("The key you are searching for was not used in constructing the database so you cannot search for it.")
        
    # The pointer found in the table is encrypted under tk2 so the server 
    #now uses that token to decrypt the pointer.
    cipher = AES.new(tk2, AES.MODE_CBC, iv)
    decrypted_pointer = cipher.decrypt(pointer)
    location = int(remove_pkcs_pad(decrypted_pointer).decode())
    
    # value now represents the beginning of the word chain.
    value = db[location]
    stop = False
    documents = set()
    
    # As long as the pointer is not None, we keep following pointers.
    while not stop:
        
        # The document IDs are all encrypted under tk2 so the server must 
        #decrypt them.
        cipher = AES.new(tk2, AES.MODE_CBC, iv)
        document = cipher.decrypt(value[0])
        documents.add(int(remove_pkcs_pad(document)))
        
        # The server also decrypted the pointer using tk2.
        cipher = AES.new(tk2, AES.MODE_CBC, iv)
        decryption_pointer = remove_pkcs_pad(cipher.decrypt(value[1]))
        
        # If this was the end of the chain then the server stops.
        if decryption_pointer == b'None':
            stop = True
        else:
            # Otherwise, update the pointer and repeat the process.
            value = db[int(decryption_pointer)]
    return documents
    


# =============================================================================
#  The following is code I took from class in order to make padding and 
#  unpadding easier for me. I did not write any of the code below this comment.
# =============================================================================
     
        
def pkcs7_pad(data):
    padding_size = (AES.block_size - len(data)) % AES.block_size
    if padding_size == 0:
        padding_size = AES.block_size
    padding = (chr(padding_size)*padding_size).encode()
    return data + padding

def remove_pkcs_pad(padded_msg, block_size=16):
    """Removes PKCS#7 padding if it exists and returns the un-padded message
    Args:
        padded_msg  (bytes/bytearray)  
    ret(bytes/bytearray): un-padded message if the padding is valid, None otherwise 
    """
    padded_msg_len = len(padded_msg)

    # Check the input length
    if padded_msg_len == 0:
        return None

    # Checks if the input is not a multiple of the block length
    if (padded_msg_len % block_size):
        return None

    # Last byte has the value
    pad_len = padded_msg[-1]

    # padding value is greater than the total message length
    if pad_len > padded_msg_len:
        return None

    # Where the padding starts on input message
    pad_start = padded_msg_len-pad_len

    # Check the ending values for the correct pad value
    for char in padded_msg[padded_msg_len:pad_start-1:-1]:
        if char != pad_len:
            return None

    # remove the padding and return the message
    return padded_msg[:pad_start]
