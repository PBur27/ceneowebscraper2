from app import app
from flask import render_template, request, redirect, url_for
from app.utils import get_element, selectors
import requests
import json
import os
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/extraction', methods=['POST', 'GET'])
def extract():
    error_message = "error"
    if request.method == 'POST':
        product_code = request.form['product_id']
        if not product_code.isdigit():
            error_message = 'Invalid product code.'
            return render_template('extraction.html', error_message=error_message)
        all_opinions = []
        url = f"https://www.ceneo.pl/{product_code}#tab=reviews"
        while(url):
            print(url)
            response = requests.get(url)
            page = BeautifulSoup(response.text, 'html.parser')
            opinions = page.select("div.js_product-review")
            for opinion in opinions:
                single_opinion = {}
                for key, value in selectors.items():
                    single_opinion[key] = get_element(opinion,*value)
                all_opinions.append(single_opinion)
            try:
                url = "https://www.ceneo.pl"+get_element(page, "a.pagination__next", "href")
            except TypeError:
                url = None
        try:
            os.mkdir("./app/static/opinions")
        except FileExistsError:
            pass
        with open(f"./app/static/opinions/{product_code}.json", "w", encoding="UTF-8") as jf:
            json.dump(all_opinions, jf, indent=4,ensure_ascii=False)
        opinions = pd.read_json(json.dumps(all_opinions,ensure_ascii=False))
        opinions.score = opinions.score.map(lambda x: float(x.split("/")[0].replace(",",".")))
        stats = {
            "opinions_count": opinions.shape[0],
            "pros_count": int(opinions.pros.map(bool).sum()),
            "cons_count": int(opinions.cons.map(bool).sum()),
            "avg_score": opinions.score.mean().round(2)
        }
        score = opinions.score.value_counts().reindex(list(np.arange(0,5.5,0.5)), fill_value = 0)
        score.plot.bar(color="hotpink")
        plt.xticks(rotation=0)
        plt.title("Histogram ocen")
        plt.xlabel("Liczba gwiazdek")
        plt.ylabel("Liczba opinii")
        plt.ylim(0,max(score.values)+1.5)
        for index, value in enumerate(score):
            plt.text(index, value+0.5, str(value), ha="center")
        try:
            os.mkdir("./app/static/plots")
        except FileExistsError:
            pass
        plt.savefig(f"./app/static/plots/{product_code}_score.png")
        plt.close()
        recommendation = opinions["recommendation"].value_counts(dropna = False).reindex(["Nie polecam", "Polecam", np.nan])
        print(recommendation)
        recommendation.plot.pie(
            label="", 
            autopct="%1.1f%%",
            labels = ["Nie polecam", "Polecam", "Nie mam zdania"],
            colors = ["crimson", "forestgreen", "gray"]
        )
        plt.legend(bbox_to_anchor=(1.0,1.0))
        plt.savefig(f"./app/static/plots/{product_code}_recommendation.png")
        plt.close()
        stats['score'] = score.to_dict()
        stats['recommendation'] = recommendation.to_dict()
        try:
            os.mkdir("./app/static/stats")
        except FileExistsError:
            pass
        with open(f"./app/static/stats/{product_code}.json", "w", encoding="UTF-8") as jf:
            json.dump(stats, jf, indent=4,ensure_ascii=False)
        return redirect(url_for('product', product_code=f"{product_code}.json"))
    return render_template('extraction.html')
@app.route('/list')
def products():
    products = os.listdir(path='./app/static/opinions')
    stats = []
    for filename in products:
        file_path = ''
        file_path = os.path.join('./app/static/stats',filename)
        link = f"https://www.ceneo.pl/{filename[0:-5]}"
        response = requests.get(link)
        page = BeautifulSoup(response.text, 'html.parser')
        name = page.select_one("div.product-top__title").get_text(strip=True)
        result_dict = {"id": filename, "name": name}
        
        with open(file_path, "r", encoding="utf8") as file:
            json_data = json.load(file)
        
        for key in ["opinions_count","pros_count","cons_count","avg_score"]:
            if key in json_data:
                result_dict[key] = json_data[key]

        stats.append(result_dict)
    return render_template('list.html', stats=stats)
@app.route('/product/<product_code>')
def product(product_code):
    file_path = ''
    file_path = os.path.join("./app/static/opinions/", product_code)
    with open(file_path, "r", encoding="utf8") as file:
        json_data = json.load(file)
    # pobranie zplików JSON opinii o prosukcie i statystyk o nim
    # przekazanie opinii i statystyk do szablonu HTML
    return render_template("product.html", product_code=product_code, data=json_data)

@app.route("/product/<product_code>/graphs")
def graphs(product_code):
    image_path = f"static/plots/{product_code[0:-5]}"
    return render_template('graphs.html', source = image_path)
@app.route('/author')
def author():
    return render_template('author.html')