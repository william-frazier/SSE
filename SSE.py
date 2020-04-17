
from random import sample
from Crypto.Cipher import AES
from Cryptodome.Hash import HMAC, SHA256
from Crypto.Random import get_random_bytes
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords 
import time
import re


documents = [["Massachusetts, officially known as the Commonwealth of Massachusetts, is the most populous state in the New England region of the northeastern United States. It borders on the Atlantic Ocean to the east, the states of Connecticut and Rhode Island to the south, New Hampshire and Vermont to the north, and New York to the west. The capital of Massachusetts is Boston, which is also the most populous city in New England. It is home to the Greater Boston metropolitan area, a region influential upon American history, academia, and industry. Originally dependent on agriculture, fishing and trade, Massachusetts was transformed into a manufacturing center during the Industrial Revolution. During the 20th century, Massachusetts's economy shifted from manufacturing to services. Modern Massachusetts is a global leader in biotechnology, engineering, higher education, finance, and maritime trade",0],
             ["Boston is the capital and most populous city[9] of the Commonwealth of Massachusetts in the United States, and the 21st most populous city in the United States. The city proper covers 49 square miles (127 km2) with an estimated population of 694,583 in 2018,[3] also making it the most populous city in New England.[2] Boston is the seat of Suffolk County as well, although the county government was disbanded on July 1, 1999.[10] The city is the economic and cultural anchor of a substantially larger metropolitan area known as Greater Boston, a metropolitan statistical area (MSA) home to a census-estimated 4.8 million people in 2016 and ranking as the tenth-largest such area in the country.[11] As a combined statistical area (CSA), this wider commuting region is home to some 8.2 million people, making it the sixth most populous in the United States.",1],
             ["New England is a region composed of six states in the northeastern United States: Maine, Vermont, New Hampshire, Massachusetts, Rhode Island, and Connecticut.[4][5][6][7][8][9] It is bordered by the state of New York to the west and by the Canadian provinces of New Brunswick to the northeast and Quebec to the north. The Atlantic Ocean is to the east and southeast, and Long Island Sound is to the southwest. Boston is New England's largest city, as well as the capital of Massachusetts. Greater Boston is the largest metropolitan area, with nearly a third of New England's population; this area includes Worcester, Massachusetts (the second-largest city in New England), Manchester, New Hampshire (the largest city in New Hampshire), and Providence, Rhode Island (the capital of and largest city in Rhode Island).",2],
             ["Worcester is a city, and county seat of, Worcester County, Massachusetts, United States. Named after Worcester, England, as of the 2010 Census the city's population was 181,045,[4] making it the second-most populous city in New England after Boston.[a] Worcester is approximately 40 miles (64 km) west of Boston, 50 miles (80 km) east of Springfield and 40 miles (64 km) north of Providence. Due to its location in Central Massachusetts, Worcester is known as the 'Heart of the Commonwealth', thus, a heart is the official symbol of the city. However, the heart symbol may also have its provenance in lore that the Valentine's Day card, although not invented in the city, was first mass-produced and popularized by Worcester resident Esther Howland.[6]",3],
             ["Providence is the capital and most populous city of the state of Rhode Island and is one of the oldest cities in the United States.[6] It was founded in 1636 by Roger Williams, a Reformed Baptist theologian and religious exile from the Massachusetts Bay Colony. He named the area in honor of 'God's merciful Providence' which he believed was responsible for revealing such a haven for him and his followers. The city is situated at the mouth of the Providence River at the head of Narragansett Bay.",4],
             ["Greater Boston is the metropolitan region of New England encompassing the municipality of Boston, the capital of the U.S. state of Massachusetts and the most populous city in New England, as well as its surrounding areas. The region forms the northern arc of the US northeast megalopolis and as such, Greater Boston can be described either as a metropolitan statistical area (MSA), or as a broader combined statistical area (CSA). The MSA consists of most of the eastern third of Massachusetts, excluding the South Coast region and Cape Cod; while the CSA additionally includes the municipalities of Manchester (the largest city in the U.S. state of New Hampshire), Worcester, Massachusetts (the second largest city in New England), as well as the South Coast region and Cape Cod in Massachusetts. While the small footprint of the city of Boston itself only contains an estimated 685,094, the urbanization has extended well into surrounding areas; the CSA is one of two in Massachusetts, the only other being Greater Springfield. Greater Boston is the only CSA-form statistical area in New England which crosses into three states (Massachusetts, New Hampshire and Rhode Island).",5],
             ["Boston University (BU) is a private research university in Boston, Massachusetts. The university is nonsectarian,[9] but has been historically affiliated with the United Methodist Church.[4][5] The university has over 3,900 faculty members and nearly 33,000 students, and is one of Boston's largest employers.[10] It offers bachelor's degrees, master's degrees, doctorates, and medical, dental, business, and law degrees through 18 schools and colleges on two urban campuses. The main campus is situated along the Charles River in Boston's Fenway-Kenmore and Allston neighborhoods, while the Boston University Medical Campus is located in Boston's South End neighborhood.",6]]

