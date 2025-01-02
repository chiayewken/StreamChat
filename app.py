import base64
import io

import anthropic
import streamlit as st
from PIL import Image
from streamlit_paste_button import paste_image_button


def reset_chat():
    st.session_state.messages = []
    st.rerun()


def convert_image_to_text(image: Image.Image, form: str = "PNG") -> str:
    # This is also how OpenAI encodes images: https://platform.openai.com/docs/guides/vision
    with io.BytesIO() as output:
        image.save(output, format=form)
        data = output.getvalue()
    return base64.b64encode(data).decode("utf-8")


def convert_text_to_image(text: str) -> Image.Image:
    data = base64.b64decode(text.encode("utf-8"))
    return Image.open(io.BytesIO(data))


def load_image_message(image: Image.Image) -> dict:
    data = dict(
        type="image",
        source=dict(
            type="base64",
            media_type="image/webp",
            data=convert_image_to_text(image, form="WEBP"),
        ),
    )

    return dict(role="user", content=[data])


def parse_image_message(message: dict) -> Image.Image:
    if (
        not isinstance(message["content"], str)
        and message["content"][0]["type"] == "image"
    ):
        return convert_text_to_image(message["content"][0]["source"]["data"])


def main():
    if st.query_params.get("key", "") != st.secrets["USER_KEY"]:
        st.balloons()
        return

    model_id = st.text_input("Model ID", value="claude-3-5-sonnet-20241022")
    client = anthropic.Anthropic(api_key=st.secrets["API_KEY"])

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            image = parse_image_message(message)
            if image:
                st.image(image)
            else:
                st.markdown(message["content"])

    paste_result = paste_image_button("📋 Paste an image")
    if paste_result.image_data is not None:
        st.session_state.messages.append(load_image_message(paste_result.image_data))

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
