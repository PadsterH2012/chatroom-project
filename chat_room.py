class ChatRoom:
    def __init__(self):
        self.conversations = []

    # Task 1: Add a new conversation
    def add_conversation(self, name):
        conversation = Conversation(name=name)
        session.add(conversation)
        session.commit()
        self.conversations.append(conversation)

    # Task 2: Get all conversations
    def get_conversations(self):
        return session.query(Conversation).all()

    # Task 3: Delete a conversation
    def delete_conversation(self, id):
        conversation = session.query(Conversation).get(id)
        if conversation:
            session.delete(conversation)
            session.commit()

    # Task 4: Add a message to a conversation
    def add_message(self, conversation_id, text):
        conversation = session.query(Conversation).get(conversation_id)
        if conversation:
            message = Message(text=text)
            conversation.messages.append(message)
            session.commit()