# All documents are the first paragraph of a Wikipedia article:
# document 0 is Massachusetts
# document 1 is Boston
# document 2 is New England
# document 3 is Worcester
# document 4 is Providence
# document 5 is Greater Boston
# document 6 is BU

key_f = get_random_bytes(16)
key_p = get_random_bytes(16)
iv = get_random_bytes(16)


def produce_keywords(document):
    stop_words = set(stopwords.words('english')) 
#    porter = PorterStemmer()
    stemmed_file = ""
    regex = re.compile('[^a-zA-Z]')
    #First parameter is the replacement, second parameter is your input string
    document = regex.sub(' ', document)
    document = document.lower()
    document = document.split()
    for word in document:
        if word not in stop_words:
            stemmed_file += word
            stemmed_file += " "
    return stemmed_file



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
    


def system_run(documents):
    keywords = set()
    for document in documents:
        for word in produce_keywords(document[0]).split():
            keywords.add(word)
    keywords = list(keywords)
    keywords.sort()
    print("The system will allow you to search for the following keywords:", keywords)
    time.sleep(1)
    print()
    print("Building RAM1...")
    time.sleep(2)
    RAM1 = build_RAM1(documents, keywords)
    print("Here is RAM1:")
    print(RAM1)
    time.sleep(2)
    print()
    print("Building RAM2...")
    time.sleep(2)
    RAM2 = build_RAM2(RAM1)
    print("Here is RAM2:")
    print(RAM2)
    time.sleep(2)
    print()
    print("Building RAM3...")
    time.sleep(2)
    RAM3 = build_RAM3(RAM2,keywords)
    table = RAM3[1]
    print("Here is RAM3:")
    print(RAM3[0])
    time.sleep(2)
    print()
    print("Here is the lookup table:")
    print(table)
    time.sleep(3)
    print()
    x = ()
    print("You can now search for any of the following words:", keywords)
    while True:
#        
        print("What word would you like to search? (Or type 'quit' to exit.) ")
        x = input()
        x = x.lower()
        if x == 'quit':
            break
        print("Searching for", x)
        if x not in keywords:
            print("Invalid choice.")
            print()
        else:
            tk1,tk2 = produce_search_tokens(x)
            print("Your search tokens are:", tk1, "and", tk2)
            time.sleep(1)
            print("Looking at table[", tk1, "]")
            print("Found pointer to slot", table[tk1])
            time.sleep(2)
            print("Decrypting...")
            time.sleep(2)
            cipher = AES.new(tk2, AES.MODE_CBC, iv)
            decrypted_pointer = cipher.decrypt(table[tk1])
            location = int(remove_pkcs_pad(decrypted_pointer).decode())
            print("Found", location)
            print("Following pointers...")
            time.sleep(2)
            print("IDs of documents containing", x + ":", search_db(tk1,tk2,RAM3[0],table))
            time.sleep(2)
            print()
    


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
