import os
from transformers import MarianMTModel, MarianTokenizer

def download_and_save_model(model_name, save_directory):
    """
    Downloads a model and tokenizer from Hugging Face and saves it to a local directory.
    """
    if os.path.exists(save_directory):
        print(f"Directory {save_directory} already exists. Skipping download.")
        return

    print(f"Downloading model: {model_name} to {save_directory}...")
    try:
        # Download tokenizer and model
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)

        # Save them to the specified directory
        tokenizer.save_pretrained(save_directory)
        model.save_pretrained(save_directory)
        print(f"Model {model_name} downloaded and saved successfully.")
    except Exception as e:
        print(f"Failed to download model {model_name}. Error: {e}")
        # Exit with a non-zero code to fail the Docker build if download fails
        exit(1)

if __name__ == "__main__":
    # The model we need for English to Turkish translation
    model_to_download = "Helsinki-NLP/opus-mt-en-tr"
    # The directory where the model will be saved inside the container
    # This should match the path used in translation_service.py
    save_path = "/app/models/translation/en-tr"
    
    # Ensure the parent directory exists
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    download_and_save_model(model_to_download, save_path) 