# Searchable Symmetric Encryption for CS568

To see my system in action: 'system_run()'. This will load the encrypted database with 6 documents which are paragraphs from Wikipedia. It will then step through the build process and allow you to search. For the same functionality on your own collection of documents named db: 'system_run(db)'

If you want to run the system step by step you will first need a list of lists of documents where the 0th item in each list is the document and the 1st item is an integer ID (call this list of lists db) and you will need a list of keywords (this can be created by running each document through produce_keywords() or you can create your own, call this list keywords).

1) Create RAM1 by running 'RAM1 = build_RAM1(db, keywords)'
2) Create RAM2 by running 'RAM2 = build_RAM2(RAM1)'
3) Create RAM3 and table by running 'RAM3, table = build_RAM3(RAM2, keywords)'
4) Now you can create search tokens by running 'tk1, tk2 = produce_search_tokens(word)'
5) Search by running 'search_db(tk1,tk2,RAM3,table)'
