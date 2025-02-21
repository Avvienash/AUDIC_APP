from flask import Flask, render_template, request, redirect, url_for
import os
import markdown
import PyPDF2
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # Load API key from .env file

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# OpenAI client
client = OpenAI(
  base_url="https://api.openai.com/v1",
    api_key=os.environ.get('OPENAI_API_KEY'))


def pdf_to_text(file_path):
    with open(file_path, "rb") as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        # Initialize an empty string to store the text
        text = ''

        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += 'Page ' + str(page_num + 1) + '\n' + page.extract_text() + '\n\n'
            
    return text

@app.route("/", methods=["GET", "POST"])
def index():
    output_html = None
    results = False
    if request.method == "POST":
        # Save uploaded files
        records_file = request.files["records"]
        guidelines_file = request.files["guidelines"]
        print("Obatined files from user")

        records_path = os.path.join(UPLOAD_FOLDER, "records.pdf")
        guidelines_path = os.path.join(UPLOAD_FOLDER, "guidelines.pdf")
        
        # Check if files were uploaded
        if not records_file or not guidelines_file:
            return render_template("index.html", output_html="<p>Please upload both files</p>")
        

        records_file.save(records_path)
        guidelines_file.save(guidelines_path)

        # Convert PDFs to text
        records_text = pdf_to_text(records_path)
        guidelines_text = pdf_to_text(guidelines_path)

        # Load prompt text from file
        with open("static/prompt.txt", "r") as file:
            prompt_text = file.read()

        prompt = f"{prompt_text}\n\nRecords:\n{records_text}\n\nGuidelines:\n{guidelines_text}"
        print("Generated prompt text")
        
        # Query OpenAI
        completion = client.chat.completions.create(
            extra_body={},
            model="gpt-4o",
            messages=[
                {
                "role": "user",
                "content": prompt
                }
            ]
            )
        print("Generated completion")
        
        raw_output = completion.choices[0].message.content
        print("Generated raw output")
        print(raw_output)

        # Extract Markdown content and convert it to HTML
        try:
            if len(raw_output.split("```")) > 1:
                md_content = raw_output.split("```")[1]
                if len(md_content.split("markdown")) > 1:
                    md_content = md_content.split("markdown")[1]
            else:
                md_content = raw_output.split("|")[1]
                md_content = "|" + md_content
            output_html = markdown.markdown(md_content, extensions=["tables"])  # Convert to HTML
            results = True
        except Exception as e:
            print("Error processing Markdown:", str(e))
            output_html = f"<p>Error processing response: {str(e)}</p>"

        print("Generated markdown content")
        print(output_html)

        # return to results section of index.html
        return render_template("index.html", output_html=output_html, results=results)
    
    return render_template("index.html", output_html=output_html, results=False)

if __name__ == "__main__":
    app.run(debug =True, host="0.0.0.0")
