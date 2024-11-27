# Intel Support KB Content Editor

This Python program scrapes Intel support articles, extracts metadata and content, and generates suggestions using a generative AI model. The suggestions are saved in markdown files for review.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Environment Variables](#environment-variables)
- [System Prompt](#system-prompt)
- [Dependencies](#dependencies)
- [License](#license)

## Installation

1. Clone the repository:

    ```sh
    git clone https://github.com/amr-jwright2/gss_gpt_based_bulk_kb_article_review.git
    cd gss_gpt_based_kb_article_review
    ```

2. Create a virtual environment:

    ```sh
    python -m venv venv
    ```

3. Activate the virtual environment:

    - On Windows:

        ```sh
        .\venv\Scripts\activate
        ```

    - On macOS and Linux:

        ```sh
        source venv/bin/activate
        ```

4. Install the dependencies:

    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. Create a `.env` file in the root directory and add your credentials:

    ```env
    CLIENT_ID=your_client_id
    CLIENT_SECRET=your_client_secret
    ```

2. Ensure you have a CSV file named `Report.csv` in the root directory with a column named `External URL` containing the URLs to be processed.

3. Review and update the system prompt in the `Intel Support KB Content Editor.md` file as needed.

4. Run the program:

    ```sh
    python gpt_article_reviewer.py
    ```

## Environment Variables

The program uses the following environment variables, which should be stored in a `.env` file in the root directory:

- `CLIENT_ID`: Your client ID for authentication.
- `CLIENT_SECRET`: Your client secret for authentication.

## System Prompt

The system prompt is loaded from the `Intel Support KB Content Editor.md` file. Review and update this file to customize the prompt used by the generative AI model.

## Dependencies

The required dependencies are listed in the `requirements.txt` file. Install them using the following command:

```sh
pip install -r requirements.txt
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
```

Feel free to customize the README file further as per your requirements.