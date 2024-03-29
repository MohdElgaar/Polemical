
from flask import render_template, redirect, flash, url_for, abort, jsonify, request
from app.main.forms import LoginForm, RegisterationForm, EditProfileForm, AddTopicForm, SearchForm
from app import db, Config
from flask_login import current_user, login_user, logout_user, user_unauthorized
from app.models import User, Comment, Post, Vote
from app.main.similarity import sentence_similarity
from flask_login import login_required
from sqlalchemy import desc
from datetime import datetime
from app.main import keywordsfile
import time 
from functools import wraps
from app.main import main_bp as bp




@bp.context_processor
def injector():
    return {
        'now' : datetime.utcnow(),
        'site_name': Config.SITE_NAME
    }

def getKwds(comment_list):
    t = keywordsfile.Keyword()
    text = ". ".join([c.body for c in comment_list])
   
    t.analyze(text)
    return t.get_keywords(10)

def getVotingRatio(mid):
    """Given an argument id, returns the ratio of pro votes""" 
    pro = Vote.query.filter_by(post_id=mid, is_pro=True).count()
    against = Vote.query.filter_by(post_id=mid, is_pro=False).count()
    total = pro + against
    print("the total voting is", total)
    return ( round(pro/total * 100.0, 2) if total else total)

def hasVoted(mid):
    """ Checks if the current user has voted for a particular argument"""
    return  Vote.query. \
            filter_by(user_id=current_user.id, post_id=mid) \
            .first() is not None


@bp.route('/index', methods=['GET', 'POST'])
@bp.route('/', methods=['GET', 'POST'])
@login_required
def fun():
    search=SearchForm(request.form)
    if request.method == 'POST':
        # search_query = request.form['search']
        return search_results(search)
    arguments = Post.query.all()
    return render_template("index.html", args=arguments, form=search)

@bp.route('/search')
def search_results(search):
    results = []
    search_string = search.data['search']
 
    if search_string == '':
        results=Post.query.all()
    else:
        posts=Post.query.all()
        for post in posts:
            if search_string in post.question:
                results.append(post)
    if not results:
        flash('No results found!')
        return redirect('/')
    else:
        return render_template('index.html', args=results, form=search)


def getKwds(comment_list):
    t = keywordsfile.TextRank4Keyword()
    text = ". ".join([c.body for c in comment_list])
    t.analyze(text)
    return t.get_keywords(10)


@bp.route('/a/<aid>', methods=['GET', 'POST'])
def viewarg(aid):
    #TODO@ahmed: improve the shitty quality of this piece of code
    arg = Post.query.filter_by(id=aid).first_or_404()
    pro_comments = Comment.query.filter_by(post_id=aid, is_pro=1).order_by(desc(Comment.timestamp))
    con_comments = Comment.query.filter_by(post_id=aid, is_pro=0).order_by(desc(Comment.timestamp))
    pro_kwds = getKwds(pro_comments)
    con_kwds = getKwds(con_comments)

    
    if hasVoted(aid):
        return render_template("view_argument.html", arg=arg, ratio=getVotingRatio(aid), pro_comments=pro_comments, con_comments=con_comments, pro_kwd=pro_kwds, con_kwd=con_kwds)
    return render_template("view_argument.html", arg=arg, pro_kwd=pro_kwds, con_kwd=con_kwds, pro_comments=pro_comments, con_comments=con_comments)

@bp.route('/addtopic', methods=['GET', 'POST'])
def addtopic():
    form = AddTopicForm()
    if form.validate_on_submit():

        post = Post(question=form.name.data, body=form.description.data,
         timestamp=datetime.utcnow(), user_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('main.fun'))
    for fieldName, errorMessages in form.errors.items():
        for err in errorMessages:
            flash(err)
            #TODO: handle errors at the front-end
            print("error!", errorMessages)
    return render_template("add_topic.html", form=form)

@bp.route('/vote/<flag>/<mid>', methods=['POST'])
def make_vote(flag, mid):
    """ makes a vote record in the database, flag indicates wheather up or down"""
    record = Vote.query.filter_by(user_id=current_user.id, post_id=mid).first()
    if record:
        return jsonify({"id":mid, "flag":flag,"msg":"already exists!", "ratio": getVotingRatio(mid)})
    vote = Vote(user_id=current_user.id, post_id=mid, is_pro=( int(flag) & 1) )
    db.session.add(vote)
    db.session.commit()

    return jsonify({"ratio": getVotingRatio(mid)  })

@bp.route('/comment/<mid>', methods=['POST'])
def make_comment(mid):
    """ creates a commnet record in the database,
     flag indicates wheather pro or con"""
    req_json = request.get_json()
    comment_body = req_json.get('body')
    flag =  req_json.get('flag')

    if (len(comment_body) < 25): 
        return jsonify({"success":False, 'msg':'Sorry, your argument is too short. Could you elaborate more ?'})
    elif (len(comment_body) > 480):
        return jsonify({"success":False, 'msg':'Sorry, your argument is too long. Could you be less verbose ?'})
    #TODO: @Mohammed check if there is a similar comment.
    comment = Comment(body=comment_body, 
    user_id=current_user.id,
    post_id=mid, is_pro=( int(flag) & 1) )
    db.session.add(comment)
    db.session.commit()
        
    return jsonify({"success":True, 'msg':'Thank you for your opinion!'})

@bp.route('/sim/<mid>/<pro>', methods=['POST'])
def similarity(mid, pro):
    arg = Post.query.filter_by(id=mid).first_or_404()
    if pro:
        comments = Comment.query.filter_by(post_id=mid, is_pro=1) \
                .order_by(desc(Comment.timestamp))
    else:
        comments = Comment.query.filter_by(post_id=mid, is_pro=0) \
                .order_by(desc(Comment.timestamp))
    req_json = request.get_json()
    sentence = req_json.get('sentence')

    max_sim = 0
    for reference in comments:
        sim = sentence_similarity(sentence,reference.body)
        if sim > max_sim:
            max_sim = sim

    return jsonify({"sim": max_sim})



def log_lastseen():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
    db.session.commit()


@bp.before_request
def before_request():
    log_lastseen()


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        print("User is authenticated!")
        return redirect(url_for('main.fun'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username= form.username.data.lower() ).first()
        if user is None or not user.check_password(form.password.data):
            flash("Wrond password or username")
            print("wrong password mate")
            return redirect(url_for('main.login'))
        login_user(user, remember=False)
        print("[Login] {} logged in {}".format(user.username, datetime.utcnow()) )
        return redirect(url_for('main.fun'))
        flash('login for {} with password {} is failed'.format(form.username.data, form.password.data) )
    return render_template("login.html", form=form)

@bp.route('/register', methods=['GET', 'POST'])
def reg():
    if current_user.is_authenticated:
        return redirect(url_for('main.fun'))
    form = RegisterationForm()
    if form.validate_on_submit():
        print("User registered")
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('main.login'))
    for fieldName, errorMessages in form.errors.items():
        for err in errorMessages:
            flash(err)
    return render_template('register.html', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.fun'))


@bp.route('/user/<username>')  # dynamic component
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = [
    ]
    return render_template('user.html', posts=posts, user=user,
     form=EditProfileForm(current_user))
    # return render_template('user.html')

@bp.route('/disputes/<username>')  # dynamic component
@login_required

def disputes(username):
    user = User.query.filter_by(username=username).first_or_404()
    arguments = Post.query.filter_by(user_id=user.id)
    return render_template('disputes.html', args=arguments)

@bp.route('/edit_profile', methods=['POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about = form.about.data
        db.session.commit()
        return "Updated successfully"
    else:
        return "There was an error!"
