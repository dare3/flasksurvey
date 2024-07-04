from flask import Flask, session, request, render_template, redirect, make_response, flash
from flask_debugtoolbar import DebugToolbarExtension
from surveys import surveys

# key names will use to store some things in the session;
# put here as constants so we're guaranteed to be consistent in
# our spelling of these

SURVEY_KEY = 'current_survey'
RESPONSES_KEY = 'responses'

app = Flask(__name__)
app.config['SECRET_KEY'] = "hidden"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

debug = DebugToolbarExtension(app)


@app.route("/")
def select_survey_form():
    """Show a selected survey form."""
    return render_template("select-survey.html", surveys=surveys)


@app.route("/", methods=["POST"])
def choose_survey():
    """Select a survey."""
    survey_id = request.form['survey_code']

    # check if survey is already completed
    if request.cookies.get(f"completed_{survey_id}"):
        return render_template("done-survey.html")

    survey = surveys[survey_id]
    session[SURVEY_KEY] = survey_id
    return render_template("survey.html",survey=survey)


@app.route("/begin", methods=["POST"])
def begin_survey():
    """Clear the session of responses."""
    session[RESPONSES_KEY] = []
    return redirect("/questions/0")


@app.route("/answer", methods=["POST"])
def handle_question():
    """Save response and redirect to next question."""
    choice = request.form['answer']
    text = request.form.get("text", "")

    # add this response to the list in the session
    responses = session.get(RESPONSES_KEY, [])
    responses.append({"choice": choice, "text": text})
    

    # update the session wit h the new responses
    session[RESPONSES_KEY] = responses
    survey_code = session[SURVEY_KEY]
    survey = surveys[survey_code]

    if len(responses) == len(survey.questions):
        # All questions answered! Thank them.
        return redirect("/complete")
    else:
        return redirect(f"/questions/{len(responses)}")


@app.route("/questions/<int:ques>")
def display_question(ques):
    """show current question."""
    responses = session.get(RESPONSES_KEY)
    if (responses is None):
        return redirect("/")
    
    survey_code = session[SURVEY_KEY]
    survey = surveys[survey_code]

    if len(responses) == len(survey.questions):
        return redirect("/done-survey")

    # if (len(responses) == len(survey.questions)):
    #     # if they've answered all the questions! Thank them.
    #     return redirect("/done-survey")

    if (len(responses) != ques):
        #  access questions out of order.
        flash(f"Invalid question id: {ques}.")
        return redirect(f"/questions/{len(responses)}")

    question = survey.questions[ques]
    
    return render_template( "question.html", question_num=ques, question=question)


@app.route("/complete")
def say_thanks():
    """Thank user and list responses."""
    survey_id = session[SURVEY_KEY]
    survey = surveys[survey_id]
    responses = session[RESPONSES_KEY]

    html = render_template("completion.html",survey=survey, responses=responses)

    # Set cookie noting this survey is done so they can't re-do it
    response = make_response(html)
    response.set_cookie(f"completed_{survey_id}", "yes", max_age=60)
    return response

   
