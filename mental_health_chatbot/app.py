import WordPreprocessing as wp

chat_number = 1
while True:
    user_input = input(f"You (Chat Number- {chat_number}): ")
    chat_number+=1
    if "exit" in user_input:
        print("Good Bye!")
        break
    else:
        wp.Word_Preprocessing(user_input)
