
import streamlit as st
import json
from PIL import Image
import io

def load_jsonl_data(uploaded_file):
    """Load JSONL data from uploaded file"""
    try:
        data = []
        for line in uploaded_file:
            line = line.decode("utf-8").strip()
            if line:
                data.append(json.loads(line))
        return data
    except Exception as e:
        st.error(f"Error loading JSONL file: {str(e)}")
        return None

def load_image(uploaded_image):
    """Load image from uploaded file"""
    try:
        return Image.open(uploaded_image)
    except Exception as e:
        st.error(f"Error loading image: {str(e)}")
        return None

def display_conversations(conversations):
    """Display Q&A conversations in a formatted way and allow adding new ones"""
    st.subheader("Conversations")

    # Convert into Q/A pairs
    qa_pairs = []
    current_pair = {}
    for conv in conversations:
        if conv["from"] == "human":
            if current_pair:
                qa_pairs.append(current_pair)
            current_pair = {"question": conv["value"]}
        elif conv["from"] == "gpt" and "question" in current_pair:
            current_pair["answer"] = conv["value"]
            qa_pairs.append(current_pair)
            current_pair = {}
    if current_pair:
        qa_pairs.append(current_pair)

    # Editable fields for existing pairs
    edited_pairs = []
    for i, pair in enumerate(qa_pairs, 1):
        q_value = st.text_input(f"Q{i}", value=pair.get('question', ''), key=f"q{i}")
        a_value = st.text_input(f"A{i}", value=pair.get('answer', ''), key=f"a{i}")
        edited_pairs.append({"from": "human", "value": q_value})
        edited_pairs.append({"from": "gpt", "value": a_value})
        st.markdown("---")

    # Add empty slots for new Q&A
    st.markdown("### ➕ Add New Q&A")
    num_new = st.number_input("Number of new Q&A pairs to add", min_value=1, max_value=5, value=1, step=1)
    for i in range(num_new):
        q_value = st.text_input(f"New Q{i+1}", value="", key=f"new_q{i}")
        a_value = st.text_input(f"New A{i+1}", value="", key=f"new_a{i}")
        if q_value or a_value:
            edited_pairs.append({"from": "human", "value": q_value})
            edited_pairs.append({"from": "gpt", "value": a_value})
        st.markdown("---")

    return edited_pairs

def main():
    st.set_page_config(page_title="Document VQA Dataset Reviewer", layout="wide")
    st.title("📄 Document VQA Dataset Reviewer")
    st.markdown("Upload your JSONL dataset and images to review and edit Q&A pairs")

    # File uploaders
    jsonl_file = st.file_uploader("Upload JSONL Dataset File", type="jsonl")
    uploaded_images = st.file_uploader("Upload Images", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

    if jsonl_file and uploaded_images:
        # Load dataset
        data = load_jsonl_data(jsonl_file)
        if not data:
            return

        total_items = len(data)
        st.sidebar.success(f"✅ Loaded {total_items} items")

        # Match images by filename
        image_dict = {img.name: img for img in uploaded_images}

        # Sidebar navigation
        selected_index = st.sidebar.number_input("Select Item Index", min_value=0, max_value=total_items-1, value=0)
        st.sidebar.markdown(f"**Item {selected_index+1} of {total_items}**")

        # Current item
        current_item = data[selected_index]

        # Two-column layout
        col1, col2 = st.columns([1, 1.5])

        with col1:
            st.subheader("Image")
            image_filename = current_item.get('image', '')
            if image_filename in image_dict:
                img = load_image(image_dict[image_filename])
                if img:
                    st.image(img, caption=image_filename, use_column_width=True)
            else:
                st.warning(f"No uploaded image found for: {image_filename}")

            st.subheader("Caption")
            st.markdown(f"*{current_item.get('caption', 'No caption available')}*")

        with col2:
            conversations = current_item.get('conversations', [])
            edited_conversations = display_conversations(conversations)
            current_item["conversations"] = edited_conversations

            # Download button for edited single item
            json_str = json.dumps(current_item, indent=2, ensure_ascii=False)
            st.download_button(
                label="💾 Download Edited Item",
                data=json_str,
                file_name=f"item_{current_item.get('id', 'N')}.json",
                mime="application/json"
            )

        # Download all edited data
        all_json_str = "\n".join(json.dumps(item, ensure_ascii=False) for item in data)
        st.download_button(
            label="📦 Download Full Updated Dataset",
            data=all_json_str,
            file_name="updated_dataset.jsonl",
            mime="application/json"
        )

    else:
        st.info("Please upload both JSONL dataset and corresponding images.")

if __name__ == "__main__":
    main()
