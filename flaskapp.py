import pymongo
from bson.objectid import ObjectId
from flask import Flask, request, url_for, redirect, render_template, abort, send_from_directory, session, safe_join
from flask_paginate import Pagination, get_page_parameter
#import flask_resize
import json
from os import path
import secrets
from PIL import Image, ImageDraw
from PIL.ImageOps import invert
from hashlib import sha224

app = Flask(__name__)

if path.isfile('/etc/ad_keeper_cfg.json'):
    with open('/etc/ad_keeper_cfg.json') as config_file:
        config = json.load(config_file)
elif path.isfile('ad_keeper_cfg.json'):
    with open('ad_keeper_cfg.json') as config_file:
        config = json.load(config_file)
else:
    print('Cannot locate configuration file.')
    import sys
    sys.exit()

app.config['SECRET_KEY'] = config.get('SECRET_KEY')
app.config['RESIZE_URL'] = config.get('RESIZE_URL')
app.config['RESIZE_ROOT'] = config.get('RESIZE_ROOT')
app.config['RESIZE_TARGET_DIRECTORY'] = config.get('RESIZE_TARGET_DIRECTORY')
app.config['DB_CONNECT'] = config.get('DB_CONNECT')
app.config['APP_BIND_IP'] = config.get('APP_BIND_IP')
app.config['APP_DEBUG'] = config.get('APP_DEBUG')

#resize = flask_resize.Resize(app)

# image rounded corners
def add_corners(img, rad):
    """
    function to make transperent rounded corners
    :param img: image stored in PIL Image object
    :param rad: radius in pixrls to cut from corners
    :return: PIL Image object
    """
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
    alpha = Image.new('L', img.size, 255)
    w, h = img.size
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
    img.putalpha(alpha)
    return img


def resize_image(img, dim,bg_color,rad, mask_img):

    ratio = min ( [float(dim[i])/float(img.size[i]) for i in range(2)])
    if ratio < 1 :
        method = Image.BILINEAR
    elif ratio > 1 :
        method = Image.LANCZOS
    else:
        return img

    new_dim = [int(img.size[i]*ratio) for i in range(2)]
    img = img.resize(new_dim, method)

    return img






def url_for_resized_image(file_name, dim, bg_color=None, rad=None, mask_fn=None):
    """
    Creates resized image in subfolder with hashed filename. if image file resized to the same dimentions exists
    function returns cashed image.

    :param file_name: str: file name (with path from app.config['RESIZE_ROOT'] ) of image file. Can be absolute path on
    local machine, outside of flask root
    :param dim: str: desired dimentions of new image in form of 'HEIGHTxWIDTH' i.e. '300x200'
    :param bg_color: tuple: RGB or RGBA values of background color which fills remaining area if image resized by
    aspect ratio wont fill all area
    :param rad: int :radius in pixels to to make rounded corners
    :param mask_fn: filename of mask image mask wil be sized to 1/3 of image and placed in center. White color will
    become transperent, black color wil be intransperent
    :return: URL for recised image cashed in folder's  app.config['RESIZE_TARGET_DIRECTORY']  subfolder
    app.config['RESIZE_TARGET_DIRECTORY']
    """
    full_path = (app.config['RESIZE_ROOT']+ file_name).replace('\\','/')
    img_dim = [int(s) for s in dim.split('x')]


    img_path, fn = path.split(file_name)

    ext = path.splitext(fn)[-1]
    string_to_encode = (file_name + dim + str(bg_color) + str(rad) + str(mask_fn) ).encode('utf-8')
    #response += 'File name to encode: {}\n'.format(string_to_encode)
    new_fn = sha224(string_to_encode).hexdigest() + ext
    #response += 'New filename: {}\n'.format(new_fn)

    new_full_path = path.join(path.join(app.config['RESIZE_ROOT'], app.config['RESIZE_TARGET_DIRECTORY'] ),new_fn).replace('\\','/').encode('utf-8').decode()
    ##response += 'New local full path : {}\n'.format(new_full_path)

    if path.isfile(new_full_path):
        pass
    else:

        src = Image.open(full_path)


        if mask_fn:
            mask_img = Image.open(path.join(app.config['RESIZE_ROOT'], mask_fn ))
            #response += 'Opened mask image {} sucessfully\n'.format(path.join(app.config['RESIZE_ROOT'], mask_fn ))
        else:
            mask_img = None
            #response += 'Mask image is not required\n'



        src = resize_image(src, img_dim, bg_color, rad, mask_img)
        src.save(new_full_path)


    ##response += 'Image opened sucessfully\n'
    ##response += 'Image dimentions will be {} x {}\n'.format(img_dim[0], img_dim[1])
    ##response += 'Image saved sucsesfuly.\n'
    img_url =  safe_join(safe_join(app.config['RESIZE_URL'], app.config['RESIZE_TARGET_DIRECTORY']), new_fn)
    ##response += 'Image available at: {}\n'.format(img_url)

    return img_url#, #response

# test
@app.route("/test/", methods=["GET"])
def test():
    mongo_data = db.skelbimai.find_one({'site_id':'46830447'})

    url = url_for_resized_image(mongo_data['screenshot'], dim='100x200')
    return render_template('text_test.html', data = mongo_data, image = url)




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
                img['th_url'] = url_for_resized_image(img['local_file'], '135x135')
        if 'screenshot' in rec:
            img_path = None
            img_path = (rec['screenshot']).replace('\\','/')
            try:
                rec['th_scr_url']=url_for_resized_image(img_path, '135x135')
            except:
                img['th_url'] = 'https://picsum.photos/135'
    return render_template('home.html', data = mongo_data, pagination =pagination, tags=session['tag_filter'], data_filter = filter)

@app.route('/zoom/<id>', methods=["GET",])
def zoom_ad(id):
    record = db.skelbimai.find_one({'_id':ObjectId(id)})

    if 'photos' in record:
        for img in record['photos']:
            img['local_file']=img['local_file'].replace('\\','/')
            img['med_url']=url_for_resized_image(img['local_file'], '800x800')
    if 'screenshot' in record:
        record['med_scr_url']=url_for_resized_image(record['screenshot'], '800x800')
    return render_template('view.html', data = record)



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



# Mongo Connect
db = pymongo.MongoClient(host=app.config['DB_CONNECT']).skelbimai

per_page = 25
base_filter = {'status': 'complete'}

if __name__ == '__main__':
    app.run(debug=app.config['APP_DEBUG'], host=app.config['APP_BIND_IP'])