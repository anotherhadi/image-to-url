from flask import Flask, request, send_from_directory, render_template, redirect, url_for, make_response, flash
import os, string, json, random, hashlib
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder='templateFiles', static_folder='staticFiles')

info_path = r"./settingFiles/info.json"
settings_path = r"./settingFiles/settings.json"

# Load Settings
with open(settings_path, "r+") as f:
    settings = json.load(f)

# Load informations about uploaded images
with open(info_path, "r+") as f:
    info = json.load(f)

# Check if the "src" folder exist (Used to store images)
if not os.path.isdir("./src"):
    os.mkdir("./src")

# Return a random string of length length (Used to generate image name)
def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

# Check if the file is in the allowed extensions list
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in settings["ALLOWED_EXTENSIONS"]

@app.route('/', methods=['GET'])
def index(): return redirect(url_for("new"))

@app.route('/<string:path>', methods=['GET'])
def image(path):
    path = secure_filename(path)
    if not os.path.isfile(app.config['UPLOAD_FOLDER']+ path):
        folder = "staticFiles/"
        path = "404.png"
        return send_from_directory(folder, path)

    return send_from_directory(app.config['UPLOAD_FOLDER'], path)

@app.route('/explore', methods=['GET'])
def explore_home(): return redirect(url_for("explore", level=0))

@app.route('/explore/<int:level>', methods=['GET'])
def explore(level=0):
    if settings["EXPLORE"] == True:
        images = list(info.items())[level*9:level*9+9]
        context={
            "images":images,
            "level":level,
            "url":settings["URL"],
        }
        return render_template('explore.html', **context)
    else:
        flash("Explore desactivated")
        return redirect(url_for("new"))

@app.route('/new', methods=['GET', 'POST'])
def new():
    hash_nsec = request.cookies.get("nsec")
    if not hash_nsec in settings["NSEC"]:
        if settings["ALLOW_EVERYONE"] == False:
            flash(hash_nsec + " : Not authorized to post")
            return redirect(url_for("login"))

    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)

        file = request.files["file"]

        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)

        if file and allowed_file(file.filename):

            name = request.form.get("name")
            path = get_random_string(settings["IMAGE_NAME_SIZE"]) + "." + file.filename.rsplit('.', 1)[1].lower()
            while path in list(info.values()):
                path = get_random_string(settings["IMAGE_NAME_SIZE"]) + "." + file.filename.rsplit('.', 1)[1].lower()
           
            if name is None or name == "":
                name=path

            if name in list(info.keys()):
                flash("Name already taken")
                return redirect(request.url)

            file.save(os.path.join(app.config['UPLOAD_FOLDER'], path))

            size = os.stat(os.path.join(app.config['UPLOAD_FOLDER'], path)).st_size

            if size > settings["IMAGE_MAX_SIZE"]:
                flash("Image size too big.")
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], path))
                return redirect(request.url)


            info[name] = path
            with open(info_path, "w") as f:
                json.dump(info, f)

            flash("Success !")
            return render_template('file.html', **{"name":name, "path":path, "link":settings["URL"]+path})

    else:
        return render_template('new.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        nsec = request.form["nsec"]
        nsec_hash = hashlib.md5(str(nsec).encode("utf-8"))
        resp = make_response(redirect(url_for("new")))
        resp.set_cookie('nsec', nsec_hash.hexdigest())
        flash("Hash of nsec successfully written to 'nsec' cookie")
        return resp
    else:
        return render_template('login.html')

if __name__ == '__main__':

    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    SECRET_KEY = os.urandom(12).hex()
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['UPLOAD_FOLDER'] = "src/"
    app.run(port=settings["PORT"])