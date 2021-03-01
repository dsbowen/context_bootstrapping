from flask_login import current_user
from hemlock import (
    Branch, Page, Embedded, Blank, Check, Dashboard, Input, Textarea, 
    Label, Debug as D, Validate as V, Navigate as N, route
)
from hemlock.tools import (
    Assigner, Randomizer, consent_page, completion_page, html_list
)
from hemlock_berlin import berlin
from hemlock_crt import crt
try:
    from yaml import load, CLoader as Loader
except:
    from yaml import load, Loader

from random import shuffle

# percentiles of the distribution predicted by the participant
PERCENTILES = (10, 50, 90)
# number of time-series forecasts made by each participant
N_FCASTS = 2
# number of forecasted time steps ahead
TIME_STEPS = 5

# templates for the elicitation question with and without context, e.g.,
# pctile=50, 
# fewer_less=fewer, 
# y=thousand new daily COVID-19 cases in the U.S., 
# t=5
# x=days
# output: "There is a 50 in 100 chance that there will be fewer than _____ thousand new daily COVID-19 cases in the U.S. 5 days after the end of this graph."
CONTEXT = (
    '<p>There is a {pctile} in 100 chance that {quantity} will be {fewer_less} than ', ' {y} {t} {x} after the end of this graph.</p>'
)
# output: "There is a 50 in 100 chance that the line will be below _____ 5 time steps after the end of this graph."
NO_CONTEXT = (
    '<p>There is a {pctile} in 100 chance that the line will be below ', ' {t} time steps after the end of this graph.'
)

# 2 (dialectical bootstrapping or no dialectical bootstrapping)
# x 3 (context for both estimates, neither estimate, or second only)
assigner = Assigner({
    'Bootstrap': (0, 1),
    'Context': ('both', 'neither', 'second-only')
})
# load forecast questions
forecast_questions = load(open('forecasts.yaml', 'r'), Loader=Loader)
# randomly selects keys for the forecast questions
fcast_selector = Randomizer(list(forecast_questions.keys()), r=N_FCASTS)

@route('/survey')
def start():
    def make_first_estimate_questions():
        # returns a list of (forecast key, questions) tuples asking participants to enter forecasts
        fcast_keys = fcast_selector.next()
        fcast_keys = (
            list(fcast_keys) if isinstance(fcast_keys, tuple) 
            else [fcast_keys]
        )
        # shuffle the order of the questions
        shuffle(fcast_keys)
        # track the order of the questions as embedded data
        current_user.embedded.append(Embedded('Forecast', fcast_keys))
        return [
            [key, make_fcast_questions(key, context, first_estimate=True)] 
            for key in fcast_keys
        ]

    assigner.next()
    context = use_context(first_estimate=True)
    first_estimate_questions = make_first_estimate_questions()
    return Branch(
        consent_page(
            # TODO write consent form
            '''
            By continuing with this study, you consent to sell your first-born child to the Tetlock lab for a price no greater than $98.66.
            '''
        ),
        *crt(
            'bat_ball', 
            'flowers', 
            'students', 
            'green_round', 
            'stock', 
            'whales', 
            page=True
        ),
        berlin(),
        Page(
            Label(
                '''
                <p>We will now show you some graphs and ask you to make estimates about them.</p> 
                
                <p>All the graphs are about something changing over time. For example, we might show you a graph of how the temperature in New York changed between January and July 2020.</p>

                <p>Your task is to predict what will happen after the graph stops. For example, we might ask you to use the temperature graph to predict what the temperature in New York will be in December 2020.</p>

                <p>We may or may not tell you what you're estimating. For example, we may show you a graph of New York temperatures but remove the labels and simply call it an "Untitled Graph".

                We will pay you a larger bonus if your estimates are more accurate. Please do not look up the answers.
                '''
            )
        ),
        *[
            Page(
                Dashboard(
                    src='/dashapp/', 
                    g={'fcast_key': fcast_key, 'context': context}
                ),
                *questions,
                timer='FirstEstimateTime'
            ) 
            for fcast_key, questions in first_estimate_questions
        ],
        navigate=N.second_estimates(first_estimate_questions)
    )

def use_context(first_estimate):
    # indicates whether to include context
    return (
        (first_estimate and current_user.meta['Context'] == 'both')
        or (not first_estimate and current_user.meta['Context'] != 'neither')
    )

