import os
import dotenv


def generate_directories():
    dotenv.load_dotenv()

    root_dir = os.getenv("ROOT_DIR")

    directories = [
        os.path.join(root_dir, "raw", "gdp"),
        os.path.join(root_dir, "raw", "audit"),
        os.path.join(root_dir, "standardized", "gdp"),
        os.path.join(root_dir, "standardized", "errors")
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)