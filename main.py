import os
from flask import Flask, render_template, request, make_response, redirect
from twilio.rest import Client
from dotenv import load_dotenv
import openai
import random
from deta import Deta

load_dotenv("private.env")

# Load environment variables
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
openai.api_key = os.getenv("OPENAI_API_KEY")
deta = Deta(os.getenv("DETA_PROJECT_KEY"))
# Create a new base
db = deta.Base("TheatrePrompts")


# Send bulk SMS to a list of phone numbers
def send_messages(numbers, content):
    for number in numbers:
        print(content)
        print(number)
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=content,
            messaging_service_sid='MGa7c75be6043b71ab2cad34bbcc1fd2e2',
            to=number
        )


# Split the text into a list of prompts
def split_text(text):
    return list(filter(None, text.splitlines()))


# Ngl, I don't know what this does but it works and burns money.
def generate_prompts():
    response = openai.Completion.create(
        model="text-davinci-002",
        prompt="Come up with 8 improv prompts for theatre.",
        temperature=0.7,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    return split_text(response.choices[0].text)


app = Flask(__name__)


@app.route('/api/send', methods=['GET'])
def send():
    # Get the prompt from the url
    prompt = request.args.get('prompts')
    id = request.cookies.get('ID')
    send_messages(db.get(id)['phone_numbers'], prompt)
    return redirect('/confirmed')


@app.route('/confirmed', methods=['GET'])
def confirmed():
    return render_template('confirmed.html')


@app.route('/', methods=['GET', 'POST'])
def prompts():
    id = request.cookies.get('ID')
    if id is None:
        prompts1 = generate_prompts()
        id = str(random.randint(0, 1000000))
        resp = make_response(render_template('prompts.html', id=id, prompts=prompts1))
        resp.set_cookie('ID', id)
        db.put({"id": id, "prompts": prompts1, "phone_numbers": []}, id)
        return resp

    else:
        prompts1 = db.get(id)['prompts']
        phone_numbers = db.get(id)['phone_numbers']
        resp = make_response(render_template('prompts.html', id=id, prompts=prompts1, phone_numbers=phone_numbers))
        return resp


@app.route('/api/add', methods=['GET', 'POST'])
def add():
    id = request.cookies.get('ID')
    number = request.form.get('number')
    phone_numbers = db.get(id)['phone_numbers']
    phone_numbers.append(number)
    db.put({"id": id, "prompts": db.get(id)['prompts'], "phone_numbers": phone_numbers}, id)
    return redirect('/')


if __name__ == '__main__':
    app.run()