def make_fcast_questions(key, context, first_estimate):
    # key is a key from forecasts.yaml, e.g., COVID_cases
    # context is a boolean indicating to use context
    # returns a list of forecast questions
    labels = make_fcast_question_labels(key, context)
    content = forecast_questions[key].copy() # dictionary of question content
    append = get_content_item(content, 'append', 'y') if context else None
    # variable is 'FirstEstimate' or 'SecondEstimate'
    var = 'FirstEstimate' if first_estimate else 'SecondEstimate'
    return [
        Blank(
            label,
            append=append, blank_empty='_____', type='number', step='any',
            var=var+str(pctile), required=True
        )
        for label, pctile in zip(labels, PERCENTILES)
    ]

def make_fcast_question_labels(key, context):
    def make_question_label(pctile):
        if context:
            # forecast question label with context
            return (
                CONTEXT[0].format(
                    pctile=pctile, 
                    fewer_less=fewer_less,
                    quantity=quantity
                ),
                CONTEXT[1].format(y=y, t=TIME_STEPS, x=x)
            )
        else:
            # forecast question label without context
            return (
                NO_CONTEXT[0].format(pctile=pctile),
                NO_CONTEXT[1].format(t=TIME_STEPS)
            )

    content = forecast_questions[key].copy() # dictionary of question content
    # x variable text, e.g., 'days'
    x = get_content_item(content, 'x_text', 'x')
    # y variable text, e.g., 'thousand new COVID-19 cases in the U.S.'
    y = get_content_item(content, 'y_text', 'y')
    # fewer or less
    fewer_less = content['fewer_less']
    # name of the quantity, or 'there' e.g., 'there will be...'
    quantity = content.get('quantity', 'there')
    return [make_question_label(pctile) for pctile in PERCENTILES]

def get_content_item(content, key, substitute):
    item = content.get(key)
    if item is None:
        item = content[substitute]
        item = item[0].lower() + item[1:]
    return item

@N.register
def second_estimates(first_estimate_branch, first_estimate_questions):
    def make_second_estimates_intro_page():
        page = Page(
            Label(
                '''
                We will now ask you to make new estimates for all of the questions you just answered. Your second estimate should be different from your first.
                '''
            )
        )
        if current_user.meta['Context'] == 'second-only':
            page.questions.append(Label(
                # TODO it might be confusing for people who made their estimates without context the first time to now make their estimates with context. 'I never estimated anything about COVID-19 deaths, what do you mean my first estimate?' Maybe add something explaining this to them. 
                '''
                When making your second estimates, we'll tell you what you're estimating.
                '''
            ))
        return page

    def make_second_estimate_page(key, questions):
        # key is a key in the forecasts.yaml dictionary
        # questions is a list of first estimate questions for this key
        # returns a page asking for second estimates
        labels = make_fcast_question_labels(key, context)
        return Page(
            Dashboard(
                src='/dashapp/', 
                g={'fcast_key': key, 'context': context}
            ),
            # remind user of first estimates
            Label(
                '''
                <p>Your first estimates were:</p>
                ''' + html_list(
                    *[
                        label[0]+q.response+label[1] 
                        for label, q in zip(labels, questions)
                    ], 
                    ordered=False
                )
            ),
            # additional questions (i.e., for dialectical bootstrapping)
            *make_additional_questions(),
            # estimation questions
            *make_fcast_questions(key, context, first_estimate=False),
            timer='SecondEstimateTime'
        )

    def make_additional_questions():
        if not current_user.meta['Bootstrap']:
            return [Label(
                '''
                Please make second estimates which are different from your first estimates.
                '''
            )]
        # questions for dialectical bootstrapping
        return [
            Textarea(
                '''
                <p>Imagine your first estimates were off the mark. Write at least one reason why that could be. Which assumptions or considerations could have been wrong?</p>
                ''',
                var='Assumptions', required=True, validate=V.min_words(7),
                debug=[D.send_keys('here are 7 words without a meaning'), D.send_keys(p_exec=.2)]
            ),
            Check(
                '''
                <p>What does this reason imply? Were your first estimates too high or too low?</p>
                ''',
                [
                    ('Too high', 'high'), 
                    ('Too low', 'low'),
                    ('Some were too high, others too low', 'both')
                ],
                var='Direction', validate=V.require()
            ),
            Label(
                '''
                Based on this new perspective, make second estimates which are different from your first estimates.
                '''
            )
        ]

    context = use_context(first_estimate=False)
    return Branch(
        make_second_estimates_intro_page(),
        *[
            make_second_estimate_page(key, questions)
            for key, questions in first_estimate_questions
        ],
        completion_page()
    )