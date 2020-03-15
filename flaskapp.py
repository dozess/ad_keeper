import pymongo
from flask import Flask, request, url_for, redirect, render_template, abort, send_from_directory, session, safe_join
from flask_paginate import Pagination, get_page_parameter
import flask_resize


app = Flask(__name__)
app.config['SECRET_KEY']='0612dec6be4c1d5412cf8c7d5df7fc60'
app.config['RESIZE_URL'] = '/'
app.config['RESIZE_ROOT'] = 'F:\\image_archyve\\'
app.config['RESIZE_TARGET_DIRECTORY'] = 'resized-images'

resize = flask_resize.Resize(app)


@app.route('/', methods=["GET", "POST"])
def showAll():
    sort = [('modified',-1)]
    filter = base_filter.copy()
    if not 'tag_filter' in session:
        session['tag_filter'] = []
    if session['tag_filter'] != []:
        filter['tags'] = {'$all':session['tag_filter'].copy()}

    current_page = request.args.get(get_page_parameter(), type=int, default=1)
    pagination =Pagination(page=current_page, total=db.skelbimai.count_documents(filter), per_page= per_page, css_framework='bootstrap', bs_version='4')

    mongo_data = list(db.skelbimai.find(filter).sort(sort).skip((current_page-1)*per_page).limit(per_page))

    for rec in mongo_data:
        if 'photos' in rec:
            for index, img in enumerate(rec['photos']):
                if index > 4 : pass
                img['local_file']=img['local_file'].replace('\\','/')
                img['th_url']=resize(app.config['RESIZE_ROOT']+img['local_file'], '135x135',  format='jpg')
        if 'screenshot' in rec:
            rec['th_scr_url']=resize(app.config['RESIZE_ROOT']+rec['screenshot'], '135x135',  format='jpg')
    return render_template('home.html', data = mongo_data, pagination =pagination, tags=session['tag_filter'], data_filter = filter)




@app.route('/add_tag', methods=["POST"])
def add_tag():
    if request.method == 'POST':
        if request.form['add_filter_tag']:
            app.logger.debug('Receved tag : ' + request.form['add_filter_tag'])
            if not 'tag_filter' in session:
                session['tag_filter'] = []
            temp_tag = session.get('tag_filter')
            temp_tag.append(request.form['add_filter_tag'])
            session['tag_filter'] = temp_tag.copy()
    return redirect(url_for('showAll'))



@app.route('/remove_tag', methods=["POST"])
def remove_tag():
    if request.method == 'POST':
        if request.form['remove_filter_tag']:
            temp_tag = session.get('tag_filter')
            temp_tag.remove(request.form['remove_filter_tag'])
            session['tag_filter'] = temp_tag.copy()
    return redirect(url_for('showAll'))

@app.route('/resized-images/<path:filename>', methods=["GET"])
def serve_media_file(filename):
    return send_from_directory( 'F:\\image_archyve\\resized-images\\' , filename)


# test
@app.route("/test/", methods=["GET"])
def test():
    return render_template('text_test.html')



# Mongo Connect
db = pymongo.MongoClient(host="mongodb://localhost:27017").skelbimai

per_page = 25
base_filter = {'status': 'complete'}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')