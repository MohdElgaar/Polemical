from app import app_factory, db
from app.models import User, Post, Comment

app = app_factory()

# used for debugging 
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 
    'Post': Post,  'Comment': Comment}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')