
try:
    with open("test_result_success.log", "r", encoding="utf-8") as f:
        print(f.read())
except:
    try:
        with open("test_result_success.log", "r", encoding="utf-16") as f:
            print(f.read())
    except:
        with open("test_result_success.log", "r", encoding="cp1252") as f:
             print(f.read())
