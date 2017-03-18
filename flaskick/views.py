from flask import render_template


from app import app
import models

@app.route('/')
def index():
    start_idx = 0
    page_size = 10
    matchdays = models.MatchDay.query.order_by(
        models.MatchDay.date.desc())[start_idx:start_idx + page_size]
    return render_template('index.html',
                           # matchdays=filter(lambda md: len(md.matches) > 0, matchdays)
                           matchdays=matchdays
    )
