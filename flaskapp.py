import pymongo
from flask import Flask, request, url_for, redirect, render_template, abort, send_from_directory
from flask_paginate import Pagination, get_page_parameter


app = Flask(__name__)


@app.route('/', methods=["GET", "POST"])
def showAll():
    sort = [('modified',-1)]
    filter = base_filter.copy()
    if tag_filter != []:
        filter['tags'] = {'$all':tag_filter.copy()}

    current_page = request.args.get(get_page_parameter(), type=int, default=1)
    pagination =Pagination(page=current_page, total=db.skelbimai.count_documents(filter), per_page= per_page, css_framework='bootstrap', bs_version='4')


    mongoData = db.skelbimai.find(filter).sort(sort).skip((current_page-1)*per_page).limit(per_page)
    return render_template('home.html', data = mongoData, pagination =pagination, tags=tag_filter, data_filter = filter)



@app.route('/<path:resource>', methods=["GET"])
def serveStaticResource(resource):
    return send_from_directory('static/', resource)

@app.route('/add_tag', methods=["POST"])
def add_tag():
    if request.method == 'POST':
        if request.form['add_filter_tag']:
            tag_filter.append(request.form['add_filter_tag'])
    return redirect(url_for('showAll'))

@app.route('/remove_tag', methods=["POST"])
def remove_tag():
    if request.method == 'POST':
        if request.form['remove_filter_tag']:
            tag_filter.remove(request.form['remove_filter_tag'])
    return redirect(url_for('showAll'))


# test
@app.route("/test/", methods=["GET"])
def test():
    return render_template('text_test.html')


# Mongo Connect
db = pymongo.MongoClient(host="mongodb://localhost:27017").skelbimai

per_page = 25
base_filter = {'status': 'complete'}
tag_filter = []
if __name__ == '__main__':
    app.run()