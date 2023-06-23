from flask import Flask, render_template, request, redirect, flash, session
import requests
from bs4 import BeautifulSoup
from flask_sqlalchemy import SQLAlchemy
from flask_paginate import Pagination, get_page_parameter

app = Flask(__name__)
app.secret_key = 'jelly'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///animals.sqlite'
db = SQLAlchemy(app)


class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    common_name = db.Column(db.String(100))
    scientific_name = db.Column(db.String(100))
    category = db.Column(db.String(100))
    diet = db.Column(db.String(100))
    avg_life = db.Column(db.String(100))
    size = db.Column(db.String(100))
    weight = db.Column(db.String(100))
    facts = db.Column(db.String(100))
    url = db.Column(db.String(100))


with app.app_context():
    db.create_all()


def __str__():
    return f'THIS IS {db.Model.common_name} DID YOU KNOW THAT:{db.Model.fact}'


def get_animal_facts(animal_type):
    with app.app_context():
        info = Animal.query.filter(Animal.category.ilike(f'%{animal_type}%')).all()
        animal_data = get_animal_info(info)
        print(animal_data)
    return animal_data


def get_animal_info(info):
    animal_data = []
    for animal_obj in info:
        animal_dict = {
            'common_name': animal_obj.common_name,
            'scientific_name': animal_obj.scientific_name,
            'weight': animal_obj.weight,
            'size': animal_obj.size,
            'avg_life': animal_obj.avg_life,
            'facts': animal_obj.facts,
            'category': animal_obj.category,
            'diet': animal_obj.diet,
            'url': animal_obj.url
        }
        animal_data.append(animal_dict)
    return animal_data


def parsing_db():
    payloads = {1: 'mammals', 2: 'invertebrates', 3: 'reptiles'}
    animals = {'mammals': [], 'invertebrates': [], 'reptiles': []}

    n = 1
    while n < 4:
        url_animals = f'https://kids.nationalgeographic.com/animals/{payloads[n]}'
        res = requests.get(url_animals)
        print(res)
        content = res.text
        soup = BeautifulSoup(content, 'html.parser')
        all_animals = soup.find_all('div', class_='GridPromoTile__Tile')
        for animal in all_animals:
            name = animal.select_one('.PromoTile__Title--truncated').text.strip()

            if n == 1:
                animals['mammals'].append(name.lower().replace(' ', '-'))
            elif n == 2:
                animals['invertebrates'].append(name.lower().replace(' ', '-'))
            else:
                animals['reptiles'].append(name.lower().replace(' ', '-'))
        n += 1
    print(animals)

    with app.app_context():
        for category, animal_list in animals.items():
            for animal_name in animal_list:
                url_facts = f'https://kids.nationalgeographic.com/animals/{category}/facts/{animal_name}'
                res = requests.get(url_facts)
                content = res.text
                soup = BeautifulSoup(content, 'html.parser')
                fast_facts = soup.find_all('div', 'FastFacts__TopFacts__Data')
                a = Animal()
                info_dict = {}
                for fact in fast_facts:
                    fact_paragraph = soup.find('p').text.strip()
                    title = fact.find('dt', class_='FastFacts__TopFacts__Data__Title').text.strip()
                    description = fact.find('dd', class_='FastFacts__TopFacts__Data__Description').text.strip()
                    info_dict[title.lower()] = description
                a.common_name = info_dict.get('common name:', None)
                a.scientific_name = info_dict.get('scientific name:', None)
                a.category = info_dict.get('type:', None)
                a.diet = info_dict.get('diet:', None)
                a.avg_life = info_dict.get('average life span in the wild:', None)
                a.size = info_dict.get('size:', None)
                a.weight = info_dict.get('weight:', None)
                a.facts = fact_paragraph
                print(a.common_name)
                print(a.category)

                with app.app_context():
                    db.session.add(a)
                    db.session.commit()


# parsing_db()

@app.route('/')
def home():
    return render_template('base.html')


