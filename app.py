import anthropic
import streamlit as st


def reset_chat():
    st.session_state.messages = []
    st.rerun()


def main():
    model_id = st.text_input("Username")
    api_key = st.text_input("Password", type="password")
    if not model_id:
        model_id = "claude-3-5-sonnet-20241022"
    if api_key:
        client = anthropic.Anthropic(api_key=api_key)
    else:
        return

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("What is your question?"):
        if prompt.strip().lower() == "clear":
            reset_chat()
            return

        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            # noinspection PyTypeChecker
            with client.messages.stream(
                model=model_id,
                max_tokens=1024,
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
            ) as stream:
                for text in stream.text_stream:
                    full_response += text or ""
                    message_placeholder.markdown(full_response)

            message_placeholder.markdown(full_response)
        # Add assistant response to chat history
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )

    # Add a button to clear the conversation
    if st.button("Clear Conversation"):
        reset_chat()


if __name__ == "__main__":
    main()
