from forecasts import forecast_questions

from flask_login import current_user
from hemlock import Branch, Page, Embedded, Blank, Check, Dashboard, Input, Textarea, Label, Debug as D, Validate as V, Navigate as N, route
from hemlock.tools import Assigner, Randomizer, consent_page, completion_page, html_list
from hemlock_berlin import berlin
from hemlock_crt import crt

from random import shuffle

# TODO update percentiles and number of forecasts
PERCENTILES = (10, 50, 90)
N_FCASTS = 1

assigner = Assigner({
    'Bootstrap': (0, 1),
    'Context': ('both', 'neither', 'second-only')
})
fcast_selector = Randomizer(forecast_questions, r=N_FCASTS)

@route('/survey')
def start():
    assigner.next()
    fcast_questions = make_fcast_questions()
    return Branch(
        consent_page(
            # TODO write consent form
            '''
            By continuing with this study, you consent to sell your first-born child to the Tetlock lab for a price no greater than $98.66.
            '''
        ),
        *crt('bat_ball', 'flowers', 'students', 'green_round', 'stock', 'whales', page=True),
        berlin(),
        Page(
            Label(
                # TODO write introductory instructions explaining the task, bonuses, etc.
                '''
                We will now ask you to make some estimates.
                '''
            )
        ),
        *[
            make_first_estimate_page(content, fcast_inputs)
            for content, fcast_inputs in fcast_questions
        ],
        navigate=N.second_estimates(fcast_questions)
    )

@N.register
def second_estimates(first_estimate_branch, fcast_questions):
    return Branch(
        make_second_estimates_intro_page(),
        *[
            make_second_estimate_page(content, fcast_inputs)
            for content, fcast_inputs in fcast_questions
        ],
        completion_page()
    )

def make_second_estimates_intro_page():
    page = Page(
        Label(
            # TODO write instructions explaining that now you're going to make your estimates a second time
            '''
            We will now ask you to make new estimates for all of the questions you just answered. Your second estimate should be different from your first.
            '''
        )
    )
    if current_user.meta['Context'] == 'second-only':
        page.questions.append(Label(
            # TODO it might be confusing for people who made their estimatese without context the first time to now make their estimates with context. 'I never estimated anything about COVID-19 deaths, what do you mean my first estimate?' Maybe add something explaining this to them. 
            '''
            When making your second estimates, we will reveal the context. That is, you will know what you are estimating.
            '''
        ))
    return page

def use_context(first_estimate):
    # indicates whether to include context
    return (
        (first_estimate and current_user.meta['Context'] == 'both')
        or (not first_estimate and current_user.meta['Context'] != 'neither')
    )

def make_fcast_questions():
    # make all questions (confidence intervals) for all time series
    fcast_content = fcast_selector.next()
    fcast_content = (
        list(fcast_content) if isinstance(fcast_content, tuple)
        else [fcast_content]
    )
    shuffle(fcast_content)
    current_user.embedded.append(
        Embedded('Forecast', [q['name'] for q in fcast_content])
    )
    return [
        [content, make_questions(content, first_estimate=True)] 
        for content in fcast_content
    ]

def make_questions(content, first_estimate):
    # make questions (confidence intervals) for a given time series
    def make_question(ci, content):
        return Blank(
            (content['question'][0].format(ci), content['question'][1]),
            var=var+str(ci), append=content['append'], step='any',
            blank_empty='_____', type='number', required=True
        )

    content_ = (
        content['context'] if use_context(first_estimate=first_estimate)
        else content['no_context']
    )
    var = 'FirstEstimate' if first_estimate else 'SecondEstimate'
    return [make_question(pctile, content_) for pctile in PERCENTILES]

def make_first_estimate_page(content, fcast_inputs):
    content = content.copy()
    content['use_context'] = use_context(first_estimate=True)
    return Page(
        Dashboard(src='/dashapp/', g=content),
        # estimation questions
        *fcast_inputs,
        timer='FirstEstimateTime'
    )

def make_second_estimate_page(content, fcast_inputs):
    content = content.copy()
    if use_context(first_estimate=False):
        content['use_context'] = True
        content_ = content['context']
    else:
        content['use_context'] = False
        content_ = content['no_context']
    return Page(
        Dashboard(src='/dashapp/', g=content),
        # remind user of first estimates
        Label(
            '''
            <p>Your first estimates were:</p>
            ''' + html_list(
                *[
                    (
                        'There is a {} in 100 chance '+content_['remind']
                    ).format(pctile, fcast_input.response)
                    for pctile, fcast_input in zip(PERCENTILES, fcast_inputs)
                ], 
                ordered=False
            )
        ),
        # additional questions (i.e., for dialectical bootstrapping)
        *make_additional_questions(),
        # estimation questions
        *make_questions(content, first_estimate=False),
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