@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    quiz_data = [
        {
            "question": "How many hearts does an octopus have?",
            "options": ["1 heart", "2 hearts", "3 hearts", "None"],
            "answer": 2
        },
        {
            "question": "Which animal can hold its breath the longest underwater?",
            "options": ["Dolphin", "Whale", "Crocodile", "Sea turtle"],
            "answer": 1
        },
        {
            "question": "Which mammal has the longest lifespan?",
            "options": ["Elephant", "Gorilla", "Blue Whale", "Human"],
            "answer": 0
        },
        {
            "question": "Which animal is known for its ability to regrow its tail?",
            "options": ["Turtle", "Frog", "Snake", "lizard"],
            "answer": 3
        },
        {
            "question": "What is the smallest breed of dog?",
            "options": ["Chihuahua", "Dachshund", "Shih Tzu", "Pomeranian"],
            "answer": 0
        },
        {
            "question": "Which animal is not a reptile?",
            "options": [" Snake", "Turtle", "Crocodile", " Frog "],
            "answer": 3
        },
        {
            "question": "What is the average lifespan of a bear in the wild?",
            "options": [" 10-15 years", " 20-30 years ", " 40-50 years", " 60-70 years"],
            "answer": 1
        },
        {
            "question": "True or False: Wolves are known for their exceptional swimming ability",
            "options": ["True", "False"],
            "answer": 0
        }
    ]

    if 'current_question' not in session:
        session['current_question'] = 0
    if 'score' not in session:
        session['score'] = 0

    if request.method == 'POST':
        selected_option = request.form.get('option')

        if not selected_option:
            flash('Please select an answer', 'error')
        elif selected_option:
            if int(selected_option) == quiz_data[session['current_question']]['answer']:
                session['score'] += 1
            session['current_question'] += 1

        if session['current_question'] < len(quiz_data):
            question = quiz_data[session['current_question']]['question']
            options = quiz_data[session['current_question']]['options']
            return render_template('quiz.html', question=question, options=options)
        else:
            result_message = f"You scored {session['score']} out of {len(quiz_data)} questions."
            session.pop('current_question')
            session.pop('score')
            return render_template('quiz.html', result_message=result_message)

    question = quiz_data[session['current_question']]['question']
    options = quiz_data[session['current_question']]['options']
    return render_template('quiz.html', question=question, options=options)


@app.route('/mammals')
def mammals():
    animal_type = 'mammal'
    animal_data = get_animal_facts(animal_type)
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 8
    total_animals = len(animal_data)
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    animals_on_page = animal_data[start_index:end_index]
    pagination = Pagination(page=page, total=total_animals, per_page=per_page, css_framework='bootstrap4')
    return render_template('mammals.html', animals_on_page=animals_on_page, pagination=pagination)


@app.route('/redirecting')
def redirecting():
    pressed_animal = request.args['pressed'].lower().replace(' ', '-')
    payloads = {1: 'mammals', 2: 'invertebrates', 3: 'reptiles'}
    for index, payload in payloads.items():
        with app.app_context():
            info = Animal.query.filter(Animal.category.ilike(f'%{payload}%')).all()
            for animal_obj in info:
                common_name = animal_obj.common_name.lower().replace(' ', '-')
                if common_name == pressed_animal:
                    url = f'https://kids.nationalgeographic.com/animals/{payload}/facts/{common_name}'
                    return redirect(url)


@app.route('/reptiles')
def reptiles():
    animal_type = 'reptiles'
    animal_data = get_animal_facts(animal_type)
    return render_template('reptiles.html', animal_data=animal_data)


@app.route('/invertebrates')
def invertebrates():
    animal_type = 'invertebrates'
    animal_data = get_animal_facts(animal_type)
    return render_template('invertebrates.html', animal_data=animal_data)


@app.route('/search')
def search():
    animal = request.args.get('searched')

    with app.app_context():
        info = Animal.query.filter(Animal.common_name.ilike(f'%{animal}%')).all()
        animal_data = get_animal_info(info)
        if not animal_data:
            flash('We do not have information about this animal.', 'error')
            return render_template('home.html')

    return render_template('search.html', animal_data=animal_data)


# search()

if __name__ == '__main__':
    app.run()
