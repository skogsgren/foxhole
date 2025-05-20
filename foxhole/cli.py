import search
import sys
from pathlib import Path



def check_method(search_method:str, search_methods:list):
    if search_method.isdigit():
        search_method = search_methods[int(search_method)-1]
    method_provided = True
    if search_method not in search_methods:
        raise TypeError("ERROR: Search method must be out of", search_methods)
    return search_method

def select_model(i:int):
    if i == 1: se = search.TFIDFSearchEngine()
    if i == 2: se = search.BM25SearchEngine()
    if i == 3: se = search.ChromaSemanticSearchEngine()
    return se


def main():

    # get db file name from command line
    try:
        db_path = Path(sys.argv[1])
    except:
        raise TypeError("ERROR: No path provided at all!")

    if not db_path.exists() or db_path.is_dir():
        raise TypeError("ERROR: No valid path to a .db file provided!")
    print("Database file", db_path, "selected.")


    # try getting optional top_k
    k_provided = False
    try:
        if sys.argv[2][:3] == "top":
            top_k = int(sys.argv[2][3:])
            k_provided = True
            print("top_k =", top_k)
    except:
        pass

    interactive = False

    # select search method to be used
    search_methods = ("TFIDF", "BM25", "ChromaSemantic")
    try:
        search_method = check_method(sys.argv[2+int(k_provided)], search_methods)
        method_provided = True
        print("Search method", search_method, "selected.")
    except:
        #raise TypeError("ERROR: No search method provided!")
        method_provided = False
        interactive = True
        print("No search method selected.")
    
    if method_provided:
        se = select_model(search_methods.index(search_method)+1)
        se.load_db(db_path)
    

    # try getting query from command line or start interactive mode
    if not interactive:
        try:
            query = " ".join(sys.argv[3+int(k_provided):])
        except:
            interactive = True

    # conduct the search and print the results
    if not interactive:
        print("Searching with method", search_method, "the following query:", query)
        if k_provided:
            result = se.search_db(query, top_k)
        else:
            result = se.search_db(query)
        print("result:\n", result)
    else: # interactive input loop
        while True:
            if not method_provided:
                user_input = input("Select search method:\n")
                search_method = check_method(user_input, search_methods)
                print("Search method", search_method, "selected.")
                se = select_model(search_methods.index(search_method)+1)
                se.load_db(db_path)

            user_input = input("Type whatever query or enter 'q' to quit:\n")
            if user_input == "q":
                break
            query = user_input
            print("Searching with method", search_method, "the following query:", query)
            if k_provided:
                result = se.search_db(query, top_k)
            else:
                result = se.search_db(query)
            print("result:\n", result)



if __name__ == "__main__":
    main()

