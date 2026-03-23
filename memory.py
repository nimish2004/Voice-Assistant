# conversation memory

conversation_history = []

MAX_HISTORY = 6

def add_to_memory(role, text):
    global conversation_history

    conversation_history.append({
        "role": role,
        "content": text
    })

    # keep only last few messages
    if len(conversation_history) > MAX_HISTORY:
        conversation_history.pop(0)


def get_memory():
    return conversation_history